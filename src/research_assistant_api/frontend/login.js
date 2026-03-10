import {
  apiRequest,
  bootstrapPage,
  saveSession,
  setButtonPending,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const form = document.querySelector("#login-form");
  const statusElement = document.querySelector("#auth-status");

  await bootstrapPage({ redirectAuthenticatedTo: "/app/projects" });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector('button[type="submit"]');

    const payload = {
      email: document.querySelector("#login-email").value.trim(),
      password: document.querySelector("#login-password").value,
    };

    try {
      setButtonPending(submitButton, true, "Signing in...");
      const tokenResponse = await apiRequest("/auth/login", {
        method: "POST",
        body: payload,
      });
      saveSession(tokenResponse);
      setStatus(statusElement, "Signed in. Redirecting to projects.", "success");
      window.location.assign("/app/projects");
    } catch (error) {
      setStatus(statusElement, toErrorMessage(error), "error");
    } finally {
      setButtonPending(submitButton, false);
    }
  });
});
