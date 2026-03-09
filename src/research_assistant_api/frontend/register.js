import {
  apiRequest,
  bootstrapPage,
  saveSession,
  setStatus,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const form = document.querySelector("#register-form");
  const statusElement = document.querySelector("#auth-status");

  await bootstrapPage({ redirectAuthenticatedTo: "/app/projects" });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.querySelector("#register-email").value.trim(),
      password: document.querySelector("#register-password").value,
    };

    try {
      const tokenResponse = await apiRequest("/auth/register", {
        method: "POST",
        body: payload,
      });
      saveSession(tokenResponse);
      const user = await apiRequest("/auth/me", { auth: true });
      saveSession({ ...tokenResponse, user });
      setStatus(statusElement, "Account created. Redirecting to projects.", "success");
      window.location.assign("/app/projects");
    } catch (error) {
      setStatus(statusElement, error.message, "error");
    }
  });
});
