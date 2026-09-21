const state = {
  dataset: "",
  frameCount: 0,
  frameNumber: 0,
  mode: "exact",
  componentOverlay: "off",
  componentIds: "off",
  candidateOverlay: "off",
  currentFrame: null,
  selectedComponentId: null,
  selectedRelationship: null,
  selectedCandidate: null,
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
const componentIdSelect = document.querySelector("#componentIdSelect");
const candidateOverlaySelect = document.querySelector("#candidateOverlaySelect");
const datasetStatus = document.querySelector("#datasetStatus");
const frameStatus = document.querySelector("#frameStatus");
const headerStatus = document.querySelector("#headerStatus");
const componentStatus = document.querySelector("#componentStatus");
const relationshipStatus = document.querySelector("#relationshipStatus");
const candidateStatus = document.querySelector("#candidateStatus");
const componentLimitInput = document.querySelector("#componentLimitInput");
const componentMinAreaInput = document.querySelector("#componentMinAreaInput");
const componentSummary = document.querySelector("#componentSummary");
const componentList = document.querySelector("#componentList");
const relationshipDistanceInput = document.querySelector("#relationshipDistanceInput");
const relationshipLimitInput = document.querySelector("#relationshipLimitInput");
const relationshipComponentInput = document.querySelector("#relationshipComponentInput");
const relationshipSummary = document.querySelector("#relationshipSummary");
const relationshipList = document.querySelector("#relationshipList");
const candidateLimitInput = document.querySelector("#candidateLimitInput");
const candidateComponentInput = document.querySelector("#candidateComponentInput");
const candidateSummary = document.querySelector("#candidateSummary");
const candidateList = document.querySelector("#candidateList");
const errorMessage = document.querySelector("#errorMessage");
const canvas = document.querySelector("#dmdCanvas");
const context = canvas.getContext("2d");
const overlayCanvas = document.querySelector("#overlayCanvas");
const overlayContext = overlayCanvas.getContext("2d");
const labelOverlay = document.querySelector("#labelOverlay");

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
  state.selectedComponentId = null;
  state.selectedRelationship = null;
  state.selectedCandidate = null;
  state.frameNumber = payload.frame.frame_number;
  frameInput.value = state.frameNumber;
  frameStatus.textContent = `Frame ${state.frameNumber + 1} of ${state.frameCount}`;
  headerStatus.textContent = `Header ${payload.frame.header}`;
  componentStatus.textContent = `${payload.frame.components.length} raw components`;
  relationshipStatus.textContent = `${payload.frame.relationship_count} relationships`;
  candidateStatus.textContent = `${payload.frame.candidate_box_count} candidate boxes`;
  state.currentFrame = payload.frame;
  drawFrame(payload.frame);
  renderComponentReview(payload.frame);
  renderRelationshipReview(payload.frame);
  renderCandidateReview(payload.frame);
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
  labelOverlay.innerHTML = "";
  drawComponentOverlay(frame.components || []);
  drawCandidateOverlay(frame.candidate_boxes || []);
}

function drawComponentOverlay(components) {
  if (state.componentOverlay === "off") {
    drawSelectedComponent(components);
    drawSelectedRelationship(components);
    drawComponentIds(components);
    return;
  }

  if (state.componentOverlay === "pixels" || state.componentOverlay === "both") {
    drawComponentPixels(components);
  }

  if (state.componentOverlay === "boxes" || state.componentOverlay === "both") {
    drawComponentBoxes(components);
  }
  drawSelectedComponent(components);
  drawSelectedRelationship(components);
  drawComponentIds(components);
}

function drawCandidateOverlay(candidates) {
  if (state.candidateOverlay === "off") {
    return;
  }

  const selectedCandidates = filteredCandidates(candidates);

  for (const candidate of selectedCandidates) {
    if (isSelectedCandidate(candidate)) {
      continue;
    }
    addOverlayBox(candidate.bounding_box, "candidateBox");
  }

  drawSelectedCandidate(candidates, state.currentFrame?.components || []);
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
  for (const component of components) {
    addOverlayBox(
      component.bounding_box,
      "componentBox",
      componentColor(component.component_id, 0.95),
    );
  }
}

function drawSelectedComponent(components) {
  if (state.selectedComponentId === null) {
    return;
  }

  const component = components.find((item) => item.component_id === state.selectedComponentId);
  if (!component) {
    return;
  }

  addOverlayBox(
    component.bounding_box,
    "selectedComponentBox",
    componentColor(component.component_id, 1),
  );
}

function drawComponentIds(components) {
  if (state.componentIds === "off") {
    return;
  }

  const labelledComponents = state.componentIds === "selected"
    ? components.filter((component) => component.component_id === state.selectedComponentId)
    : filteredComponents(components);

  for (const component of labelledComponents) {
    const box = component.bounding_box;
    const label = document.createElement("div");
    label.className = "componentLabel";
    label.textContent = component.component_id;
    label.style.left = `${(box.min_x / 128) * 100}%`;
    label.style.top = `${(box.min_y / 32) * 100}%`;
    labelOverlay.append(label);
  }
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

  for (const component of selectedComponents) {
    addOverlayBox(
      component.bounding_box,
      "selectedComponentBox",
      componentColor(component.component_id, 1),
    );
  }

  if (selectedComponents.length === 2) {
    overlayContext.save();
    overlayContext.imageSmoothingEnabled = false;
    const [first, second] = selectedComponents;
    overlayContext.strokeStyle = "#ffffff";
    overlayContext.lineWidth = 1;
    overlayContext.beginPath();
    overlayContext.moveTo(first.centroid.x + 0.5, first.centroid.y + 0.5);
    overlayContext.lineTo(second.centroid.x + 0.5, second.centroid.y + 0.5);
    overlayContext.stroke();
    overlayContext.restore();
  }
}

function drawSelectedCandidate(candidates, components) {
  if (!state.selectedCandidate) {
    return;
  }

  const candidate = candidates.find(isSelectedCandidate);
  if (!candidate) {
    return;
  }

  const selectedIds = new Set(candidate.component_ids);
  const selectedComponents = components.filter((component) => selectedIds.has(component.component_id));

  addOverlayBox(candidate.bounding_box, "selectedCandidateBox");

  for (const component of selectedComponents) {
    addOverlayBox(
      component.bounding_box,
      "componentBox",
      componentColor(component.component_id, 1),
    );
  }
}

function addOverlayBox(box, className, color = "") {
  const element = document.createElement("div");
  element.className = `overlayBox ${className}`;
  element.style.left = `${(box.min_x / 128) * 100}%`;
  element.style.top = `${(box.min_y / 32) * 100}%`;
  element.style.width = `${(box.width / 128) * 100}%`;
  element.style.height = `${(box.height / 32) * 100}%`;
  if (color) {
    element.style.color = color;
  }
  labelOverlay.append(element);
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

function renderComponentReview(frame) {
  const allComponents = frame.components || [];
  const filtered = filteredComponents(allComponents);

  componentSummary.textContent =
    `${filtered.length} shown of ${allComponents.length} components `
    + `(min area ${componentMinArea()}, limit ${componentLimit()})`;

  componentList.innerHTML = "";
  for (const component of filtered) {
    const item = document.createElement("div");
    item.className = "componentItem";
    if (component.component_id === state.selectedComponentId) {
      item.classList.add("selected");
    }
    item.tabIndex = 0;
    item.addEventListener("click", () => selectComponent(component.component_id));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectComponent(component.component_id);
      }
    });

    const pair = document.createElement("div");
    pair.className = "componentPair";
    pair.textContent = `#${component.component_id}`;

    const details = document.createElement("div");
    details.className = "componentDetails";
    details.textContent = componentSummaryText(component);

    item.append(pair, details);
    componentList.append(item);
  }
}

function selectComponent(componentId) {
  state.selectedComponentId = componentId;
  state.selectedRelationship = null;
  state.selectedCandidate = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderComponentReview(state.currentFrame);
    renderRelationshipReview(state.currentFrame);
    renderCandidateReview(state.currentFrame);
  }
}

function filteredComponents(components) {
  return components
    .filter((component) => component.area >= componentMinArea())
    .sort((left, right) => (
      right.area - left.area
      || left.component_id - right.component_id
    ))
    .slice(0, componentLimit());
}

function componentLimit() {
  return Math.max(1, Number(componentLimitInput.value) || 1);
}

function componentMinArea() {
  return Math.max(1, Number(componentMinAreaInput.value) || 1);
}

function componentSummaryText(component) {
  const box = component.bounding_box;
  return [
    `area=${component.area}`,
    `box ${box.width}x${box.height} at ${box.min_x},${box.min_y}`,
    `centroid ${formatNumber(component.centroid.x)},${formatNumber(component.centroid.y)}`,
  ].join(" | ");
}

function selectRelationship(relationship) {
  state.selectedComponentId = null;
  state.selectedRelationship = relationship;
  state.selectedCandidate = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderComponentReview(state.currentFrame);
    renderRelationshipReview(state.currentFrame);
    renderCandidateReview(state.currentFrame);
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

function renderCandidateReview(frame) {
  const allCandidates = frame.candidate_boxes || [];
  const filtered = filteredCandidates(allCandidates);

  candidateSummary.textContent =
    `${filtered.length} shown of ${allCandidates.length} candidates `
    + `(threshold ${candidateThresholdLabel()}, limit ${candidateLimit()})`;

  candidateList.innerHTML = "";
  for (const candidate of filtered) {
    const item = document.createElement("div");
    item.className = "candidateItem";
    if (isSelectedCandidate(candidate)) {
      item.classList.add("selected");
    }
    item.tabIndex = 0;
    item.addEventListener("click", () => selectCandidate(candidate));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectCandidate(candidate);
      }
    });

    const pair = document.createElement("div");
    pair.className = "candidatePair";
    pair.textContent = `C${candidate.candidate_id}`;

    const details = document.createElement("div");
    details.className = "candidateDetails";
    details.textContent = candidateSummaryText(candidate);

    item.append(pair, details);
    candidateList.append(item);
  }
}

function selectCandidate(candidate) {
  state.selectedComponentId = null;
  state.selectedCandidate = candidate;
  state.selectedRelationship = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderComponentReview(state.currentFrame);
    renderCandidateReview(state.currentFrame);
    renderRelationshipReview(state.currentFrame);
  }
}

function isSelectedCandidate(candidate) {
  return state.selectedCandidate
    && candidate.candidate_id === state.selectedCandidate.candidate_id;
}

function filteredCandidates(candidates) {
  const componentFilter = candidateComponentInput.value === ""
    ? null
    : Number(candidateComponentInput.value);

  return candidates
    .filter(candidateThresholdAllows)
    .filter((candidate) => (
      componentFilter === null || candidate.component_ids.includes(componentFilter)
    ))
    .sort((left, right) => (
      left.threshold - right.threshold
      || candidateArea(left) - candidateArea(right)
      || left.candidate_id - right.candidate_id
    ))
    .slice(0, candidateLimit());
}

function candidateThresholdAllows(candidate) {
  if (state.candidateOverlay === "off") {
    return false;
  }
  if (state.candidateOverlay === "all") {
    return true;
  }
  return candidate.threshold <= Number(state.candidateOverlay);
}

function candidateLimit() {
  return Math.max(1, Number(candidateLimitInput.value) || 1);
}

function candidateThresholdLabel() {
  if (state.candidateOverlay === "off") {
    return "off";
  }
  if (state.candidateOverlay === "all") {
    return "all";
  }
  return `<= ${state.candidateOverlay}`;
}

function candidateArea(candidate) {
  return candidate.bounding_box.width * candidate.bounding_box.height;
}

function candidateSummaryText(candidate) {
  const box = candidate.bounding_box;
  const pairs = candidate.evidence_pairs
    .map((pair) => `${pair.component_a_id}<->${pair.component_b_id}`)
    .join(", ");
  return [
    `threshold=${candidate.threshold}`,
    `components ${candidate.component_ids.join("+")}`,
    `box ${box.width}x${box.height} at ${box.min_x},${box.min_y}`,
    `evidence ${pairs}`,
  ].join(" | ");
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
componentIdSelect.addEventListener("change", () => {
  state.componentIds = componentIdSelect.value;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
  }
});
candidateOverlaySelect.addEventListener("change", () => {
  state.candidateOverlay = candidateOverlaySelect.value;
  state.selectedCandidate = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderCandidateReview(state.currentFrame);
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
componentLimitInput.addEventListener("input", () => {
  state.selectedComponentId = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderComponentReview(state.currentFrame);
  }
});
componentMinAreaInput.addEventListener("input", () => {
  state.selectedComponentId = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderComponentReview(state.currentFrame);
  }
});
candidateLimitInput.addEventListener("input", () => {
  state.selectedCandidate = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderCandidateReview(state.currentFrame);
  }
});
candidateComponentInput.addEventListener("input", () => {
  state.selectedCandidate = null;
  if (state.currentFrame) {
    drawAnalysisOverlay(state.currentFrame);
    renderCandidateReview(state.currentFrame);
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
