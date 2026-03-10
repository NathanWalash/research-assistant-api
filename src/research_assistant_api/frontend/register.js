import {
  apiRequest,
  bootstrapPage,
  saveSession,
  setButtonPending,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const form = document.querySelector("#register-form");
  const statusElement = document.querySelector("#auth-status");

  await bootstrapPage({ redirectAuthenticatedTo: "/app/projects" });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector('button[type="submit"]');

    const payload = {
      email: document.querySelector("#register-email").value.trim(),
      password: document.querySelector("#register-password").value,
    };

    try {
      setButtonPending(submitButton, true, "Creating...");
      const tokenResponse = await apiRequest("/auth/register", {
        method: "POST",
        body: payload,
      });
      saveSession(tokenResponse);
      setStatus(statusElement, "Account created. Redirecting to projects.", "success");
      window.location.assign("/app/projects");
    } catch (error) {
      setStatus(statusElement, toErrorMessage(error), "error");
    } finally {
      setButtonPending(submitButton, false);
    }
  });
});
