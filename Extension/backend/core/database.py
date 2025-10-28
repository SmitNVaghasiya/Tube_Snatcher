from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect_to_database(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close_database(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index for IP address in downloaded_videos
            await self.db.downloaded_videos.create_index("ip_address")
            await self.db.downloaded_videos.create_index("download_timestamp")
            await self.db.downloaded_videos.create_index("success")
            
            # Index for unique visitors
            await self.db.unique_visitors.create_index("ip_address", unique=True)
            await self.db.unique_visitors.create_index("first_seen")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def log_download(self, download_info: Dict[str, Any]):
        """Log download to database"""
        try:
            # Insert download record
            await self.db.downloaded_videos.insert_one(download_info)
            
            # Update unique visitor stats
            await self.update_visitor_stats(
                download_info.get('ip_address'), 
                download_info.get('user_agent', 'unknown')
            )
            
        except Exception as e:
            logger.error(f"Failed to log download: {e}")
    
    async def update_visitor_stats(self, ip_address: str, user_agent: str):
        """Update unique visitor and download count"""
        try:
            result = await self.db.unique_visitors.find_one_and_update(
                {"ip_address": ip_address},
                {
                    "$set": {
                        "last_seen": datetime.utcnow(),
                        "user_agent": user_agent
                    },
                    "$inc": {"total_downloads": 1},
                    "$setOnInsert": {
                        "first_seen": datetime.utcnow()
                    }
                },
                upsert=True,
                return_document=True
            )
            
            if result is None:
                logger.warning(f"Failed to update visitor stats for IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Failed to update visitor stats: {e}")
    
    async def get_analytics(self):
        """Get download analytics"""
        try:
            total_downloads = await self.db.downloaded_videos.count_documents({})
            successful_downloads = await self.db.downloaded_videos.count_documents({"success": True})
            failed_downloads = total_downloads - successful_downloads
            unique_users = await self.db.unique_visitors.count_documents({})
            
            # Get recent downloads
            recent_downloads = await self.db.downloaded_videos.find().sort(
                "download_timestamp", -1
            ).limit(10).to_list(length=10)
            
            # Convert ObjectId to string for serialization
            for download in recent_downloads:
                if "_id" in download:
                    download["_id"] = str(download["_id"])
            
            return {
                "total_downloads": total_downloads,
                "successful_downloads": successful_downloads,
                "failed_downloads": failed_downloads,
                "unique_users": unique_users,
                "recent_downloads": recent_downloads
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {
                "total_downloads": 0,
                "successful_downloads": 0,
                "failed_downloads": 0,
                "unique_users": 0,
                "recent_downloads": []
            }

# Global database instance
db_manager = DatabaseManager()

def get_database():
    """Dependency for database access"""
    return db_manager.db