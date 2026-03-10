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

export function cleanText(value) {
  if (typeof value !== "string") {
    return "";
  }
  return value.replace(/\s+/g, " ").trim();
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
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function getUserDisplayName(email) {
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

export function getAccessTokenExpiry(accessToken) {
  if (!accessToken) {
    return null;
  }
  const parts = accessToken.split(".");
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

export async function apiRequest(
  path,
  { method = "GET", body = null, auth = false, accessToken = null, headers = {} } = {},
) {
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");

  if (body !== null) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    if (!accessToken) {
      throw new ApiError("You need to sign in first.", 401);
    }
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
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
    throw new ApiError(detail, response.status, payload);
  }

  return payload;
}

