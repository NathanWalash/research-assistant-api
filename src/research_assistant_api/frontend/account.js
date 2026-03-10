import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatDate,
  formatDateTime,
  getAccessTokenExpiry,
  formatNumber,
  renderEmpty,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const { user } = await bootstrapPage();

  renderAccountSummary(user);
  await loadHealthSummary(statusElement);

  if (!user) {
    return;
  }

  try {
    const projects = await apiRequest("/projects", { auth: true });
    const container = document.querySelector("#account-projects");
    renderProjectMetrics(projects);
    if (!projects.length) {
      renderEmpty(container, "You have not created any projects yet.");
      return;
    }
    container.replaceChildren(
      ...projects.map((project) =>
        createResultItem({
          title: project.title,
          description: project.description ?? "No description set.",
          href: `/app/projects?project=${encodeURIComponent(project.id)}`,
          meta: [formatDate(project.created_at)],
        }),
      ),
    );
    setStatus(statusElement, "Account summary loaded.", "success");
  } catch (error) {
    const message = toErrorMessage(error);
    renderEmpty(document.querySelector("#account-projects"), message);
    setStatus(statusElement, message, "error");
  }
});

function renderAccountSummary(user) {
  document.querySelector("[data-account-email]").textContent = user?.email ?? "Guest";
  document.querySelector("[data-account-status]").textContent = user
    ? "Authenticated"
    : "Signed out";
  document.querySelector("[data-account-created]").textContent = user
    ? formatDate(user.created_at)
    : "Not available";
  const tokenExpiry = getAccessTokenExpiry();
  document.querySelector("[data-account-token-expiry]").textContent = tokenExpiry
    ? formatDateTime(tokenExpiry.toISOString())
    : "Not available";
}

async function loadHealthSummary(statusElement) {
  try {
    const health = await apiRequest("/health");
    document.querySelector("[data-account-health]").textContent =
      health.status ?? "Unavailable";
    document.querySelector("[data-account-environment]").textContent =
      health.environment ?? "Unavailable";
  } catch (error) {
    document.querySelector("[data-account-health]").textContent = "Unavailable";
    document.querySelector("[data-account-environment]").textContent = "Unavailable";
    setStatus(statusElement, toErrorMessage(error), "error");
  }
}

function renderProjectMetrics(projects) {
  document.querySelector("[data-project-count]").textContent = formatNumber(projects.length);
  if (!projects.length) {
    document.querySelector("[data-project-latest]").textContent = "Not available";
    return;
  }
  const latest = projects
    .map((project) => new Date(project.created_at))
    .filter((value) => !Number.isNaN(value.getTime()))
    .sort((left, right) => right.getTime() - left.getTime())[0];
  document.querySelector("[data-project-latest]").textContent = latest
    ? formatDate(latest.toISOString())
    : "Not available";
}
