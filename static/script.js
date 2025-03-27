$(document).ready(function () {
  let fetchStartTime;

  function fetchDetails() {
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    if (url === "") return;

    // Clear previous content
    $("#videoThumbnail").attr("src", "");
    $(".download-card.options").html("");
    $(".below-container").addClass("hidden");

    // Display fetching started message
    $("#videoDescription").text(`Fetching started for this URL: ${url}`);
    fetchStartTime = Date.now();

    $("#loadingCircle").show();
    try {
      $.ajax({
        type: "POST",
        url: "/fetch_details",
        data: { url: url, format: format },
        dataType: "json",
        success: function (response) {
          $("#loadingCircle").hide();
          var fetchEndTime = Date.now();
          var timeTaken = ((fetchEndTime - fetchStartTime) / 1000).toFixed(2);

          if (response.error) {
            $("#videoDescription").text(
              `Error: ${response.error}. Time taken: ${timeTaken} seconds`
            );
            $("#videoThumbnail").attr("src", "");
            $(".below-container").addClass("hidden");
            return;
          }

          if (response.type === "playlist") {
            $("#videoDescription").text(
              `Details fetched for ${url}. Time taken: ${timeTaken} seconds`
            );
            $("#videoThumbnail").attr("src", response.thumbnail);
            var videosHtml = `
                          <select id="playlistResolution">
                              <option value="best">Best Quality</option>
                              <option value="1080p">1080p</option>
                              <option value="720p">720p</option>
                              <option value="480p">480p</option>
                              <option value="360p">360p</option>
                              <option value="240p">240p</option>
                              <option value="144p">144p</option>
                          </select>
                          <div class="select-videos">
                              <input type="text" id="videoSelection" placeholder="e.g., 1,4,7-10,15">
                              <button id="downloadVideos">Download</button>
                          </div>
                          <div class="playlist-videos">`;
            response.videos.forEach(function (video, index) {
              var duration = video.duration
                ? `${Math.floor(video.duration / 60)}:${(video.duration % 60)
                    .toString()
                    .padStart(2, "0")}`
                : "N/A";
              var thumbnailUrl =
                video.thumbnail ||
                "https://via.placeholder.com/200x112?text=No+Thumbnail";
              var videoIndex = index + 1; // 1-based index for display
              videosHtml += `
                              <div class="video-box">
                                  <div class="video-selector" data-index="${index}">
                                      <img src="${thumbnailUrl}" alt="${video.title}" onload="this.parentElement.parentElement.classList.remove('loading')">
                                      <div class="loading-dots">...</div>
                                      <p class="video-title">${videoIndex}. ${video.title}</p>
                                  </div>
                                  <hr class="divider">
                                  <p>Duration: ${duration}</p>
                                  <hr class="divider secondary">
                                  <button class="download-video" data-url="${video.url}">Download</button>
                                  <input type="checkbox" id="video${index}" value="${video.url}" class="hidden-checkbox">
                              </div>
                          `;
            });
            videosHtml += `</div><button id="download">Download</button>`;
            $(".download-card.options").html(videosHtml);
            $(".below-container").removeClass("hidden");
          } else {
            $("#videoDescription").text(
              `Details fetched for ${url}. Time taken: ${timeTaken} seconds`
            );
            $("#videoThumbnail").attr("src", response.thumbnail);
            var formatsHtml = "";
            response.formats.forEach(function (fmt) {
              var sizeText = fmt.filesize ? fmt.filesize : "";
              formatsHtml += `
                              <div class="option">
                                  <span>${fmt.format_note}, ${fmt.resolution}${
                sizeText ? ", " + sizeText : ""
              }</span>
                                  <button class="downloadButton" data-format-id="${
                                    fmt.format_id
                                  }">Download</button>
                              </div>
                          `;
            });
            $(".download-card.options").html(formatsHtml);
            $(".below-container").removeClass("hidden");
          }
        },
        error: function (xhr, status, error) {
          $("#loadingCircle").hide();
          var fetchEndTime = Date.now();
          var timeTaken = ((fetchEndTime - fetchStartTime) / 1000).toFixed(2);
          $("#videoDescription").text(
            `An error occurred while fetching details. Time taken: ${timeTaken} seconds. Error: ${error}`
          );
          $("#videoThumbnail").attr("src", "");
          $(".below-container").addClass("hidden");
        },
      });
    } catch (e) {
      $("#loadingCircle").hide();
      var fetchEndTime = Date.now();
      var timeTaken = ((fetchEndTime - fetchStartTime) / 1000).toFixed(2);
      $("#videoDescription").text(
        `An error occurred: ${e.message}. Time taken: ${timeTaken} seconds`
      );
    }
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
    try {
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
              $("#loadingCircle").hide(); // Hide loading circle before download
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
                  if (downloadResponse.error) {
                    $("#videoDescription").text(
                      `Error: ${downloadResponse.error}`
                    );
                  } else {
                    $("#videoDescription").text(downloadResponse.message);
                  }
                  $('button[type="submit"]').prop("disabled", false);
                },
                error: function () {
                  $("#videoDescription").text("Download failed.");
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
        error: function () {
          $("#loadingCircle").hide();
          $("#videoDescription").text("An error occurred.");
          $('button[type="submit"]').prop("disabled", false);
        },
      });
    } catch (e) {
      $("#loadingCircle").hide();
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      $('button[type="submit"]').prop("disabled", false);
    }
  });

  $(document).on("click", ".video-selector", function () {
    var index = $(this).data("index");
    var checkbox = $(`#video${index}`);
    checkbox.prop("checked", !checkbox.prop("checked"));
  });

  $(document).on("input", "#videoSelection", function () {
    var selection = $(this).val().trim();
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
    });
  });

  $(document).on("click", "#downloadVideos, #download", function () {
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
    $("#download").prop("disabled", true);
    $("#downloadVideos").prop("disabled", true);
    $("#loadingCircle").hide(); // Hide loading circle before download
    downloadNextVideo(selectedVideos, 0, desiredHeight);
  });

  function downloadNextVideo(videos, index, desiredHeight) {
    if (index >= videos.length) {
      $("#download").prop("disabled", false);
      $("#downloadVideos").prop("disabled", false);
      $("#videoDescription").text("All selected videos have been downloaded.");
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
          if (downloadResponse.error) {
            console.error("Error downloading video:", downloadResponse.error);
          } else {
            $("#videoDescription").text(downloadResponse.message);
          }
          downloadNextVideo(videos, index + 1, desiredHeight);
        },
        error: function () {
          console.error("Download failed for video:", url);
          downloadNextVideo(videos, index + 1, desiredHeight);
        },
      });
    } catch (e) {
      console.error("Error during download:", e.message);
      downloadNextVideo(videos, index + 1, desiredHeight);
    }
  }

  $(document).on("click", ".downloadButton", function () {
    var url = $("#urlInput").val().trim();
    var formatId = $(this).data("format-id");
    var format = $("#formatSelect").val();
    if (url === "") return;
    $(this).prop("disabled", true);
    $("#loadingCircle").hide(); // Hide loading circle before download
    try {
      $.ajax({
        type: "POST",
        url: "/download",
        data: { url: url, format_id: formatId, format: format },
        dataType: "json",
        success: function (response) {
          if (response.error) {
            $("#videoDescription").text(`Error: ${response.error}`);
          } else {
            $("#videoDescription").text(response.message);
          }
          $(this).prop("disabled", false);
        }.bind(this),
        error: function () {
          $("#videoDescription").text("Download failed.");
          $(this).prop("disabled", false);
        }.bind(this),
      });
    } catch (e) {
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
    $(this).prop("disabled", true);
    $("#loadingCircle").hide(); // Hide loading circle before download
    try {
      $.ajax({
        type: "POST",
        url: "/download",
        data: { url: url, desired_height: desiredHeight, format: format },
        dataType: "json",
        success: function (response) {
          if (response.error) {
            $("#videoDescription").text(`Error: ${response.error}`);
          } else {
            $("#videoDescription").text(response.message);
          }
          $(this).prop("disabled", false);
        }.bind(this),
        error: function () {
          $("#videoDescription").text("Download failed.");
          $(this).prop("disabled", false);
        }.bind(this),
      });
    } catch (e) {
      $("#videoDescription").text(`An error occurred: ${e.message}`);
      $(this).prop("disabled", false);
    }
  });
});
