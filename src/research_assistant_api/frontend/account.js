import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatDate,
  renderEmpty,
  setStatus,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const { user } = await bootstrapPage();

  renderAccountSummary(user);

  if (!user) {
    return;
  }

  try {
    const projects = await apiRequest("/projects", { auth: true });
    const container = document.querySelector("#account-projects");
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
    renderEmpty(document.querySelector("#account-projects"), error.message);
    setStatus(statusElement, error.message, "error");
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
}
