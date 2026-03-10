import {
  apiRequest,
  bootstrapPage,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

const METHOD_ORDER = ["GET", "POST", "PATCH", "PUT", "DELETE"];
const TAG_ORDER = [
  "meta",
  "health",
  "auth",
  "papers",
  "authors",
  "topics",
  "analytics",
  "projects",
  "reading-list",
  "annotations",
];
const TAG_LABELS = {
  meta: "Meta",
  health: "Health",
  auth: "Authentication",
  papers: "Paper Discovery",
  authors: "Author Discovery",
  topics: "Topic Discovery",
  analytics: "Corpus Analytics",
  projects: "Projects and Reading Lists (Authenticated)",
  "reading-list": "Reading List Items (Authenticated)",
  annotations: "Annotations (Authenticated)",
};

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#endpoints-status");
  const tableBody = document.querySelector("#api-endpoint-body");

  await bootstrapPage();

  try {
    const schema = await apiRequest("/openapi.json");
    const endpoints = extractEndpoints(schema);
    renderEndpoints(tableBody, endpoints);
    setStatus(
      statusElement,
      `Loaded ${endpoints.length} API endpoints from the backend schema.`,
      "success",
    );
  } catch (error) {
    tableBody.replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.textContent = "Unable to load endpoint inventory.";
    row.append(cell);
    tableBody.append(row);
    setStatus(statusElement, toErrorMessage(error), "error");
  }
});

function extractEndpoints(schema) {
  const endpoints = [];
  const paths = schema?.paths ?? {};

  Object.entries(paths).forEach(([path, operations]) => {
    Object.entries(operations).forEach(([method, operation]) => {
      const methodName = method.toUpperCase();
      if (!METHOD_ORDER.includes(methodName)) {
        return;
      }

      const tag = Array.isArray(operation?.tags) && operation.tags.length
        ? operation.tags[0]
        : "meta";
      const description =
        cleanText(operation?.description) ||
        cleanText(operation?.summary) ||
        "No description available.";
      const authenticated =
        Array.isArray(operation?.security) && operation.security.length > 0;

      endpoints.push({
        tag,
        method: methodName,
        path,
        auth: authenticated ? "Yes" : "No",
        description,
      });
    });
  });

  return endpoints.sort((left, right) => {
    const tagOrder =
      tagIndex(left.tag) - tagIndex(right.tag);
    if (tagOrder !== 0) {
      return tagOrder;
    }
    if (left.path !== right.path) {
      return left.path.localeCompare(right.path);
    }
    return METHOD_ORDER.indexOf(left.method) - METHOD_ORDER.indexOf(right.method);
  });
}

function renderEndpoints(tableBody, endpoints) {
  tableBody.replaceChildren();
  const fragment = document.createDocumentFragment();

  let currentTag = null;
  endpoints.forEach((endpoint) => {
    if (endpoint.tag !== currentTag) {
      currentTag = endpoint.tag;
      fragment.append(buildCategoryRow(TAG_LABELS[currentTag] ?? currentTag));
    }
    fragment.append(buildEndpointRow(endpoint));
  });

  tableBody.append(fragment);
}

function buildCategoryRow(label) {
  const row = document.createElement("tr");
  row.className = "api-category-row";
  const cell = document.createElement("td");
  cell.colSpan = 4;
  cell.textContent = label;
  row.append(cell);
  return row;
}

function buildEndpointRow(endpoint) {
  const row = document.createElement("tr");
  row.dataset.method = endpoint.method;
  row.dataset.endpoint = endpoint.path;

  const methodCell = document.createElement("td");
  const methodBadge = document.createElement("span");
  methodBadge.className = `pill method-pill ${endpoint.method.toLowerCase()}`;
  methodBadge.textContent = endpoint.method;
  methodCell.append(methodBadge);

  const endpointCell = document.createElement("td");
  const endpointCode = document.createElement("code");
  endpointCode.textContent = endpoint.path;
  endpointCell.append(endpointCode);

  const authCell = document.createElement("td");
  authCell.textContent = endpoint.auth;

  const descriptionCell = document.createElement("td");
  descriptionCell.textContent = endpoint.description;

  row.append(methodCell, endpointCell, authCell, descriptionCell);
  return row;
}

function cleanText(value) {
  if (typeof value !== "string") {
    return "";
  }
  return value.replace(/\s+/g, " ").trim();
}

function tagIndex(tag) {
  const index = TAG_ORDER.indexOf(tag);
  return index === -1 ? TAG_ORDER.length + 1 : index;
}
