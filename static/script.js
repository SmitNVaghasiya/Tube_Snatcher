$(document).ready(function () {
  // Function to fetch video details and update UI (for individual resolution buttons)
  function fetchDetails() {
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val(); // Get selected format (mp4 or mp3)
    if (url === "") return;

    $("#loadingCircle").show();

    $.ajax({
      type: "POST",
      url: "/fetch_details",
      data: { url: url, format: format }, // Pass selected format to backend
      dataType: "json",
      success: function (response) {
        $("#loadingCircle").hide();

        if (response.error) {
          $("#videoDescription").text("Error: " + response.error);
          $("#videoThumbnail").attr("src", "");
          $(".below-container").addClass("hidden");
          return;
        }

        // Update UI with video details and formats
        $("#videoDescription").text(response.title);
        $("#videoThumbnail").attr("src", response.thumbnail);

        var formatsHtml = "";
        response.formats.forEach(function (fmt) {
          // Only show filesize if available
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
      },
      error: function () {
        $("#loadingCircle").hide();
        $("#videoDescription").text("An error occurred.");
        $("#videoThumbnail").attr("src", "");
        $(".below-container").addClass("hidden");
      },
    });
  }

  // Fetch details when the URL input or format dropdown changes
  $("#urlInput").on("input", function () {
    fetchDetails();
  });
  $("#formatSelect").on("change", function () {
    fetchDetails();
  });

  // Main download button (form submit event)
  $("#downloadForm").on("submit", function (e) {
    e.preventDefault(); // Prevent page reload
    var url = $("#urlInput").val().trim();
    var format = $("#formatSelect").val();
    if (url === "") return;

    $("#loadingCircle").show();

    // First, fetch details so we know which formats are available
    $.ajax({
      type: "POST",
      url: "/fetch_details",
      data: { url: url, format: format },
      dataType: "json",
      success: function (response) {
        $("#loadingCircle").hide();
        if (response.error) {
          $("#videoDescription").text("Error: " + response.error);
          return;
        }

        var bestFormat = null;
        if (format === "mp4") {
          // For MP4, choose the one with the highest resolution (by height)
          var maxHeight = 0;
          response.formats.forEach(function (fmt) {
            if (fmt.resolution && fmt.resolution !== "Audio Only") {
              var parts = fmt.resolution.split("x");
              if (parts.length === 2) {
                var height = parseInt(parts[1]);
                if (height > maxHeight) {
                  maxHeight = height;
                  bestFormat = fmt;
                }
              }
            }
          });
        } else {
          // For MP3, simply choose the first available option
          if (response.formats.length > 0) {
            bestFormat = response.formats[0];
          }
        }

        if (bestFormat) {
          // Trigger download using the best format's format_id
          $.ajax({
            type: "POST",
            url: "/download",
            data: { url: url, format_id: bestFormat.format_id },
            dataType: "json",
            success: function (downloadResponse) {
              if (downloadResponse.error) {
                $("#responseContainer").html(
                  "Error: " + downloadResponse.error
                );
              } else {
                $("#responseContainer").html(
                  'Download started: <a href="/download_file/' +
                    encodeURIComponent(downloadResponse.filename) +
                    '" download>Click here to download</a>'
                );
              }
            },
            error: function () {
              $("#responseContainer").html(
                "An error occurred while downloading."
              );
            },
          });
        } else {
          $("#responseContainer").html("No suitable format found.");
        }
      },
      error: function () {
        $("#loadingCircle").hide();
        $("#videoDescription").text("An error occurred.");
      },
    });
  });

  // Individual resolution download buttons
  $(document).on("click", ".downloadButton", function () {
    var url = $("#urlInput").val().trim();
    var formatId = $(this).data("format-id");
    if (url === "") return;

    $.ajax({
      type: "POST",
      url: "/download",
      data: { url: url, format_id: formatId },
      dataType: "json",
      success: function (response) {
        if (response.error) {
          $("#responseContainer").html("Error: " + response.error);
        } else {
          $("#responseContainer").html(
            'Download started: <a href="/download_file/' +
              encodeURIComponent(response.filename) +
              '" download>Click here to download</a>'
          );
        }
      },
      error: function () {
        $("#responseContainer").html("An error occurred.");
      },
    });
  });
});
