import {
  apiRequest,
  bootstrapPage,
  saveSession,
  setStatus,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const form = document.querySelector("#login-form");
  const statusElement = document.querySelector("#auth-status");

  await bootstrapPage({ redirectAuthenticatedTo: "/app/projects" });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.querySelector("#login-email").value.trim(),
      password: document.querySelector("#login-password").value,
    };

    try {
      const tokenResponse = await apiRequest("/auth/login", {
        method: "POST",
        body: payload,
      });
      saveSession(tokenResponse);
      const user = await apiRequest("/auth/me", { auth: true });
      saveSession({ ...tokenResponse, user });
      setStatus(statusElement, "Signed in. Redirecting to projects.", "success");
      window.location.assign("/app/projects");
    } catch (error) {
      setStatus(statusElement, error.message, "error");
    }
  });
});
