$(document).ready(function () {
  let fetchStartTime;
  let availableResolutions = new Set();

  // Save data to local storage
  function saveToLocalStorage() {
    localStorage.setItem("url", $("#urlInput").val());
    localStorage.setItem("format", $("#formatSelect").val());
    localStorage.setItem("videoDescription", $("#videoDescription").text());
    localStorage.setItem("videoThumbnail", $("#videoThumbnail").attr("src"));
    localStorage.setItem(
      "downloadCardHtml",
      $(".download-card.options").html()
    );
  }

  // Load data from local storage
  function loadFromLocalStorage() {
    const url = localStorage.getItem("url");
    const format = localStorage.getItem("format");
    const videoDescription = localStorage.getItem("videoDescription");
    const videoThumbnail = localStorage.getItem("videoThumbnail");
    const downloadCardHtml = localStorage.getItem("downloadCardHtml");

    if (url) $("#urlInput").val(url);
    if (format) $("#formatSelect").val(format);
    if (videoDescription) $("#videoDescription").text(videoDescription);
    if (videoThumbnail) $("#videoThumbnail").attr("src", videoThumbnail);
    if (downloadCardHtml) {
      $(".download-card.options").html(downloadCardHtml);
      $(".below-container").removeClass("hidden");
      toggleDownloadSelectedButton();
    }
  }

  // Load persisted data on page load
  loadFromLocalStorage();

  // Toggle visibility of "Download Selected Videos" button based on selections
  function toggleDownloadSelectedButton() {
    const anyChecked =
      $(".playlist-videos input[type='checkbox']:checked").length > 0;
    $("#downloadSelectedVideos").toggleClass("hidden", !anyChecked);
  }

  function fetchDetails() {
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    if (url === "") return;

    // Only clear if URL has changed
    if (localStorage.getItem("url") !== url) {
      $("#videoThumbnail").attr("src", "");
      $(".download-card.options").html(
        '<div class="playlist-videos"></div><button id="downloadSelectedVideos" class="download-selected hidden">Download Selected Videos</button>'
      );
      $(".below-container").addClass("hidden");
      availableResolutions.clear();
    }

    $("#videoDescription").text(`Fetching started for this URL: ${url}`);
    fetchStartTime = Date.now();
    $("#loadingCircle").show();
    $("#loadingMessage").hide(); // Hide message by default

    console.log(`Fetching playlist: ${url}`);

    fetch("/fetch_details", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ url: url, format: format }),
    })
      .then((response) => {
        if (!response.ok)
          throw new Error(`HTTP error! Status: ${response.status}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        function processStream({ done, value }) {
          if (done) {
            $("#loadingCircle").hide();
            $("#loadingMessage").hide();
            const fetchEndTime = Date.now();
            const timeTaken = (fetchEndTime - fetchStartTime) / 1000;
            console.log(`Time taken: ${timeTaken.toFixed(2)} seconds`);
            if (availableResolutions.size > 0) populateResolutionDropdown();
            saveToLocalStorage();
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          let lines = buffer.split("\n");
          buffer = lines.pop();

          lines.forEach((line) => {
            if (line.trim() === "") return;
            try {
              const data = JSON.parse(line);
              if (data.error) {
                $("#videoDescription").text(`Error: ${data.error}`);
                $("#videoThumbnail").attr("src", "");
                $(".below-container").addClass("hidden");
                $("#loadingCircle").hide();
                $("#loadingMessage").hide();
                saveToLocalStorage();
                return;
              }

              if (data.type === "playlist") {
                $("#videoDescription").text(
                  `Playlist detected: ${data.title} with ${data.video_count} videos`
                );
                $("#loadingMessage")
                  .text(
                    "Fetching playlist details, this may take around 4 to 5 minutes."
                  )
                  .show();
                $("#videoThumbnail").attr(
                  "src",
                  data.thumbnail ||
                    "https://via.placeholder.com/200x112?text=No+Thumbnail"
                );
                var videosHtml = `
                  <select id="playlistResolution"><option value="best">Best Quality</option></select>
                  <div class="select-videos">
                    <input type="text" id="videoSelection" placeholder="e.g., 1,4,7-10,15">
                    <button id="downloadVideos">Download</button>
                  </div>
                  <div class="playlist-videos"></div>
                  <button id="downloadSelectedVideos" class="download-selected hidden">Download Selected Videos</button>`;
                $(".download-card.options").html(videosHtml);
                $(".below-container").removeClass("hidden");
              } else if (data.type === "video_update") {
                if (data.video.formats) {
                  data.video.formats.forEach((fmt) => {
                    if (fmt.format_note && fmt.format_note.endsWith("p"))
                      availableResolutions.add(fmt.format_note);
                  });
                }
                var video = data.video;
                var index = $(".playlist-videos .video-box").length;
                var duration = video.duration
                  ? `${Math.floor(video.duration / 60)}:${(video.duration % 60)
                      .toString()
                      .padStart(2, "0")}`
                  : "N/A";
                var thumbnailUrl =
                  video.thumbnail ||
                  "https://via.placeholder.com/200x112?text=No+Thumbnail";
                var videoIndex = index + 1;
                var videoHtml = `
                  <div class="video-box loading">
                    <div class="video-selector" data-index="${index}">
                      <input type="checkbox" id="video${index}" value="${video.url}" class="video-checkbox">
                      <img src="${thumbnailUrl}" alt="${video.title}">
                      <div class="loading-dots">...</div>
                      <p class="video-title">${videoIndex}. ${video.title}</p>
                    </div>
                    <hr class="divider">
                    <div class="video-info">
                      <p>Duration: ${duration}</p>
                      <div class="vertical-divider"></div>
                      <button class="download-video" data-url="${video.url}">Download</button>
                    </div>
                  </div>`;
                $(".playlist-videos").append(videoHtml);
                // Remove loading class after appending
                $(`.video-box[data-index="${index}"]`).removeClass("loading");
              } else if (data.type === "video") {
                $("#videoDescription").text(
                  `Details fetched for ${data.title}`
                );
                $("#videoThumbnail").attr(
                  "src",
                  data.thumbnail ||
                    "https://via.placeholder.com/200x112?text=No+Thumbnail"
                );
                var formatsHtml = data.formats
                  ? data.formats
                      .map(
                        (fmt) => `
                  <div class="option">
                    <span>${fmt.format_note}, ${fmt.resolution}, ${
                          fmt.filesize || "Size Unknown"
                        }</span>
                    <button class="downloadButton" data-format-id="${
                      fmt.format_id
                    }">Download</button>
                  </div>`
                      )
                      .join("")
                  : "<div class='option'><span>No formats available</span></div>";
                $(".download-card.options").html(formatsHtml);
                $(".below-container").removeClass("hidden");
              }
            } catch (e) {
              console.error("Error parsing JSON:", e, "Line:", line);
            }
          });

          return reader.read().then(processStream);
        }

        return reader.read().then(processStream);
      })
      .catch((error) => {
        console.error("Fetch error:", error);
        $("#loadingCircle").hide();
        $("#loadingMessage").hide();
        $("#videoDescription").text(`An error occurred: ${error.message}`);
        $("#videoThumbnail").attr("src", "");
        $(".below-container").addClass("hidden");
        saveToLocalStorage();
      });
  }

  function populateResolutionDropdown() {
    var $dropdown = $("#playlistResolution");
    $dropdown.empty();
    $dropdown.append('<option value="best">Best Quality</option>');
    var sortedResolutions = Array.from(availableResolutions).sort(
      (a, b) => parseInt(b) - parseInt(a)
    );
    sortedResolutions.forEach((resolution) =>
      $dropdown.append(`<option value="${resolution}">${resolution}</option>`)
    );
  }

  $("#urlInput").on("input", fetchDetails);
  $("#formatSelect").on("change", fetchDetails);

  $("#downloadForm").on("submit", function (e) {
    e.preventDefault();
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    if (url === "") return;
    $('button[type="submit"]').prop("disabled", true);
    $("#loadingCircle").show();

    $.ajax({
      type: "POST",
      url: "/fetch_details",
      data: { url: url, format: format },
      dataType: "json",
      success: function (response) {
        $("#loadingCircle").hide();
        if (response.error) {
          $("#videoDescription").text(`Error: ${response.error}`);
          $('button[type="submit"]').prop("disabled", false);
          saveToLocalStorage();
          return;
        }
        if (response.type === "video") {
          var bestFormat = response.formats[0];
          if (format === "mp4") {
            var maxHeight = 0;
            response.formats.forEach((fmt) => {
              if (fmt.resolution && fmt.resolution !== "Audio Only") {
                var height = parseInt(fmt.resolution.split("x")[1]);
                if (height > maxHeight) {
                  maxHeight = height;
                  bestFormat = fmt;
                }
              }
            });
          }
          if (bestFormat) {
            $("#loadingCircle").show();
            $.ajax({
              type: "POST",
              url: "/download",
              data: {
                url: url,
                format_id: bestFormat.format_id,
                format: format,
              },
              dataType: "json",
              success: function (downloadResponse) {
                $("#loadingCircle").hide();
                $("#videoDescription").text(
                  downloadResponse.error
                    ? `Error: ${downloadResponse.error}`
                    : downloadResponse.message
                );
                $('button[type="submit"]').prop("disabled", false);
                saveToLocalStorage();
              },
              error: function (xhr, status, error) {
                $("#loadingCircle").hide();
                $("#videoDescription").text(
                  `Download failed: ${status} - ${error}`
                );
                $('button[type="submit"]').prop("disabled", false);
                saveToLocalStorage();
              },
            });
          }
        }
      },
      error: function (xhr, status, error) {
        $("#loadingCircle").hide();
        $("#videoDescription").text(`An error occurred: ${status} - ${error}`);
        $('button[type="submit"]').prop("disabled", false);
        saveToLocalStorage();
      },
    });
  });

  $(document).on("click", ".video-selector", function () {
    var index = $(this).data("index");
    var checkbox = $(`#video${index}`);
    checkbox.prop("checked", !checkbox.prop("checked"));
    toggleDownloadSelectedButton();
  });

  $(document).on("input", "#videoSelection", function () {
    var selection = $(this).val().trim();
    $(".playlist-videos input[type='checkbox']").prop("checked", false);
    if (!selection) {
      toggleDownloadSelectedButton();
      return;
    }

    var ranges = selection.split(",").map((s) => s.trim());
    var selectedIndices = new Set();

    ranges.forEach((range) => {
      if (range.includes("-")) {
        var [start, end] = range.split("-").map(Number);
        for (var i = start - 1; i < end; i++) selectedIndices.add(i);
      } else {
        selectedIndices.add(Number(range) - 1);
      }
    });

    selectedIndices.forEach((index) =>
      $(`#video${index}`).prop("checked", true)
    );
    toggleDownloadSelectedButton();
  });

  $(document).on("click", "#downloadVideos", function () {
    var selectedVideos = [];
    $(".playlist-videos input[type='checkbox']:checked").each(function () {
      selectedVideos.push($(this).val());
    });
    if (selectedVideos.length === 0) {
      alert("Please select at least one video to download.");
      return;
    }
    var selectedResolution = $("#playlistResolution").val();
    var desiredHeight =
      selectedResolution === "best"
        ? "best"
        : selectedResolution.replace("p", "");
    $("#downloadVideos").prop("disabled", true);
    $("#loadingCircle").show();
    downloadNextVideo(selectedVideos, 0, desiredHeight);
  });

  $(document).on("click", "#downloadSelectedVideos", function () {
    var selectedVideos = [];
    $(".playlist-videos input[type='checkbox']:checked").each(function () {
      selectedVideos.push($(this).val());
    });
    if (selectedVideos.length === 0) {
      alert("Please select at least one video to download.");
      return;
    }
    var selectedResolution = $("#playlistResolution").val();
    var desiredHeight =
      selectedResolution === "best"
        ? "best"
        : selectedResolution.replace("p", "");
    $("#downloadSelectedVideos").prop("disabled", true);
    $("#loadingCircle").show();
    downloadNextVideo(selectedVideos, 0, desiredHeight);
  });

  function downloadNextVideo(videos, index, desiredHeight) {
    if (index >= videos.length) {
      $("#downloadVideos").prop("disabled", false);
      $("#downloadSelectedVideos").prop("disabled", false);
      $("#loadingCircle").hide();
      $("#videoDescription").text("All selected videos have been downloaded.");
      saveToLocalStorage();
      toggleDownloadSelectedButton();
      return;
    }
    var url = videos[index];
    var format = $("#formatSelect").val();
    console.log(`Downloading video: ${url}`);
    $.ajax({
      type: "POST",
      url: "/download",
      data: { url: url, desired_height: desiredHeight, format: format },
      dataType: "json",
      success: function (downloadResponse) {
        $("#videoDescription").text(
          downloadResponse.error
            ? `Error: ${downloadResponse.error}`
            : downloadResponse.message
        );
        saveToLocalStorage();
        downloadNextVideo(videos, index + 1, desiredHeight);
      },
      error: function (xhr, status, error) {
        $("#videoDescription").text(
          `Download failed for video ${index + 1}: ${status} - ${error}`
        );
        saveToLocalStorage();
        downloadNextVideo(videos, index + 1, desiredHeight);
      },
    });
  }

  $(document).on("click", ".downloadButton", function () {
    var url = $("#urlInput").val().trim();
    var formatId = $(this).data("format-id");
    var format = $("#formatSelect").val();
    if (url === "") return;
    $(this).prop("disabled", true);
    $("#loadingCircle").show();

    console.log(`Downloading single video: ${url}`);

    $.ajax({
      type: "POST",
      url: "/download",
      data: { url: url, format_id: formatId, format: format },
      dataType: "json",
      success: function (response) {
        $("#loadingCircle").hide();
        $("#videoDescription").text(
          response.error ? `Error: ${response.error}` : response.message
        );
        $(this).prop("disabled", false);
        saveToLocalStorage();
      }.bind(this),
      error: function (xhr, status, error) {
        $("#loadingCircle").hide();
        $("#videoDescription").text(`Download failed: ${status} - ${error}`);
        $(this).prop("disabled", false);
        saveToLocalStorage();
      }.bind(this),
    });
  });

  $(document).on("click", ".download-video", function () {
    var url = $(this).data("url");
    var format = $("#formatSelect").val();
    var selectedResolution = $("#playlistResolution").val();
    var desiredHeight =
      selectedResolution === "best"
        ? "best"
        : selectedResolution.replace("p", "");
    $(this).prop("disabled", true);
    $("#loadingCircle").show();

    console.log(`Downloading video: ${url}`);

    $.ajax({
      type: "POST",
      url: "/download",
      data: { url: url, desired_height: desiredHeight, format: format },
      dataType: "json",
      success: function (response) {
        $("#loadingCircle").hide();
        $("#videoDescription").text(
          response.error ? `Error: ${response.error}` : response.message
        );
        $(this).prop("disabled", false);
        saveToLocalStorage();
      }.bind(this),
      error: function (xhr, status, error) {
        $("#loadingCircle").hide();
        $("#videoDescription").text(`Download failed: ${status} - ${error}`);
        $(this).prop("disabled", false);
        saveToLocalStorage();
      }.bind(this),
    });
  });

  // Save on input and change
  $("#urlInput").on("input", saveToLocalStorage);
  $("#formatSelect").on("change", saveToLocalStorage);
});
