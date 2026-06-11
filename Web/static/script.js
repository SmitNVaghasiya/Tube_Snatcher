document.addEventListener('DOMContentLoaded', function () {
  let loadingTimerInterval = null;
  let playlistTotalCount = 0;
  let availableResolutions = new Set();

  // ── LocalStorage helpers ──────────────────────────────────────────────────

  function saveToLocalStorage() {
    localStorage.setItem('url', document.getElementById('urlInput').value);
    localStorage.setItem('format', document.getElementById('formatSelect').value);
    localStorage.setItem('videoDescription', document.getElementById('videoDescription').textContent);
    localStorage.setItem('videoThumbnail', document.getElementById('videoThumbnail').src);
    localStorage.setItem('downloadCardHtml', document.querySelector('.download-card.options').innerHTML);
  }

  function loadFromLocalStorage() {
    const url = localStorage.getItem('url');
    const format = localStorage.getItem('format');
    const desc = localStorage.getItem('videoDescription');
    const thumb = localStorage.getItem('videoThumbnail');
    const cardHtml = localStorage.getItem('downloadCardHtml');

    if (url) document.getElementById('urlInput').value = url;
    if (format) document.getElementById('formatSelect').value = format;
    if (desc) document.getElementById('videoDescription').textContent = desc;
    if (thumb) document.getElementById('videoThumbnail').src = thumb;
    if (cardHtml) {
      document.querySelector('.download-card.options').innerHTML = cardHtml;
      document.querySelector('.below-container').classList.remove('hidden');
      toggleDownloadSelectedButton();
    }
  }

  loadFromLocalStorage();

  // ── UI helpers ────────────────────────────────────────────────────────────

  function toggleDownloadSelectedButton() {
    const anyChecked = document.querySelectorAll('.playlist-videos input[type="checkbox"]:checked').length > 0;
    const btn = document.getElementById('downloadSelectedVideos');
    if (btn) btn.classList.toggle('hidden', !anyChecked);
  }

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
                startLoadingTimer();
                document.querySelector('.download-card.options').innerHTML = `
                  <select id="playlistResolution"><option value="best">Best Quality</option></select>
                  <div class="select-videos">
                    <input type="text" id="videoSelection" placeholder="e.g., 1,4,7-10,15" aria-label="Select video range">
                    <button id="downloadVideos" aria-label="Download selected videos">Download</button>
                  </div>
                  <div class="playlist-videos"></div>
                  <button id="downloadSelectedVideos" class="download-selected hidden" aria-label="Download checked videos">Download Selected Videos</button>`;
                document.querySelector('.below-container').classList.remove('hidden');

              } else if (data.type === 'video_update') {
                if (data.video.formats) {
                  data.video.formats.forEach(fmt => {
                    if (fmt.format_note && fmt.format_note.endsWith('p'))
                      availableResolutions.add(fmt.format_note);
                  });
                }
                const video = data.video;
                const index = document.querySelectorAll('.playlist-videos .video-box').length;
                const mins = Math.floor((video.duration || 0) / 60);
                const secs = ((video.duration || 0) % 60).toString().padStart(2, '0');
                const duration = video.duration ? `${mins}:${secs}` : 'N/A';
                const safeTitle = video.title.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                document.querySelector('.playlist-videos').insertAdjacentHTML('beforeend', `
                  <div class="video-box">
                    <div class="video-selector" data-index="${index}">
                      <input type="checkbox" id="video${index}" value="${video.url}" class="video-checkbox" aria-label="${safeTitle}">
                      <img src="${video.thumbnail || ''}" alt="${safeTitle}" loading="lazy">
                      <p class="video-title">${index + 1}. ${safeTitle}</p>
                    </div>
                    <hr class="divider">
                    <div class="video-info">
                      <p>Duration: ${duration}</p>
                      <div class="vertical-divider"></div>
                      <button class="download-video" data-url="${video.url}" aria-label="Download ${safeTitle}">Download</button>
                    </div>
                  </div>`);

              } else if (data.type === 'video') {
                setDescription(`Ready: ${data.title}`);
                document.getElementById('videoThumbnail').src = data.thumbnail || '';
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

    // Read only the first chunk to get video info, then download best format
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
          const lines = buffer.split('\n');
          for (const line of lines) {
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
        if (!response || response.type !== 'video') {
          hideLoading();
          submitBtn.disabled = false;
          return;
        }
        let bestFormat = response.formats[0];
        if (format === 'mp4') {
          let maxHeight = 0;
          response.formats.forEach(fmt => {
            if (fmt.resolution && fmt.resolution !== 'Audio Only') {
              const h = parseInt(fmt.resolution.split('x')[1]);
              if (h > maxHeight) { maxHeight = h; bestFormat = fmt; }
            }
          });
        }
        if (!bestFormat) { hideLoading(); submitBtn.disabled = false; return; }

        return fetch('/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ url, format_id: bestFormat.format_id, format }),
        }).then(r => r.json());
      })
      .then(downloadResponse => {
        if (!downloadResponse) return;
        hideLoading();
        setDescription(downloadResponse.error ? `Error: ${downloadResponse.error}` : downloadResponse.message);
        submitBtn.disabled = false;
        saveToLocalStorage();
      })
      .catch(err => {
        hideLoading();
        setDescription(`Error: ${err.message}`);
        submitBtn.disabled = false;
        saveToLocalStorage();
      });
  });

  // ── Delegated event handlers ──────────────────────────────────────────────

  document.addEventListener('click', function (e) {

    // Checkbox toggle via row click
    const selector = e.target.closest('.video-selector');
    if (selector && !e.target.matches('input[type="checkbox"]')) {
      const cb = document.getElementById(`video${selector.dataset.index}`);
      if (cb) { cb.checked = !cb.checked; toggleDownloadSelectedButton(); }
    }
    if (e.target.matches('.video-checkbox')) {
      toggleDownloadSelectedButton();
    }

    // Download individual video from playlist
    if (e.target.matches('.download-video')) {
      const url = e.target.dataset.url;
      const format = document.getElementById('formatSelect').value;
      const resEl = document.getElementById('playlistResolution');
      const selectedRes = resEl ? resEl.value : 'best';
      const desiredHeight = selectedRes === 'best' ? 'best' : selectedRes.replace('p', '');
      e.target.disabled = true;
      showLoading();

      fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ url, desired_height: desiredHeight, format }),
      })
        .then(r => r.json())
        .then(response => {
          hideLoading();
          setDescription(response.error ? `Error: ${response.error}` : response.message);
          e.target.disabled = false;
          saveToLocalStorage();
        })
        .catch(err => {
          hideLoading();
          setDescription(`Download failed: ${err.message}`);
          e.target.disabled = false;
          saveToLocalStorage();
        });
    }

    // Download specific format
    if (e.target.matches('.downloadButton')) {
      const url = document.getElementById('urlInput').value.trim();
      if (!url) return;
      const formatId = e.target.dataset.formatId;
      const format = document.getElementById('formatSelect').value;
      e.target.disabled = true;
      showLoading();

      fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ url, format_id: formatId, format }),
      })
        .then(r => r.json())
        .then(response => {
          hideLoading();
          setDescription(response.error ? `Error: ${response.error}` : response.message);
          e.target.disabled = false;
          saveToLocalStorage();
        })
        .catch(err => {
          hideLoading();
          setDescription(`Download failed: ${err.message}`);
          e.target.disabled = false;
          saveToLocalStorage();
        });
    }

    // Batch download selected playlist videos
    if (e.target.matches('#downloadVideos') || e.target.matches('#downloadSelectedVideos')) {
      const selectedVideos = Array.from(
        document.querySelectorAll('.playlist-videos input[type="checkbox"]:checked')
      ).map(cb => cb.value);
      if (selectedVideos.length === 0) {
        alert('Please select at least one video to download.');
        return;
      }
      const resEl = document.getElementById('playlistResolution');
      const selectedRes = resEl ? resEl.value : 'best';
      const desiredHeight = selectedRes === 'best' ? 'best' : selectedRes.replace('p', '');
      e.target.disabled = true;
      showLoading();
      downloadNextVideo(selectedVideos, 0, desiredHeight);
    }
  });

  // Video range input
  document.addEventListener('input', function (e) {
    if (!e.target.matches('#videoSelection')) return;
    const selection = e.target.value.trim();
    document.querySelectorAll('.playlist-videos input[type="checkbox"]').forEach(cb => cb.checked = false);
    if (!selection) { toggleDownloadSelectedButton(); return; }
    const selectedIndices = new Set();
    selection.split(',').map(s => s.trim()).forEach(range => {
      if (range.includes('-')) {
        const [start, end] = range.split('-').map(Number);
        for (let i = start - 1; i < end; i++) selectedIndices.add(i);
      } else {
        const n = Number(range) - 1;
        if (!isNaN(n)) selectedIndices.add(n);
      }
    });
    selectedIndices.forEach(i => {
      const cb = document.getElementById(`video${i}`);
      if (cb) cb.checked = true;
    });
    toggleDownloadSelectedButton();
  });

  // ── Sequential playlist download ─────────────────────────────────────────

  function downloadNextVideo(videos, index, desiredHeight) {
    if (index >= videos.length) {
      document.querySelectorAll('#downloadVideos, #downloadSelectedVideos').forEach(btn => btn.disabled = false);
      hideLoading();
      setDescription(`All ${videos.length} video(s) queued for download.`);
      saveToLocalStorage();
      toggleDownloadSelectedButton();
      return;
    }
    const url = videos[index];
    const format = document.getElementById('formatSelect').value;
    setDescription(`Queuing video ${index + 1} of ${videos.length}…`);

    fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ url, desired_height: desiredHeight, format }),
    })
      .then(r => r.json())
      .then(response => {
        if (response.error) setDescription(`Error on video ${index + 1}: ${response.error}`);
        saveToLocalStorage();
        downloadNextVideo(videos, index + 1, desiredHeight);
      })
      .catch(err => {
        setDescription(`Failed on video ${index + 1}: ${err.message}`);
        saveToLocalStorage();
        downloadNextVideo(videos, index + 1, desiredHeight);
      });
  }

  // ── Persist on input ──────────────────────────────────────────────────────

  document.getElementById('urlInput').addEventListener('input', fetchDetails);
  document.getElementById('formatSelect').addEventListener('change', fetchDetails);
  document.getElementById('urlInput').addEventListener('input', saveToLocalStorage);
  document.getElementById('formatSelect').addEventListener('change', saveToLocalStorage);
});
