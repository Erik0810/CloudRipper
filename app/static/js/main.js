document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const playlistUrlInput = document.getElementById("playlist-url");
  const ripButton = document.getElementById("rip-button");
  const statusContainer = document.getElementById("status-container");
  const statusOutput = document.getElementById("status-output");
  const progressIndicator = document.getElementById("progress-indicator");
  const progressText = document.getElementById("progress-text");
  const downloadContainer = document.getElementById("download-container");
  const downloadButton = document.getElementById("download-button");
  const errorContainer = document.getElementById("error-container");
  const errorOutput = document.getElementById("error-output");

  let currentTaskId = null;
  let statusCheckInterval = null;

  // Add glitch effect to terminal occasionally
  setInterval(() => {
    const terminal = document.querySelector(".terminal");
    terminal.style.transform = "translate(-2px, 0)";
    setTimeout(() => {
      terminal.style.transform = "translate(2px, 0)";
      setTimeout(() => {
        terminal.style.transform = "translate(0, 0)";
      }, 50);
    }, 50);
  }, 10000);

  // Add typing effect to terminal lines
  document
    .querySelectorAll(".terminal-line:not(.input-container) .command")
    .forEach((cmd) => {
      const text = cmd.textContent;
      cmd.textContent = "";
      let i = 0;
      const typeInterval = setInterval(() => {
        if (i < text.length) {
          cmd.textContent += text.charAt(i);
          i++;
        } else {
          clearInterval(typeInterval);
        }
      }, 50);
    });

  // Handle rip button click
  ripButton.addEventListener("click", async () => {
    const playlistUrl = playlistUrlInput.value.trim();

    if (!playlistUrl) {
      showError("Please enter a SoundCloud playlist URL");
      return;
    }

    if (!isValidSoundCloudUrl(playlistUrl)) {
      showError(
        "Invalid SoundCloud playlist URL. Please enter a valid URL (e.g., https://soundcloud.com/user/sets/playlist-name)",
      );
      return;
    }

    // Show status container and hide other containers
    statusContainer.classList.remove("hidden");
    downloadContainer.classList.add("hidden");
    errorContainer.classList.add("hidden");

    // Disable rip button
    ripButton.disabled = true;
    ripButton.textContent = "PROCESSING...";

    try {
      // Send request to process the playlist
      const response = await fetch("/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ playlist_url: playlistUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to process playlist");
      }

      const data = await response.json();
      currentTaskId = data.task_id;

      // Start checking status
      statusOutput.textContent = "Processing playlist...";
      updateProgress(10);
      startStatusCheck();
    } catch (error) {
      showError(error.message);
      ripButton.disabled = false;
      ripButton.textContent = "RIP";
    }
  });

  // Handle download button click
  downloadButton.addEventListener("click", () => {
    if (currentTaskId) {
      window.location.href = `/download/${currentTaskId}`;
    }
  });

  // Function to validate SoundCloud URL
  function isValidSoundCloudUrl(url) {
    const pattern =
      /^https?:\/\/(?:www\.)?soundcloud\.com\/[^\/]+\/sets\/[^\/]+/;
    return pattern.test(url);
  }

  // Function to show error
  function showError(message) {
    errorContainer.classList.remove("hidden");
    errorOutput.textContent = message;
    statusContainer.classList.add("hidden");
  }

  // Function to start checking status
  function startStatusCheck() {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
    }

    console.log("Starting status check for task:", currentTaskId); // Debug log

    statusCheckInterval = setInterval(async () => {
      try {
        console.log("Fetching status for:", currentTaskId); // Debug log

        const response = await fetch(`/status/${currentTaskId}`);
        console.log("Status response:", response); // Debug log

        if (!response.ok) {
          const errorText = await response.text();
          console.error("Status response not OK:", response.status, errorText); // Debug log
          throw new Error(`Failed to get status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Status data received:", data); // Debug log

        // Update status based on task status
        if (!data.status) {
          console.error("No status in response data:", data); // Debug log
          throw new Error("Invalid status data received");
        }

        // Update status based on task status
        switch (data.status) {
          case "pending":
            statusOutput.textContent = "Waiting in queue...";
            updateProgress(10);
            break;

          case "processing":
            statusOutput.textContent = "Downloading tracks from SoundCloud...";
            updateProgress(30);
            break;

          default:
            if (data.status.startsWith("processing:")) {
              const progressPercent = parseInt(data.status.split(":")[1], 10);
              console.log("Processing progress:", progressPercent); // Debug log
              statusOutput.textContent = `Downloading tracks from SoundCloud... (${progressPercent}%)`;
              updateProgress(progressPercent);
            } else if (data.status === "completed") {
              console.log("Download completed"); // Debug log
              statusOutput.textContent = "Download complete!";
              updateProgress(100);
              clearInterval(statusCheckInterval);
              showDownloadButton();
            } else if (data.status === "failed") {
              console.error("Download failed:", data.error_message); // Debug log
              showError(data.error_message || "Failed to download playlist");
              clearInterval(statusCheckInterval);
              ripButton.disabled = false;
              ripButton.textContent = "RIP";
            }
        }
      } catch (error) {
        console.error("Status check error:", error); // Debug log
        showError("Error checking status: " + error.message);
        clearInterval(statusCheckInterval);
        ripButton.disabled = false;
        ripButton.textContent = "RIP";
      }
    }, 2000);
  }

  function updateProgress(percent) {
    console.log("Updating progress:", percent); // Debug log
    progressIndicator.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
  }

  function showError(message) {
    console.error("Error:", message); // Debug log
    statusOutput.textContent = message;
    statusOutput.classList.add("error");
  }

  // Function to show download button
  function showDownloadButton() {
    console.log("Showing download button");
    downloadContainer.classList.remove("hidden");
    ripButton.disabled = false;
    ripButton.textContent = "RIP";
  }

  // Add some visual effects
  function addGlitchEffect() {
    const glitchElements = document.querySelectorAll(".glitch-text");
    glitchElements.forEach((el) => {
      el.style.transform = "skew(0.5deg)";
      setTimeout(() => {
        el.style.transform = "skew(-0.5deg)";
        setTimeout(() => {
          el.style.transform = "skew(0)";
        }, 100);
      }, 100);
    });
  }

  // Add random glitch effects
  setInterval(addGlitchEffect, 5000);
});
