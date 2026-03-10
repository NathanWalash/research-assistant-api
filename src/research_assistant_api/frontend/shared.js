const SESSION_STORAGE_KEY = "research-assistant-session";

export class ApiError extends Error {
  constructor(message, status, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function toErrorMessage(error, fallback = "Request failed.") {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function getSession() {
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function saveSession(session) {
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  syncAuthChrome();
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
  syncAuthChrome();
}

export function getSessionUser() {
  return getSession()?.user ?? null;
}

export function getAccessTokenExpiry() {
  const token = getSession()?.access_token;
  if (!token) {
    return null;
  }
  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }
  try {
    const payloadText = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(payloadText);
    if (typeof payload.exp !== "number") {
      return null;
    }
    return new Date(payload.exp * 1000);
  } catch {
    return null;
  }
}

export function encodePathSegment(value) {
  return encodeURIComponent(value);
}

export function setButtonPending(button, pending, pendingLabel = "Working...") {
  if (!button) {
    return;
  }
  if (!button.dataset.defaultLabel) {
    button.dataset.defaultLabel = button.textContent ?? "";
  }
  button.disabled = pending;
  button.textContent = pending ? pendingLabel : button.dataset.defaultLabel;
}

export async function apiRequest(
  path,
  { method = "GET", body = null, auth = false, headers = {} } = {},
) {
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");

  if (body !== null) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    const session = getSession();
    if (!session?.access_token) {
      throw new ApiError("You need to sign in first.", 401);
    }
    requestHeaders.set("Authorization", `Bearer ${session.access_token}`);
  }

  const response = await fetch(path, {
    method,
    headers: requestHeaders,
    body: body === null ? null : JSON.stringify(body),
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? payload.detail
        : `Request failed with status ${response.status}`;
    if (response.status === 401 && auth) {
      clearSession();
    }
    throw new ApiError(detail, response.status, payload);
  }

  return payload;
}

export async function refreshCurrentUser() {
  const session = getSession();
  if (!session?.access_token) {
    syncAuthChrome();
    return null;
  }

  try {
    const user = await apiRequest("/auth/me", { auth: true });
    saveSession({ ...session, user });
    return user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      clearSession();
      return null;
    }
    throw error;
  }
}

export async function bootstrapPage(
  { requireAuth = false, redirectAuthenticatedTo = null } = {},
) {
  markActivePage();
  bindLogoutButtons();
  const user = await refreshCurrentUser();

  if (redirectAuthenticatedTo && user) {
    window.location.assign(redirectAuthenticatedTo);
  }

  if (requireAuth && !user) {
    window.location.assign("/app/login");
  }

  syncAuthChrome();
  return { session: getSession(), user };
}

function markActivePage() {
  const currentPage = document.body.dataset.page;
  document.querySelectorAll("[data-page-link]").forEach((link) => {
    const isActive = link.dataset.pageLink === currentPage;
    link.classList.toggle("active", isActive);
    if (isActive) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

function bindLogoutButtons() {
  document.querySelectorAll("[data-logout-button]").forEach((button) => {
    button.addEventListener("click", () => {
      clearSession();
      window.location.assign("/app");
    });
  });
}

export function syncAuthChrome() {
  const session = getSession();
  const user = session?.user ?? null;
  const authenticated = Boolean(session?.access_token && user);
  const accountLabel = authenticated ? getUserDisplayName(user.email) : "My account";

  document.querySelectorAll("[data-user-summary]").forEach((element) => {
    element.textContent = authenticated ? accountLabel : "Guest mode";
    element.title = authenticated ? user.email : "Not signed in";
  });

  document.querySelectorAll("[data-signin-link]").forEach((element) => {
    element.classList.toggle("hidden", authenticated);
  });

  document.querySelectorAll("[data-register-link]").forEach((element) => {
    element.classList.toggle("hidden", authenticated);
  });

  document.querySelectorAll("[data-account-link]").forEach((element) => {
    element.classList.toggle("hidden", !authenticated);
    element.textContent = accountLabel;
    element.title = authenticated ? `Signed in as ${user.email}` : "My account";
    if (document.body.dataset.page === "account") {
      element.setAttribute("aria-current", "page");
    } else {
      element.removeAttribute("aria-current");
    }
  });

  document.querySelectorAll("[data-logout-button]").forEach((element) => {
    element.classList.toggle("hidden", !authenticated);
  });

  document
    .querySelectorAll('[data-authenticated-only="true"]')
    .forEach((element) => {
      element.classList.toggle("hidden", !authenticated);
    });

  document
    .querySelectorAll('[data-authenticated-only="false"]')
    .forEach((element) => {
      element.classList.toggle("visible", !authenticated);
    });
}

function getUserDisplayName(email) {
  if (typeof email !== "string" || !email.includes("@")) {
    return "My account";
  }
  const localPart = email.split("@")[0].trim();
  if (!localPart) {
    return "My account";
  }
  const words = localPart
    .replace(/[._-]+/g, " ")
    .split(" ")
    .map((word) => word.trim())
    .filter(Boolean);
  if (!words.length) {
    return "My account";
  }
  return words
    .map((word) => `${word[0].toUpperCase()}${word.slice(1).toLowerCase()}`)
    .join(" ");
}

export function setStatus(element, message, tone = "neutral") {
  if (!element) {
    return;
  }
  element.textContent = message;
  if (tone === "neutral") {
    element.removeAttribute("data-tone");
  } else {
    element.dataset.tone = tone;
  }
  element.classList.remove("hidden");
}

export function clearStatus(element) {
  if (!element) {
    return;
  }
  element.textContent = "";
  element.removeAttribute("data-tone");
  element.classList.add("hidden");
}

export function formatDate(value) {
  if (!value) {
    return "Not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
  }).format(date);
}

export function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Not available";
  }
  return new Intl.NumberFormat("en-GB").format(Number(value));
}

export function renderEmpty(container, message) {
  container.replaceChildren();
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.textContent = message;
  container.append(empty);
}

export function createResultItem({
  title,
  href = null,
  description = "",
  meta = [],
  badges = [],
  selected = false,
}) {
  const item = document.createElement("article");
  item.className = "result-item";
  if (selected) {
    item.dataset.selected = "true";
  }

  const heading = document.createElement("h4");
  if (href) {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = title;
    heading.append(link);
  } else {
    heading.textContent = title;
  }
  item.append(heading);

  if (description) {
    const descriptionNode = document.createElement("p");
    descriptionNode.textContent = description;
    item.append(descriptionNode);
  }

  if (badges.length > 0) {
    const badgeRow = document.createElement("div");
    badgeRow.className = "badge-row";
    badges.forEach((badgeText) => {
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = badgeText;
      badgeRow.append(badge);
    });
    item.append(badgeRow);
  }

  if (meta.length > 0) {
    const metaRow = document.createElement("div");
    metaRow.className = "result-meta";
    meta.forEach((metaText) => {
      const metaTag = document.createElement("small");
      metaTag.textContent = metaText;
      metaRow.append(metaTag);
    });
    item.append(metaRow);
  }

  return item;
}

export function appendActions(container, actions) {
  const row = document.createElement("div");
  row.className = "result-actions";
  actions.forEach(
    ({
      label,
      onClick,
      tone = "secondary",
      type = "button",
      disabled = false,
      title = "",
    }) => {
    const button = document.createElement("button");
    button.type = type;
    button.className = `button ${tone} compact`;
    button.textContent = label;
    button.disabled = Boolean(disabled);
    if (title) {
      button.title = title;
    }
    button.addEventListener("click", onClick);
    row.append(button);
    },
  );
  container.append(row);
}

export function populateSelect(select, options, placeholder = "Choose an option") {
  select.replaceChildren();
  if (!options.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.append(option);
    return;
  }

  options.forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry.value;
    option.textContent = entry.label;
    select.append(option);
  });
}

export function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

export function updateQueryParams(values) {
  const params = new URLSearchParams(window.location.search);
  Object.entries(values).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
  });
  const next = params.toString();
  const path = next ? `${window.location.pathname}?${next}` : window.location.pathname;
  window.history.replaceState(null, "", path);
}
