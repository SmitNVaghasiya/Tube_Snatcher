document.addEventListener('DOMContentLoaded', function () {

  // ── State ────────────────────────────────────────────────────────────────

  let loadingTimerInterval = null;
  let playlistTotalCount = 0;
  let availableResolutions = new Set();
  const activePollers = {};   // task_id -> interval id

  // ── LocalStorage ─────────────────────────────────────────────────────────

  function saveToLocalStorage() {
    localStorage.setItem('url', document.getElementById('urlInput').value);
    localStorage.setItem('format', document.getElementById('formatSelect').value);
    const desc = document.getElementById('videoDescription');
    const thumb = document.getElementById('videoThumbnail');
    if (desc) localStorage.setItem('videoDescription', desc.textContent);
    if (thumb) localStorage.setItem('videoThumbnail', thumb.src);
    localStorage.setItem('downloadCardHtml', document.querySelector('.download-card.options').innerHTML);
  }

  function loadFromLocalStorage() {
    const url = localStorage.getItem('url');
    const format = localStorage.getItem('format');
    const desc = localStorage.getItem('videoDescription');
    const thumb = localStorage.getItem('videoThumbnail');
    const card = localStorage.getItem('downloadCardHtml');

    if (url) document.getElementById('urlInput').value = url;
    if (format) document.getElementById('formatSelect').value = format;
    if (desc) document.getElementById('videoDescription').textContent = desc;
    if (thumb) document.getElementById('videoThumbnail').src = thumb;
    if (card) {
      document.querySelector('.download-card.options').innerHTML = card;
      document.querySelector('.below-container').classList.remove('hidden');
      toggleDownloadSelectedButton();
    }
  }

  loadFromLocalStorage();

  // ── Cookie helpers (sessionStorage for security) ─────────────────────────

  function getCookies() {
    return sessionStorage.getItem('yt_cookies') || '';
  }

  function persistCookies(val) {
    const trimmed = val.trim();
    if (trimmed) {
      sessionStorage.setItem('yt_cookies', trimmed);
      document.getElementById('cookieSavedIndicator').classList.remove('hidden');
      document.getElementById('cookieBadge').classList.remove('hidden');
    } else {
      sessionStorage.removeItem('yt_cookies');
      document.getElementById('cookieSavedIndicator').classList.add('hidden');
      document.getElementById('cookieBadge').classList.add('hidden');
    }
  }

  // Restore cookies from session on page load
  const savedCookies = getCookies();
  if (savedCookies) {
    document.getElementById('cookieInput').value = savedCookies;
    document.getElementById('cookieSavedIndicator').classList.remove('hidden');
    document.getElementById('cookieBadge').classList.remove('hidden');
  }

  document.getElementById('toggleCookies').addEventListener('click', function () {
    const panel = document.getElementById('cookiePanel');
    const expanded = !panel.classList.contains('hidden');
    panel.classList.toggle('hidden', expanded);
    this.setAttribute('aria-expanded', String(!expanded));
    this.classList.toggle('active', !expanded);
  });

  document.getElementById('cookieInput').addEventListener('input', function () {
    persistCookies(this.value);
  });

  document.getElementById('clearCookies').addEventListener('click', function () {
    document.getElementById('cookieInput').value = '';
    persistCookies('');
  });

  // ── UI helpers ───────────────────────────────────────────────────────────

  function setDescription(text) {
    document.getElementById('videoDescription').textContent = text;
  }

  function showLoading() {
    document.getElementById('loadingCircle').style.display = 'block';
  }

  function hideLoading() {
    document.getElementById('loadingCircle').style.display = 'none';
    stopLoadingTimer();
    document.getElementById('loadingMessage').style.display = 'none';
  }

  function toggleDownloadSelectedButton() {
    const anyChecked = document.querySelectorAll('.playlist-videos input[type="checkbox"]:checked').length > 0;
    const btn = document.getElementById('downloadSelectedVideos');
    if (btn) btn.classList.toggle('hidden', !anyChecked);
  }

  function showSuccessToast(message) {
    const toast = document.getElementById('successToast');
    toast.textContent = '✓ ' + message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 4000);
  }

  // ── Live elapsed timer ────────────────────────────────────────────────────

  function startLoadingTimer() {
    const start = Date.now();
    const msgEl = document.getElementById('loadingMessage');
    clearInterval(loadingTimerInterval);
    loadingTimerInterval = setInterval(function () {
      const elapsed = Math.floor((Date.now() - start) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      const timeStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
      const loaded = document.querySelectorAll('.playlist-videos .video-box').length;
      const total = playlistTotalCount || '?';
      msgEl.textContent = loaded > 0
        ? `Loading playlist… ${loaded} / ${total} videos — ${timeStr} elapsed`
        : `Fetching playlist details… ${timeStr} elapsed`;
      msgEl.style.display = 'block';
    }, 1000);
  }

  function stopLoadingTimer() {
    clearInterval(loadingTimerInterval);
    loadingTimerInterval = null;
  }

  // ── Resolution dropdown ───────────────────────────────────────────────────

  function populateResolutionDropdown() {
    const dropdown = document.getElementById('playlistResolution');
    if (!dropdown) return;
    dropdown.innerHTML = '<option value="best">Best Quality</option>';
    Array.from(availableResolutions)
      .sort((a, b) => parseInt(b) - parseInt(a))
      .forEach(res => {
        const opt = document.createElement('option');
        opt.value = res;
        opt.textContent = res;
        dropdown.appendChild(opt);
      });
  }

  // ── Progress card system ──────────────────────────────────────────────────

  function createProgressCard(taskId, title) {
    const container = document.getElementById('downloadProgressList');
    container.insertAdjacentHTML('beforeend', `
      <div class="progress-card" id="progress-${taskId}">
        <div class="progress-card-header">
          <span class="progress-title">${title || 'Downloading…'}</span>
          <button class="cancel-btn" data-task-id="${taskId}" aria-label="Cancel">✕</button>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="fill-${taskId}" style="width:0%"></div>
        </div>
        <div class="progress-footer">
          <span class="progress-pct" id="pct-${taskId}">Queued</span>
        </div>
      </div>`);
    document.getElementById('activeDownloads').classList.remove('hidden');
  }

  function updateProgressCard(task) {
    const fill = document.getElementById(`fill-${task.id}`);
    const pct = document.getElementById(`pct-${task.id}`);
    const card = document.getElementById(`progress-${task.id}`);
    if (!fill || !pct || !card) return;

    if (task.status === 'downloading') {
      fill.style.width = `${task.progress}%`;
      pct.textContent = `${task.progress}%`;
    } else if (task.status === 'completed') {
      fill.style.width = '100%';
      fill.classList.add('completed');
      pct.textContent = '✓ Complete';
      card.classList.add('done');
      const cancelBtn = card.querySelector('.cancel-btn');
      if (cancelBtn) cancelBtn.remove();
    } else if (task.status === 'failed') {
      fill.classList.add('failed');
      pct.textContent = `✕ ${task.error || 'Download failed'}`;
      card.classList.add('failed-card');
    } else if (task.status === 'cancelled') {
      pct.textContent = 'Cancelled';
    }
  }

  function startProgressPolling(taskId, title) {
    createProgressCard(taskId, title);
    activePollers[taskId] = setInterval(function () {
      fetch(`/task/${taskId}`)
        .then(r => r.json())
        .then(task => {
          updateProgressCard(task);
          if (['completed', 'failed', 'cancelled'].includes(task.status)) {
            clearInterval(activePollers[taskId]);
            delete activePollers[taskId];
            setTimeout(() => {
              const card = document.getElementById(`progress-${task.id}`);
              if (card) card.classList.add('fading');
              setTimeout(() => {
                if (card) card.remove();
                if (!document.getElementById('downloadProgressList').children.length) {
                  document.getElementById('activeDownloads').classList.add('hidden');
                }
              }, 400);
            }, 3000);
            refreshHistory();
            if (task.status === 'completed') {
              showSuccessToast(`Downloaded: ${task.video_title || 'Video'}`);
            }
          }
        })
        .catch(() => {
          clearInterval(activePollers[taskId]);
          delete activePollers[taskId];
        });
    }, 1000);
  }

  // ── History ───────────────────────────────────────────────────────────────

  function refreshHistory() {
    fetch('/history')
      .then(r => r.json())
      .then(data => {
        if (!data.history || !data.history.length) {
          document.getElementById('historySection').classList.add('hidden');
          return;
        }
        document.getElementById('historySection').classList.remove('hidden');
        const list = document.getElementById('historyList');
        list.innerHTML = data.history.slice(0, 20).map(item => {
          const dateStr = item.completion_time || item.created_at;
          const timeLabel = dateStr ? new Date(dateStr).toLocaleString() : '';
          const icon = item.status === 'completed' ? '✓' : item.status === 'failed' ? '✕' : '—';
          const safeTitle = (item.video_title || 'Unknown video')
            .replace(/</g, '&lt;').replace(/>/g, '&gt;');
          return `
            <div class="history-item history-${item.status}">
              <span class="history-status-icon">${icon}</span>
              <div class="history-info">
                <span class="history-title">${safeTitle}</span>
                <span class="history-meta">${(item.format_type || 'mp4').toUpperCase()} · ${timeLabel}</span>
              </div>
            </div>`;
        }).join('');
      })
      .catch(() => {});
  }

  // Load history on startup
  refreshHistory();

  document.getElementById('clearHistory').addEventListener('click', function () {
    document.getElementById('historyList').innerHTML = '';
    document.getElementById('historySection').classList.add('hidden');
  });

  // ── Download helper ───────────────────────────────────────────────────────

  function queueDownload(params) {
    const body = new URLSearchParams(params);
    const cookies = getCookies();
    if (cookies) body.append('cookies', cookies);

    return fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
      .then(r => r.json())
      .then(response => {
        if (response.task_id) {
          startProgressPolling(response.task_id, null);
          setDescription(response.message);
        } else if (response.error) {
          setDescription(`Error: ${response.error}`);
        }
        saveToLocalStorage();
        return response;
      });
  }

  // ── Core fetch-details ────────────────────────────────────────────────────

  function fetchDetails() {
    const url = document.getElementById('urlInput').value.trim();
    const format = document.getElementById('formatSelect').value;
    if (!url) return;

    if (localStorage.getItem('url') !== url) {
      document.getElementById('videoThumbnail').src = '';
      document.querySelector('.download-card.options').innerHTML =
        '<div class="playlist-videos"></div>' +
        '<button id="downloadSelectedVideos" class="download-selected hidden">Download Selected Videos</button>';
      document.querySelector('.below-container').classList.add('hidden');
      document.querySelector('.below-container').classList.remove('playlist-mode');
      availableResolutions.clear();
      playlistTotalCount = 0;
    }

    setDescription(`Fetching info for: ${url}`);
    showLoading();
    document.getElementById('loadingMessage').style.display = 'none';

    fetch('/fetch_details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ url, format }),
    })
      .then(response => {
        if (!response.ok) throw new Error(`Server error ${response.status}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function processStream({ done, value }) {
          if (done) {
            hideLoading();
            if (availableResolutions.size > 0) populateResolutionDropdown();
            saveToLocalStorage();
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop();

          lines.forEach(line => {
            if (!line.trim()) return;
            try {
              const data = JSON.parse(line);

              if (data.error) {
                setDescription(`Error: ${data.error}`);
                document.getElementById('videoThumbnail').src = '';
                document.querySelector('.below-container').classList.add('hidden');
                hideLoading();
                saveToLocalStorage();
                return;
              }

              if (data.type === 'playlist') {
                playlistTotalCount = data.video_count;
                setDescription(`Playlist: "${data.title}" — ${data.video_count} videos`);
                document.getElementById('videoThumbnail').src = data.thumbnail || '';
                document.querySelector('.below-container').classList.add('playlist-mode');
                startLoadingTimer();
                document.querySelector('.download-card.options').innerHTML = `
                  <select id="playlistResolution" aria-label="Resolution">
                    <option value="best">Best Quality</option>
                  </select>
                  <div class="select-videos">
                    <input type="text" id="videoSelection" placeholder="e.g., 1,4,7-10,15" aria-label="Video selection range">
                    <button id="downloadVideos" aria-label="Download selected">Download</button>
                  </div>
                  <div class="playlist-videos"></div>
                  <button id="downloadSelectedVideos" class="download-selected hidden" aria-label="Download checked videos">
                    Download Selected Videos
                  </button>`;
                document.querySelector('.below-container').classList.remove('hidden');

              } else if (data.type === 'video_update') {
                if (data.video.formats) {
                  data.video.formats.forEach(fmt => {
                    if (fmt.format_note && fmt.format_note.endsWith('p'))
                      availableResolutions.add(fmt.format_note);
                  });
                }
                const v = data.video;
                const idx = document.querySelectorAll('.playlist-videos .video-box').length;
                const mins = Math.floor((v.duration || 0) / 60);
                const secs = ((v.duration || 0) % 60).toString().padStart(2, '0');
                const dur = v.duration ? `${mins}:${secs}` : 'N/A';
                const safeTitle = (v.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                document.querySelector('.playlist-videos').insertAdjacentHTML('beforeend', `
                  <div class="video-box">
                    <div class="video-selector" data-index="${idx}">
                      <input type="checkbox" id="video${idx}" value="${v.url}" class="video-checkbox" aria-label="${safeTitle}">
                      <img src="${v.thumbnail || ''}" alt="${safeTitle}" loading="lazy">
                      <p class="video-title">${idx + 1}. ${safeTitle}</p>
                    </div>
                    <hr class="divider">
                    <div class="video-info">
                      <p>Duration: ${dur}</p>
                      <div class="vertical-divider"></div>
                      <button class="download-video" data-url="${v.url}" aria-label="Download ${safeTitle}">Download</button>
                    </div>
                  </div>`);

              } else if (data.type === 'video') {
                setDescription(`Ready: ${data.title}`);
                document.getElementById('videoThumbnail').src = data.thumbnail || '';
                document.querySelector('.below-container').classList.remove('playlist-mode');
                const formatsHtml = data.formats && data.formats.length
                  ? data.formats.map(fmt => `
                      <div class="option">
                        <span>${fmt.format_note}, ${fmt.resolution}, ${fmt.filesize || 'Size Unknown'}</span>
                        <button class="downloadButton" data-format-id="${fmt.format_id}" aria-label="Download ${fmt.format_note}">Download</button>
                      </div>`).join('')
                  : "<div class='option'><span>No formats available</span></div>";
                document.querySelector('.download-card.options').innerHTML = formatsHtml;
                document.querySelector('.below-container').classList.remove('hidden');
              }
            } catch (e) {
              console.error('Stream parse error:', e, 'Line:', line);
            }
          });

          return reader.read().then(processStream);
        }

        return reader.read().then(processStream);
      })
      .catch(error => {
        hideLoading();
        setDescription(`Error: ${error.message}`);
        document.getElementById('videoThumbnail').src = '';
        document.querySelector('.below-container').classList.add('hidden');
        saveToLocalStorage();
      });
  }

  // ── Form submit: quick download at best quality ───────────────────────────

  document.getElementById('downloadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const url = document.getElementById('urlInput').value.trim();
    const format = document.getElementById('formatSelect').value;
    if (!url) return;

    const submitBtn = document.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    showLoading();

    fetch('/fetch_details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ url, format }),
    })
      .then(r => {
        if (!r.ok) throw new Error(`Server error ${r.status}`);
        const reader = r.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        function readFirstVideo({ done, value }) {
          if (done) return null;
          buffer += decoder.decode(value, { stream: true });
          for (const line of buffer.split('\n')) {
            if (!line.trim()) continue;
            try {
              const d = JSON.parse(line);
              if (d.type === 'video') return d;
            } catch (_) {}
          }
          return reader.read().then(readFirstVideo);
        }
        return reader.read().then(readFirstVideo);
      })
      .then(response => {
        hideLoading();
        submitBtn.disabled = false;
        if (!response || response.type !== 'video') return;

        let bestFormat = response.formats[0];
        if (format === 'mp4') {
          let maxH = 0;
          response.formats.forEach(fmt => {
            if (fmt.resolution && fmt.resolution !== 'Audio Only') {
              const h = parseInt(fmt.resolution.split('x')[1]);
              if (h > maxH) { maxH = h; bestFormat = fmt; }
            }
          });
        }
        if (!bestFormat) return;
        queueDownload({ url, format_id: bestFormat.format_id, format });
      })
      .catch(err => {
        hideLoading();
        submitBtn.disabled = false;
        setDescription(`Error: ${err.message}`);
        saveToLocalStorage();
      });
  });

  // ── Delegated events ──────────────────────────────────────────────────────

  document.addEventListener('click', function (e) {

    // Toggle checkbox via row click
    const selector = e.target.closest('.video-selector');
    if (selector && !e.target.matches('input[type="checkbox"]')) {
      const cb = document.getElementById(`video${selector.dataset.index}`);
      if (cb) { cb.checked = !cb.checked; toggleDownloadSelectedButton(); }
    }
    if (e.target.matches('.video-checkbox')) toggleDownloadSelectedButton();

    // Cancel active download
    if (e.target.matches('.cancel-btn[data-task-id]')) {
      const taskId = e.target.dataset.taskId;
      fetch(`/task/${taskId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
          clearInterval(activePollers[taskId]);
          delete activePollers[taskId];
          const card = document.getElementById(`progress-${taskId}`);
          if (card) {
            card.classList.add('fading');
            setTimeout(() => {
              card.remove();
              if (!document.getElementById('downloadProgressList').children.length)
                document.getElementById('activeDownloads').classList.add('hidden');
            }, 400);
          }
        })
        .catch(() => {});
    }

    // Download individual playlist video
    if (e.target.matches('.download-video')) {
      const url = e.target.dataset.url;
      const format = document.getElementById('formatSelect').value;
      const resEl = document.getElementById('playlistResolution');
      const res = resEl ? resEl.value : 'best';
      const desiredHeight = res === 'best' ? 'best' : res.replace('p', '');
      e.target.disabled = true;
      queueDownload({ url, desired_height: desiredHeight, format })
        .then(() => { e.target.disabled = false; });
    }

    // Download specific format (single video)
    if (e.target.matches('.downloadButton')) {
      const url = document.getElementById('urlInput').value.trim();
      if (!url) return;
      const formatId = e.target.dataset.formatId;
      const format = document.getElementById('formatSelect').value;
      e.target.disabled = true;
      queueDownload({ url, format_id: formatId, format })
        .then(() => { e.target.disabled = false; });
    }

    // Batch download
    if (e.target.matches('#downloadVideos') || e.target.matches('#downloadSelectedVideos')) {
      const selected = Array.from(
        document.querySelectorAll('.playlist-videos input[type="checkbox"]:checked')
      ).map(cb => cb.value);
      if (!selected.length) { alert('Please select at least one video to download.'); return; }
      const resEl = document.getElementById('playlistResolution');
      const res = resEl ? resEl.value : 'best';
      const desiredHeight = res === 'best' ? 'best' : res.replace('p', '');
      e.target.disabled = true;
      downloadNextVideo(selected, 0, desiredHeight, e.target);
    }
  });

  // Video range input
  document.addEventListener('input', function (e) {
    if (!e.target.matches('#videoSelection')) return;
    document.querySelectorAll('.playlist-videos input[type="checkbox"]').forEach(cb => cb.checked = false);
    const val = e.target.value.trim();
    if (!val) { toggleDownloadSelectedButton(); return; }
    const indices = new Set();
    val.split(',').map(s => s.trim()).forEach(range => {
      if (range.includes('-')) {
        const [a, b] = range.split('-').map(Number);
        for (let i = a - 1; i < b; i++) indices.add(i);
      } else {
        const n = Number(range) - 1;
        if (!isNaN(n) && n >= 0) indices.add(n);
      }
    });
    indices.forEach(i => { const cb = document.getElementById(`video${i}`); if (cb) cb.checked = true; });
    toggleDownloadSelectedButton();
  });

  // ── Sequential playlist download ──────────────────────────────────────────

  function downloadNextVideo(videos, index, desiredHeight, triggerBtn) {
    if (index >= videos.length) {
      if (triggerBtn) triggerBtn.disabled = false;
      showSuccessToast(`All ${videos.length} video(s) queued for download.`);
      saveToLocalStorage();
      toggleDownloadSelectedButton();
      return;
    }
    const url = videos[index];
    const format = document.getElementById('formatSelect').value;
    setDescription(`Queuing video ${index + 1} of ${videos.length}…`);

    queueDownload({ url, desired_height: desiredHeight, format })
      .then(() => downloadNextVideo(videos, index + 1, desiredHeight, triggerBtn))
      .catch(() => downloadNextVideo(videos, index + 1, desiredHeight, triggerBtn));
  }

  // ── Persist on input ──────────────────────────────────────────────────────

  document.getElementById('urlInput').addEventListener('input', fetchDetails);
  document.getElementById('formatSelect').addEventListener('change', fetchDetails);
  document.getElementById('urlInput').addEventListener('input', saveToLocalStorage);
  document.getElementById('formatSelect').addEventListener('change', saveToLocalStorage);
});
