$(document).ready(function () {
  let fetchStartTime;
  let availableResolutions = new Set(); // To store unique resolutions for the playlist

  function fetchDetails() {
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    console.log("fetchDetails called with URL:", url, "Format:", format); // Debug log
    if (url === "") {
      console.log("URL is empty, aborting fetchDetails");
      return;
    }

    // Clear previous content
    $("#videoThumbnail").attr("src", "");
    $(".download-card.options").html("");
    $(".below-container").addClass("hidden");
    availableResolutions.clear(); // Reset resolutions for new fetch

    // Display fetching started message
    $("#videoDescription").text(`Fetching started for this URL: ${url}`);
    fetchStartTime = Date.now();

    $("#loadingCircle").show();

    // Use Fetch API to handle streaming responses
    fetch("/fetch_details", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        url: url,
        format: format,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // Process the stream
        function processStream({ done, value }) {
          if (done) {
            $("#loadingCircle").hide();
            console.log("Stream complete");
            // Calculate and display the time taken
            const fetchEndTime = Date.now();
            const timeTaken = (fetchEndTime - fetchStartTime) / 1000;
            $("#videoDescription").append(
              `<br>Time taken: ${timeTaken.toFixed(2)} seconds`
            );
            // After all videos are fetched, populate the resolution dropdown
            if (availableResolutions.size > 0) {
              populateResolutionDropdown();
            }
            return;
          }

          // Decode the chunk and append to buffer
          buffer += decoder.decode(value, { stream: true });

          // Split buffer by newlines to process complete JSON objects
          let lines = buffer.split("\n");
          buffer = lines.pop(); // Keep the last (possibly incomplete) line in the buffer

          // Process each complete line
          lines.forEach((line) => {
            if (line.trim() === "") return; // Skip empty lines
            try {
              const data = JSON.parse(line);
              console.log("Received data:", data); // Debug log

              if (data.error) {
                $("#videoDescription").text(`Error: ${data.error}`);
                $("#videoThumbnail").attr("src", "");
                $(".below-container").addClass("hidden");
                $("#loadingCircle").hide();
                return;
              }

              if (data.type === "playlist") {
                console.log("Processing playlist data:", data);
                $("#videoDescription").text(
                  `Fetching playlist details: ${data.title}`
                );
                $("#videoThumbnail").attr(
                  "src",
                  data.thumbnail ||
                    "https://via.placeholder.com/200x112?text=No+Thumbnail"
                );
                var videosHtml = `
                              <select id="playlistResolution">
                                  <option value="best">Best Quality</option>
                              </select>
                              <div class="select-videos">
                                  <input type="text" id="videoSelection" placeholder="e.g., 1,4,7-10,15">
                                  <button id="downloadVideos">Download</button>
                              </div>
                              <div class="playlist-videos"></div>`;
                $(".download-card.options").html(videosHtml);
                $(".below-container").removeClass("hidden");
              } else if (data.type === "video_update") {
                console.log("Processing video update:", data.video);
                // Collect available resolutions from the video
                if (data.video.formats && Array.isArray(data.video.formats)) {
                  data.video.formats.forEach((fmt) => {
                    if (fmt.format_note && fmt.format_note.endsWith("p")) {
                      availableResolutions.add(fmt.format_note);
                    }
                  });
                }
                // Append a single video to the playlist
                var video = data.video;
                var index = $(".playlist-videos .video-box").length; // Current number of videos
                var duration = video.duration
                  ? `${Math.floor(video.duration / 60)}:${(video.duration % 60)
                      .toString()
                      .padStart(2, "0")}`
                  : "N/A";
                var thumbnailUrl =
                  video.thumbnail ||
                  "https://via.placeholder.com/200x112?text=No+Thumbnail";
                var videoIndex = index + 1; // 1-based index for display
                var videoHtml = `
                              <div class="video-box">
                                  <div class="video-selector" data-index="${index}">
                                      <img src="${thumbnailUrl}" alt="${video.title}" onload="this.parentElement.parentElement.classList.remove('loading')">
                                      <div class="loading-dots">...</div>
                                      <p class="video-title">${videoIndex}. ${video.title}</p>
                                  </div>
                                  <hr class="divider">
                                  <div class="video-info">
                                      <p>Duration: ${duration}</p>
                                      <button class="download-video" data-url="${video.url}">Download</button>
                                  </div>
                                  <input type="checkbox" id="video${index}" value="${video.url}" class="hidden-checkbox">
                              </div>`;
                $(".playlist-videos").append(videoHtml);
              } else if (data.type === "video") {
                console.log("Processing single video data:", data);
                // Single video
                $("#videoDescription").text(
                  `Details fetched for ${data.title}`
                );
                $("#videoThumbnail").attr(
                  "src",
                  data.thumbnail ||
                    "https://via.placeholder.com/200x112?text=No+Thumbnail"
                );
                var formatsHtml = "";
                if (data.formats && Array.isArray(data.formats)) {
                  data.formats.forEach(function (fmt) {
                    var sizeText = fmt.filesize ? fmt.filesize : "Size Unknown";
                    formatsHtml += `
                                    <div class="option">
                                        <span>${fmt.format_note}, ${fmt.resolution}, ${sizeText}</span>
                                        <button class="downloadButton" data-format-id="${fmt.format_id}">Download</button>
                                    </div>`;
                  });
                } else {
                  formatsHtml = `<div class="option"><span>No formats available</span></div>`;
                }
                $(".download-card.options").html(formatsHtml);
                $(".below-container").removeClass("hidden");
              } else {
                console.warn("Unknown data type received:", data.type);
              }
            } catch (e) {
              console.error("Error parsing JSON:", e, "Line:", line);
            }
          });

          // Continue reading the stream
          return reader.read().then(processStream);
        }

        return reader.read().then(processStream);
      })
      .catch((error) => {
        console.error("Fetch error:", error);
        $("#loadingCircle").hide();
        $("#videoDescription").text(
          `An error occurred while fetching details. Error: ${error.message}`
        );
        $("#videoThumbnail").attr("src", "");
        $(".below-container").addClass("hidden");
      });
  }

  // Function to populate the resolution dropdown dynamically
  function populateResolutionDropdown() {
    var $dropdown = $("#playlistResolution");
    $dropdown.empty(); // Clear existing options
    $dropdown.append('<option value="best">Best Quality</option>'); // Always include "Best Quality"
    // Sort resolutions in descending order (e.g., 1080p, 720p, etc.)
    var sortedResolutions = Array.from(availableResolutions).sort((a, b) => {
      return parseInt(b) - parseInt(a);
    });
    sortedResolutions.forEach((resolution) => {
      $dropdown.append(`<option value="${resolution}">${resolution}</option>`);
    });
  }

  // Debug event binding
  $("#urlInput").on("input", function () {
    console.log("URL input event triggered"); // Debug log
    fetchDetails();
  });

  $("#formatSelect").on("change", function () {
    console.log("Format select change event triggered"); // Debug log
    fetchDetails();
  });

  $("#downloadForm").on("submit", function (e) {
    e.preventDefault();
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    console.log("Form submitted with URL:", url, "Format:", format); // Debug log
    if (url === "") return;
    $('button[type="submit"]').prop("disabled", true);
    $("#loadingCircle").show();
    try {
      $.ajax({
        type: "POST",
        url: "/fetch_details",
        data: { url: url, format: format },
        dataType: "json",
        success: function (response) {
          console.log("Form fetch details success:", response); // Debug log
          $("#loadingCircle").hide();
          if (response.error) {
            $("#videoDescription").text(`Error: ${response.error}`);
            $('button[type="submit"]').prop("disabled", false);
            return;
          }
          if (response.type === "video") {
            var bestFormat = response.formats[0];
            if (format === "mp4") {
              var maxHeight = 0;
              response.formats.forEach(function (fmt) {
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
                  console.log("Download success:", downloadResponse); // Debug log
                  $("#loadingCircle").hide();
                  if (downloadResponse.error) {
                    $("#videoDescription").text(
                      `Error: ${downloadResponse.error}`
                    );
                  } else {
                    $("#videoDescription").text(downloadResponse.message);
                  }
                  $('button[type="submit"]').prop("disabled", false);
                },
                error: function (xhr, status, error) {
                  console.error(
                    "Download failed:",
                    status,
                    error,
                    xhr.responseText
                  ); // Debug log
                  $("#loadingCircle").hide();
                  $("#videoDescription").text(
                    `Download failed: ${status} - ${error}`
                  );
                  $('button[type="submit"]').prop("disabled", false);
                },
              });
            } else {
              $("#loadingCircle").hide();
              $("#videoDescription").text("No suitable format found.");
              $('button[type="submit"]').prop("disabled", false);
            }
          } else {
            $('button[type="submit"]').prop("disabled", false);
          }
        },
        error: function (xhr, status, error) {
          console.error(
            "Form fetch details error:",
            status,
            error,
            xhr.responseText
          ); // Debug log
          $("#loadingCircle").hide();
          $("#videoDescription").text(
            `An error occurred: ${status} - ${error}`
          );
          $('button[type="submit"]').prop("disabled", false);
        },
      });
    } catch (e) {
      console.error("Exception in form submit:", e); // Debug log
      $("#loadingCircle").hide();
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      $('button[type="submit"]').prop("disabled", false);
    }
  });

  $(document).on("click", ".video-selector", function () {
    var index = $(this).data("index");
    var checkbox = $(`#video${index}`);
    checkbox.prop("checked", !checkbox.prop("checked"));
    console.log(`Video ${index} selected:`, checkbox.prop("checked")); // Debug log
  });

  $(document).on("input", "#videoSelection", function () {
    var selection = $(this).val().trim();
    console.log("Video selection input:", selection); // Debug log
    if (!selection) {
      $(".playlist-videos input[type='checkbox']").prop("checked", false);
      return;
    }

    // Clear previous selections
    $(".playlist-videos input[type='checkbox']").prop("checked", false);

    // Parse the input (e.g., "1,4,7-10,15")
    var ranges = selection.split(",").map((s) => s.trim());
    var selectedIndices = new Set();

    ranges.forEach((range) => {
      if (range.includes("-")) {
        var [start, end] = range.split("-").map(Number);
        for (var i = start - 1; i < end; i++) {
          selectedIndices.add(i);
        }
      } else {
        selectedIndices.add(Number(range) - 1);
      }
    });

    // Select the corresponding checkboxes
    selectedIndices.forEach((index) => {
      $(`#video${index}`).prop("checked", true);
      console.log(`Selected video index: ${index}`); // Debug log
    });
  });

  $(document).on("click", "#downloadVideos", function () {
    var selectedVideos = [];
    $(".playlist-videos input[type='checkbox']:checked").each(function () {
      selectedVideos.push($(this).val());
    });
    console.log("Selected videos for download:", selectedVideos); // Debug log
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

  function downloadNextVideo(videos, index, desiredHeight) {
    if (index >= videos.length) {
      $("#downloadVideos").prop("disabled", false);
      $("#loadingCircle").hide();
      $("#videoDescription").text("All selected videos have been downloaded.");
      console.log("All videos downloaded"); // Debug log
      return;
    }
    var url = videos[index];
    var format = $("#formatSelect").val();
    try {
      $.ajax({
        type: "POST",
        url: "/download",
        data: { url: url, desired_height: desiredHeight, format: format },
        dataType: "json",
        success: function (downloadResponse) {
          console.log("Download next video success:", downloadResponse); // Debug log
          if (downloadResponse.error) {
            console.error("Error downloading video:", downloadResponse.error);
            $("#videoDescription").text(`Error: ${downloadResponse.error}`);
          } else {
            $("#videoDescription").text(downloadResponse.message);
          }
          downloadNextVideo(videos, index + 1, desiredHeight);
        },
        error: function (xhr, status, error) {
          console.error(
            "Download failed for video:",
            url,
            status,
            error,
            xhr.responseText
          ); // Debug log
          $("#videoDescription").text(
            `Download failed for video ${index + 1}: ${status} - ${error}`
          );
          downloadNextVideo(videos, index + 1, desiredHeight);
        },
      });
    } catch (e) {
      console.error("Error during download:", e.message); // Debug log
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      downloadNextVideo(videos, index + 1, desiredHeight);
    }
  }

  $(document).on("click", ".downloadButton", function () {
    var url = $("#urlInput").val().trim();
    var formatId = $(this).data("format-id");
    var format = $("#formatSelect").val();
    console.log(
      "Download button clicked with URL:",
      url,
      "Format ID:",
      formatId,
      "Format:",
      format
    ); // Debug log
    if (url === "") return;
    $(this).prop("disabled", true);
    $("#loadingCircle").show();
    try {
      $.ajax({
        type: "POST",
        url: "/download",
        data: { url: url, format_id: formatId, format: format },
        dataType: "json",
        success: function (response) {
          console.log("Download success:", response); // Debug log
          $("#loadingCircle").hide();
          if (response.error) {
            $("#videoDescription").text(`Error: ${response.error}`);
          } else {
            $("#videoDescription").text(response.message);
          }
          $(this).prop("disabled", false);
        }.bind(this),
        error: function (xhr, status, error) {
          console.error("Download failed:", status, error, xhr.responseText); // Debug log
          $("#loadingCircle").hide();
          $("#videoDescription").text(`Download failed: ${status} - ${error}`);
          $(this).prop("disabled", false);
        }.bind(this),
      });
    } catch (e) {
      console.error("Exception in downloadButton:", e); // Debug log
      $("#loadingCircle").hide();
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      $(this).prop("disabled", false);
    }
  });

  $(document).on("click", ".download-video", function () {
    var url = $(this).data("url");
    var format = $("#formatSelect").val();
    var selectedResolution = $("#playlistResolution").val();
    var desiredHeight =
      selectedResolution === "best"
        ? "best"
        : selectedResolution.replace("p", "");
    console.log(
      "Download video clicked with URL:",
      url,
      "Resolution:",
      desiredHeight,
      "Format:",
      format
    ); // Debug log
    $(this).prop("disabled", true);
    $("#loadingCircle").show();
    try {
      $.ajax({
        type: "POST",
        url: "/download",
        data: { url: url, desired_height: desiredHeight, format: format },
        dataType: "json",
        success: function (response) {
          console.log("Download video success:", response); // Debug log
          $("#loadingCircle").hide();
          if (response.error) {
            $("#videoDescription").text(`Error: ${response.error}`);
          } else {
            $("#videoDescription").text(response.message);
          }
          $(this).prop("disabled", false);
        }.bind(this),
        error: function (xhr, status, error) {
          console.error(
            "Download failed for video:",
            url,
            status,
            error,
            xhr.responseText
          ); // Debug log
          $("#loadingCircle").hide();
          $("#videoDescription").text(`Download failed: ${status} - ${error}`);
          $(this).prop("disabled", false);
        }.bind(this),
      });
    } catch (e) {
      console.error("Exception in download-video:", e); // Debug log
      $("#loadingCircle").hide();
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      $(this).prop("disabled", false);
    }
  });
});
