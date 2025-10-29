# core/download_manager.py - Download queue and task management
"""
Enhanced download manager with better queue handling and progress tracking
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from core.models import DownloadTask, DownloadRequest, TaskStatus, QueueStatus
from core.video_downloader import VideoDownloader
from core.config import settings

class DownloadManager:
    """Manages download queue and active downloads"""
    
    def __init__(self):
        self.download_queue: List[DownloadTask] = []
        self.active_downloads: List[DownloadTask] = []
        self.completed_tasks: List[DownloadTask] = []  # Keep recent completed tasks
        self.downloader = VideoDownloader()
        self.shutdown_timer = None
        self.start_time = datetime.now()
        self._processing = False
    
    async def start(self):
        """Start the download manager"""
        print("📥 Download Manager started")
        self._start_shutdown_timer()
    
    async def stop(self):
        """Stop the download manager and cleanup"""
        print("📥 Download Manager stopping...")
        
        # Cancel shutdown timer
        if self.shutdown_timer:
            self.shutdown_timer.cancel()
        
        # Cancel all active downloads
        for task in self.active_downloads.copy():
            await self.cancel_task(task.id)
        
        print("📥 Download Manager stopped")
    
    async def add_to_queue(self, request: DownloadRequest) -> str:
        """Add download task to queue"""
        task = DownloadTask(request)
        self.download_queue.append(task)
        
        print(f"➕ Added task {task.id} to queue")
        print(f"📊 Queue size: {len(self.download_queue)}")
        
        # Start processing if not already processing
        if not self._processing:
            asyncio.create_task(self._process_queue())
        
        # Reset shutdown timer
        self._start_shutdown_timer()
        
        return task.id
    
    async def _process_queue(self):
        """Process download queue with concurrency control"""
        if self._processing:
            return
        
        self._processing = True
        
        try:
            while self.download_queue or self.active_downloads:
                # Start new downloads if we have capacity
                while (len(self.active_downloads) < settings.MAX_CONCURRENT_DOWNLOADS 
                       and self.download_queue):
                    
                    task = self.download_queue.pop(0)
                    self.active_downloads.append(task)
                    
                    # Start download task
                    asyncio.create_task(self._download_task(task))
                
                # Wait a bit before checking again
                await asyncio.sleep(1)
            
        finally:
            self._processing = False
            
            # Start shutdown timer if no more work
            if not self.download_queue and not self.active_downloads:
                self._start_shutdown_timer()
    
    async def _download_task(self, task: DownloadTask):
        """Execute a single download task"""
        try:
            task.status = TaskStatus.DOWNLOADING
            task.start_time = datetime.now()
            
            print(f"⬇️  Starting download: {task.id}")
            
            # Get download directory
            download_dir = settings.get_download_directory(task.download_location)
            
            # Validate download directory
            if not settings.validate_download_directory(download_dir):
                raise Exception(f"Cannot write to download directory: {download_dir}")
            
            # Download the video (using cookies if available)
            result = await self.downloader.download_video(
                url=task.url,
                format_id=task.format_id,
                directory=download_dir,
                format_type=task.format_type,
                cookies=task.cookies,  # Pass cookies if available
                progress_callback=lambda progress: self._update_task_progress(task, progress)
            )
            
            if result.success:
                task.status = TaskStatus.COMPLETED
                task.filename = result.filename
                task.video_title = result.video_title
                task.thumbnail = result.thumbnail
                task.file_size = result.file_size
                task.completion_time = datetime.now()
                
                print(f"✅ Download completed: {task.id} -> {result.filename}")
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error
                print(f"❌ Download failed: {task.id} -> {result.error}")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            print(f"❌ Download error: {task.id} -> {e}")
        
        finally:
            # Move to completed tasks and remove from active
            if task in self.active_downloads:
                self.active_downloads.remove(task)
            
            # Keep completed tasks for history (limit to last 100)
            self.completed_tasks.append(task)
            if len(self.completed_tasks) > 100:
                self.completed_tasks.pop(0)
    
    def _update_task_progress(self, task: DownloadTask, progress: float):
        """Update task progress"""
        task.progress = min(100, max(0, progress))
    
    async def get_queue_status(self) -> QueueStatus:
        """Get detailed queue status"""
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        return QueueStatus(
            total_queue_size=len(self.download_queue) + len(self.active_downloads),
            active_downloads=len(self.active_downloads),
            queued_downloads=[task.to_dict() for task in self.download_queue],
            active_tasks=[task.to_dict() for task in self.active_downloads],
            server_uptime=uptime_str
        )
    
    async def get_download_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get download history"""
        # Combine active, completed, and recent tasks
        all_tasks = (
            self.active_downloads + 
            self.completed_tasks[-limit:] + 
            [task for task in self.download_queue if task.status != TaskStatus.QUEUED]
        )
        
        # Sort by creation time (newest first)
        all_tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return [task.to_dict() for task in all_tasks[:limit]]
    
    def get_task_by_id(self, task_id: str) -> Optional[DownloadTask]:
        """Find task by ID"""
        all_tasks = self.download_queue + self.active_downloads + self.completed_tasks
        
        for task in all_tasks:
            if task.id == task_id:
                return task
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Check queued tasks
        for task in self.download_queue[:]:
            if task.id == task_id:
                self.download_queue.remove(task)
                task.status = TaskStatus.CANCELLED
                self.completed_tasks.append(task)
                print(f"🚫 Cancelled queued task: {task_id}")
                return True
        
        # Check active tasks (harder to cancel, but mark as cancelled)
        for task in self.active_downloads:
            if task.id == task_id:
                task.status = TaskStatus.CANCELLED
                print(f"🚫 Marked active task as cancelled: {task_id}")
                return True
        
        return False
    
    async def clear_queue(self) -> int:
        """Clear queued downloads"""
        cleared_count = len(self.download_queue)
        
        # Move queued tasks to completed with cancelled status
        for task in self.download_queue:
            task.status = TaskStatus.CANCELLED
            self.completed_tasks.append(task)
        
        self.download_queue.clear()
        
        print(f"🧹 Cleared {cleared_count} queued downloads")
        return cleared_count
    
    def _start_shutdown_timer(self):
        """Start or restart the shutdown timer"""
        if self.shutdown_timer:
            self.shutdown_timer.cancel()
        
        self.shutdown_timer = asyncio.create_task(self._shutdown_after_delay())
    
    async def _shutdown_after_delay(self):
        """Shutdown server after delay if no activity"""
        await asyncio.sleep(settings.SHUTDOWN_DELAY)
        
        # Check if there's still no activity
        if not self.download_queue and not self.active_downloads:
            print(f"⏰ No activity for {settings.SHUTDOWN_DELAY}s, shutting down...")
            os._exit(0)
    
    def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()