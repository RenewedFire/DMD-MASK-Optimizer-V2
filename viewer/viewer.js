const state = {
  dataset: "",
  frameCount: 0,
  frameNumber: 0,
  mode: "exact",
  componentOverlay: "off",
  candidateOverlay: "off",
  currentFrame: null,
  selectedRelationship: null,
  playing: false,
  timer: null,
};

const datasetSelect = document.querySelector("#datasetSelect");
const loadButton = document.querySelector("#loadButton");
const previousButton = document.querySelector("#previousButton");
const nextButton = document.querySelector("#nextButton");
const playButton = document.querySelector("#playButton");
const frameInput = document.querySelector("#frameInput");
const jumpButton = document.querySelector("#jumpButton");
const modeSelect = document.querySelector("#modeSelect");
const componentOverlaySelect = document.querySelector("#componentOverlaySelect");
const candidateOverlaySelect = document.querySelector("#candidateOverlaySelect");
const datasetStatus = document.querySelector("#datasetStatus");
const frameStatus = document.querySelector("#frameStatus");
const headerStatus = document.querySelector("#headerStatus");
const componentStatus = document.querySelector("#componentStatus");
const relationshipStatus = document.querySelector("#relationshipStatus");
const candidateStatus = document.querySelector("#candidateStatus");
const relationshipDistanceInput = document.querySelector("#relationshipDistanceInput");
const relationshipLimitInput = document.querySelector("#relationshipLimitInput");
const relationshipComponentInput = document.querySelector("#relationshipComponentInput");
const relationshipSummary = document.querySelector("#relationshipSummary");
const relationshipList = document.querySelector("#relationshipList");
const errorMessage = document.querySelector("#errorMessage");
const canvas = document.querySelector("#dmdCanvas");
const context = canvas.getContext("2d");
const overlayCanvas = document.querySelector("#overlayCanvas");
const overlayContext = overlayCanvas.getContext("2d");

const exactPalette = [
  [0, 0, 0],
  [95, 35, 12],
  [188, 93, 22],
  [255, 192, 57],
];

const binaryPalette = [
  [0, 0, 0],
  [255, 192, 57],
];

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed");
  }
  return payload;
}

async function loadDatasets() {
  const payload = await fetchJson("/api/datasets");
  datasetSelect.innerHTML = "";
  for (const name of payload.datasets) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    datasetSelect.append(option);
  }
  if (payload.datasets.length > 0) {
    state.dataset = payload.datasets[0];
    datasetSelect.value = state.dataset;
    await loadDataset();
  }
}

async function loadDataset() {
  state.dataset = datasetSelect.value;
  state.frameNumber = 0;
  const payload = await fetchJson(`/api/dataset?name=${encodeURIComponent(state.dataset)}`);
  state.frameCount = payload.frame_count;
  frameInput.max = Math.max(0, state.frameCount - 1);
  datasetStatus.textContent = `${payload.name}: ${payload.frame_count} frames`;
  await loadFrame(0);
}

async function loadFrame(frameNumber) {
  if (!state.dataset || state.frameCount === 0) {
    return;
  }
  const bounded = Math.max(0, Math.min(state.frameCount - 1, frameNumber));
  const payload = await fetchJson(
    `/api/frame?name=${encodeURIComponent(state.dataset)}&frame=${bounded}`,
  );
  state.selectedRelationship = null;
  state.frameNumber = payload.frame.frame_number;
  frameInput.value = state.frameNumber;
  frameStatus.textContent = `Frame ${state.frameNumber + 1} of ${state.frameCount}`;
  headerStatus.textContent = `Header ${payload.frame.header}`;
  componentStatus.textContent = `${payload.frame.components.length} raw components`;
  relationshipStatus.textContent = `${payload.frame.relationship_count} relationships`;
  candidateStatus.textContent = `${payload.frame.candidate_box_count} candidate boxes`;
  state.currentFrame = payload.frame;
  drawFrame(payload.frame);
  renderRelationshipReview(payload.frame);
}

function drawFrame(frame) {
  const pixels = state.mode === "binary" ? frame.binary_pixels : frame.exact_pixels;
  const palette = state.mode === "binary" ? binaryPalette : exactPalette;
  const image = context.createImageData(128, 32);
  let offset = 0;
  for (const row of pixels) {
    for (const pixel of row) {
      const [red, green, blue] = palette[pixel];
      image.data[offset++] = red;
      image.data[offset++] = green;
      image.data[offset++] = blue;
      image.data[offset++] = 255;
    }
  }
  context.putImageData(image, 0, 0);
  drawAnalysisOverlay(frame);
}

function drawAnalysisOverlay(frame) {
  overlayContext.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
  drawComponentOverlay(frame.components || []);
  drawCandidateOverlay(frame.candidate_boxes || []);
}

function drawComponentOverlay(components) {
  if (state.componentOverlay === "off") {
    drawSelectedRelationship(components);
    return;
  }

  if (state.componentOverlay === "pixels" || state.componentOverlay === "both") {
    drawComponentPixels(components);
  }

  if (state.componentOverlay === "boxes" || state.componentOverlay === "both") {
    drawComponentBoxes(components);
  }
  drawSelectedRelationship(components);
}

function drawCandidateOverlay(candidates) {
  if (state.candidateOverlay === "off") {
    return;
  }

  const selectedCandidates = candidates.filter((candidate) => (
    state.candidateOverlay === "all" || String(candidate.threshold) === state.candidateOverlay
  ));

  overlayContext.save();
  overlayContext.imageSmoothingEnabled = false;
  overlayContext.lineWidth = 1;
  overlayContext.strokeStyle = "rgba(255, 255, 255, 0.95)";
  overlayContext.setLineDash([2, 2]);
  for (const candidate of selectedCandidates) {
    const box = candidate.bounding_box;
    overlayContext.strokeRect(box.min_x + 0.5, box.min_y + 0.5, box.width, box.height);
  }
  overlayContext.restore();
}

function componentColor(componentId, alpha) {
  const hue = (componentId * 47) % 360;
  return `hsla(${hue}, 95%, 62%, ${alpha})`;
}

function drawComponentPixels(components) {
  const image = overlayContext.createImageData(128, 32);
  for (const component of components) {
    const color = hslToRgb((component.component_id * 47) % 360, 0.95, 0.62);
    for (const pixel of component.pixels) {
      const offset = (pixel.y * 128 + pixel.x) * 4;
      image.data[offset] = color[0];
      image.data[offset + 1] = color[1];
      image.data[offset + 2] = color[2];
      image.data[offset + 3] = 150;
    }
  }
  overlayContext.putImageData(image, 0, 0);
}

function drawComponentBoxes(components) {
  overlayContext.save();
  overlayContext.imageSmoothingEnabled = false;
  overlayContext.lineWidth = 1;
  for (const component of components) {
    const box = component.bounding_box;
    overlayContext.strokeStyle = componentColor(component.component_id, 0.85);
    overlayContext.strokeRect(box.min_x + 0.5, box.min_y + 0.5, box.width, box.height);
  }
  overlayContext.restore();
}

function drawSelectedRelationship(components) {
  if (!state.selectedRelationship) {
    return;
  }

  const selectedIds = new Set([
    state.selectedRelationship.component_a_id,
    state.selectedRelationship.component_b_id,
  ]);
  const selectedComponents = components.filter((component) => selectedIds.has(component.component_id));

  overlayContext.save();
  overlayContext.imageSmoothingEnabled = false;
  overlayContext.lineWidth = 2;
  for (const component of selectedComponents) {
    const box = component.bounding_box;
    overlayContext.strokeStyle = "#ffffff";
    overlayContext.strokeRect(box.min_x + 0.5, box.min_y + 0.5, box.width, box.height);
    overlayContext.strokeStyle = componentColor(component.component_id, 1);
    overlayContext.strokeRect(
      box.min_x + 1.5,
      box.min_y + 1.5,
      Math.max(0, box.width - 2),
      Math.max(0, box.height - 2),
    );
  }

  if (selectedComponents.length === 2) {
    const [first, second] = selectedComponents;
    overlayContext.strokeStyle = "#ffffff";
    overlayContext.lineWidth = 1;
    overlayContext.beginPath();
    overlayContext.moveTo(first.centroid.x + 0.5, first.centroid.y + 0.5);
    overlayContext.lineTo(second.centroid.x + 0.5, second.centroid.y + 0.5);
    overlayContext.stroke();
  }
  overlayContext.restore();
}

function hslToRgb(hue, saturation, lightness) {
  const chroma = (1 - Math.abs(2 * lightness - 1)) * saturation;
  const scaledHue = hue / 60;
  const x = chroma * (1 - Math.abs((scaledHue % 2) - 1));
  let red = 0;
  let green = 0;
  let blue = 0;

  if (scaledHue >= 0 && scaledHue < 1) {
    red = chroma;
    green = x;
  } else if (scaledHue < 2) {
    red = x;
    green = chroma;
  } else if (scaledHue < 3) {
    green = chroma;
    blue = x;
  } else if (scaledHue < 4) {
    green = x;
    blue = chroma;
  } else if (scaledHue < 5) {
    red = x;
    blue = chroma;
  } else {
    red = chroma;
    blue = x;
  }

  const match = lightness - chroma / 2;
  return [
    Math.round((red + match) * 255),
    Math.round((green + match) * 255),
    Math.round((blue + match) * 255),
  ];
}

function renderRelationshipReview(frame) {
  const allRelationships = frame.relationships || [];
  const maxDistance = Number(relationshipDistanceInput.value);
  const limit = Number(relationshipLimitInput.value);
  const componentFilter = relationshipComponentInput.value === ""
    ? null
    : Number(relationshipComponentInput.value);

  const filtered = allRelationships
    .filter((relationship) => relationship.edge_distance <= maxDistance)
    .filter((relationship) => (
      componentFilter === null
      || relationship.component_a_id === componentFilter
      || relationship.component_b_id === componentFilter
    ))
    .sort((left, right) => left.edge_distance - right.edge_distance)
    .slice(0, limit);

  relationshipSummary.textContent =
    `${filtered.length} shown of ${allRelationships.length} relationships `
    + `(max distance ${maxDistance}, limit ${limit})`;

  relationshipList.innerHTML = "";
  for (const relationship of filtered) {
    const item = document.createElement("div");
    item.className = "relationshipItem";
    if (isSelectedRelationship(relationship)) {
      item.classList.add("selected");
    }
    item.tabIndex = 0;
    item.addEventListener("click", () => selectRelationship(relationship));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRelationship(relationship);
      }
    });

    const pair = document.createElement("div");
    pair.className = "relationshipPair";
    pair.textContent = `${relationship.component_a_id} ↔ ${relationship.component_b_id}`;

    const details = document.createElement("div");
    details.className = "relationshipDetails";
    details.textContent = relationshipSummaryText(relationship);

    item.append(pair, details);
    relationshipList.append(item);
  }
}

function selectRelationship(relationship) {
  state.selectedRelationship = relationship;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderRelationshipReview(state.currentFrame);
  }
}

function isSelectedRelationship(relationship) {
  return state.selectedRelationship
    && relationship.component_a_id === state.selectedRelationship.component_a_id
    && relationship.component_b_id === state.selectedRelationship.component_b_id;
}

function relationshipSummaryText(relationship) {
  const orientation = relationshipOrientation(relationship);
  return [
    orientation,
    `gap x=${relationship.horizontal_gap} y=${relationship.vertical_gap}`,
    `edge=${formatNumber(relationship.edge_distance)}`,
    `centroid=${formatNumber(relationship.centroid_distance)}`,
    `overlap x=${relationship.x_overlap} y=${relationship.y_overlap}`,
    `ratio area=${formatNumber(relationship.area_ratio)}`,
    `align top=${relationship.top_delta} bottom=${relationship.bottom_delta}`,
    `touch=${relationship.touches}`,
    `contains=${relationship.contains}`,
  ].join(" | ");
}

function relationshipOrientation(relationship) {
  if (relationship.touches) {
    return "touching boxes";
  }
  if (relationship.horizontal_gap > 0 && relationship.vertical_gap === 0) {
    return relationship.horizontal_gap <= 3 ? "near horizontal" : "horizontally aligned";
  }
  if (relationship.vertical_gap > 0 && relationship.horizontal_gap === 0) {
    return relationship.vertical_gap <= 3 ? "near vertical" : "vertically aligned";
  }
  return relationship.edge_distance <= 3 ? "near diagonal" : "diagonal/far";
}

function formatNumber(value) {
  return Number(value).toFixed(2).replace(/\.00$/, "");
}

function setError(message) {
  errorMessage.textContent = message;
}

function stopPlayback() {
  state.playing = false;
  playButton.textContent = "Play";
  if (state.timer !== null) {
    clearTimeout(state.timer);
    state.timer = null;
  }
}

function startPlayback() {
  if (!state.dataset || state.frameCount === 0) {
    return;
  }
  state.playing = true;
  playButton.textContent = "Pause";
  schedulePlaybackStep();
}

function schedulePlaybackStep() {
  if (!state.playing) {
    return;
  }
  if (state.timer !== null) {
    clearTimeout(state.timer);
  }
  state.timer = setTimeout(() => {
    state.timer = null;
    playbackStep();
  }, 120);
}

async function playbackStep() {
  if (!state.playing) {
    return;
  }
  const next = state.frameNumber + 1 >= state.frameCount ? 0 : state.frameNumber + 1;
  try {
    await loadFrame(next);
  } catch (error) {
    stopPlayback();
    setError(error.message);
    return;
  }
  schedulePlaybackStep();
}

async function guarded(action) {
  try {
    setError("");
    await action();
  } catch (error) {
    stopPlayback();
    setError(error.message);
  }
}

loadButton.addEventListener("click", () => guarded(loadDataset));
previousButton.addEventListener("click", () => {
  stopPlayback();
  guarded(() => loadFrame(state.frameNumber - 1));
});
nextButton.addEventListener("click", () => {
  stopPlayback();
  guarded(() => loadFrame(state.frameNumber + 1));
});
jumpButton.addEventListener("click", () => {
  stopPlayback();
  guarded(() => loadFrame(Number(frameInput.value)));
});
modeSelect.addEventListener("change", () => {
  state.mode = modeSelect.value;
  guarded(() => loadFrame(state.frameNumber));
});
componentOverlaySelect.addEventListener("change", () => {
  state.componentOverlay = componentOverlaySelect.value;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
  }
});
candidateOverlaySelect.addEventListener("change", () => {
  state.candidateOverlay = candidateOverlaySelect.value;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
  }
});
relationshipDistanceInput.addEventListener("input", () => {
  if (state.currentFrame) {
    renderRelationshipReview(state.currentFrame);
  }
});
relationshipLimitInput.addEventListener("input", () => {
  if (state.currentFrame) {
    renderRelationshipReview(state.currentFrame);
  }
});
relationshipComponentInput.addEventListener("input", () => {
  if (state.currentFrame) {
    renderRelationshipReview(state.currentFrame);
  }
});
playButton.addEventListener("click", () => {
  if (state.playing) {
    stopPlayback();
  } else {
    startPlayback();
  }
});

guarded(loadDatasets);
