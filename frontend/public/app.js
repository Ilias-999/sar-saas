const API_BASE_URL = `http://${window.location.hostname}:8000`;

const sarFileInput = document.getElementById("sarFileInput");
const selectFileButton = document.getElementById("selectFileButton");
const uploadButton = document.getElementById("uploadButton");
const selectedFileName = document.getElementById("selectedFileName");
const statusMessage = document.getElementById("statusMessage");
const uploadZone = document.getElementById("uploadZone");

const resultSection = document.getElementById("resultSection");
const summaryFilename = document.getElementById("summaryFilename");
const summaryMetricsCount = document.getElementById("summaryMetricsCount");
const summaryStatsCount = document.getElementById("summaryStatsCount");
const summaryMetricTypes = document.getElementById("summaryMetricTypes");

const metricTypeFilter = document.getElementById("metricTypeFilter");
const statsTableBody = document.getElementById("statsTableBody");

let currentStats = [];

// Announce to screen readers
function announceToScreenReader(message) {
  const announcement = document.createElement("div");
  announcement.setAttribute("aria-live", "polite");
  announcement.setAttribute("aria-atomic", "true");
  announcement.className = "sr-only";
  announcement.textContent = message;
  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => announcement.remove(), 1000);
}

selectFileButton.addEventListener("click", () => {
  sarFileInput.click();
});

sarFileInput.addEventListener("change", () => {
  const file = sarFileInput.files[0];

  if (!file) {
    selectedFileName.textContent = "No file selected";
    uploadButton.disabled = true;
    announceToScreenReader("No file selected");
    return;
  }

  selectedFileName.textContent = file.name;
  uploadButton.disabled = false;
  setStatus("", "");
  announceToScreenReader(`File selected: ${file.name}`);
});

uploadButton.addEventListener("click", async () => {
  const file = sarFileInput.files[0];

  if (!file) {
    setStatus("Please choose a SAR file first.", "error");
    return;
  }

  await uploadAndAnalyze(file);
});

uploadZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadZone.classList.add("drag-over");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});

uploadZone.addEventListener("drop", async (event) => {
  event.preventDefault();
  uploadZone.classList.remove("drag-over");

  const file = event.dataTransfer.files[0];

  if (!file) {
    setStatus("No file dropped.", "error");
    return;
  }

  sarFileInput.files = event.dataTransfer.files;
  selectedFileName.textContent = file.name;
  uploadButton.disabled = false;

  await uploadAndAnalyze(file);
});

metricTypeFilter.addEventListener("change", () => {
  renderStatsTable(currentStats);
  const selectedType = metricTypeFilter.value;
  const displayName = selectedType === "ALL" ? "all metric types" : selectedType;
  announceToScreenReader(`Filtered to ${displayName}`);
});

async function uploadAndAnalyze(file) {
  const formData = new FormData();
  formData.append("file", file);

  setLoadingState(true);
  setStatus("Uploading and analyzing file...", "loading");

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const message = data.detail || "Upload failed.";
      throw new Error(message);
    }

    currentStats = data.stats || [];

    renderSummary(data);
    populateMetricTypeFilter(currentStats);
    renderStatsTable(currentStats);

    resultSection.classList.remove("hidden");
    setStatus("File analyzed successfully.", "success");
    announceToScreenReader("Analysis complete. Results displayed below.");
  } catch (error) {
    console.error(error);
    const errorMessage = error.message || "An error occurred while analyzing the file.";
    setStatus(errorMessage, "error");
    announceToScreenReader(`Error: ${errorMessage}`);
  } finally {
    setLoadingState(false);
  }
}

function renderSummary(data) {
  const metricTypes = new Set();

  for (const stat of data.stats || []) {
    metricTypes.add(stat.metric_type);
  }

  summaryFilename.textContent = data.filename || "-";
  summaryMetricsCount.textContent = data.metrics_count ?? 0;
  summaryStatsCount.textContent = data.stats_count ?? 0;
  summaryMetricTypes.textContent = metricTypes.size;

  // Announce summary to screen readers
  const summaryText = `Analysis summary: ${data.metrics_count} metrics parsed, ${data.stats_count} stats generated, ${metricTypes.size} metric types found.`;
  announceToScreenReader(summaryText);
}

function populateMetricTypeFilter(stats) {
  const existingValue = metricTypeFilter.value;

  metricTypeFilter.innerHTML = `<option value="ALL">All metric types</option>`;

  const metricTypes = [...new Set(stats.map((stat) => stat.metric_type))].sort();

  for (const metricType of metricTypes) {
    const option = document.createElement("option");
    option.value = metricType;
    option.textContent = metricType;
    metricTypeFilter.appendChild(option);
  }

  if (metricTypes.includes(existingValue)) {
    metricTypeFilter.value = existingValue;
  }
}

function renderStatsTable(stats) {
  const selectedMetricType = metricTypeFilter.value;

  const filteredStats =
    selectedMetricType === "ALL"
      ? stats
      : stats.filter((stat) => stat.metric_type === selectedMetricType);

  statsTableBody.innerHTML = "";

  if (filteredStats.length === 0) {
    statsTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-row">No statistics found.</td>
      </tr>
    `;
    announceToScreenReader("No statistics found for the selected filter.");
    return;
  }

  for (const stat of filteredStats) {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>
        <span class="metric-type-pill">${escapeHtml(stat.metric_type)}</span>
      </td>
      <td>${escapeHtml(stat.device || "-")}</td>
      <td>${escapeHtml(stat.metric_name)}</td>
      <td>${formatNumber(stat.min_value)}</td>
      <td>${formatNumber(stat.max_value)}</td>
      <td>${formatNumber(stat.avg_value)}</td>
      <td>${stat.sample_count}</td>
    `;

    statsTableBody.appendChild(row);
  }

  // Announce table update
  announceToScreenReader(`Table updated with ${filteredStats.length} statistics.`);
}

function setLoadingState(isLoading) {
  uploadButton.disabled = isLoading || !sarFileInput.files[0];
  selectFileButton.disabled = isLoading;

  if (isLoading) {
    uploadButton.textContent = "Analyzing...";
    announceToScreenReader("Analysis in progress");
  } else {
    uploadButton.textContent = "Upload and analyze";
  }
}

function setStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = "status-message";

  if (type) {
    statusMessage.classList.add(type);
  }
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }

  return Number(value).toFixed(2);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
