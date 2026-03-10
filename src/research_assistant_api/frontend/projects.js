import {
  apiRequest,
  appendActions,
  bootstrapPage,
  createResultItem,
  formatDateTime,
  formatNumber,
  renderEmpty,
  setButtonPending,
  setStatus,
  toErrorMessage,
  updateQueryParams,
} from "/app/static/shared.js";

const state = {
  projects: [],
  selectedProject: null,
  readingItems: [],
  selectedReadingItem: null,
};

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const { user } = await bootstrapPage();

  wireProjectForm(statusElement);
  wireProjectUpdateForm(statusElement);
  wireProjectActions(statusElement);
  wireReadingListUpdateForm(statusElement);
  wireRecommendationForm(statusElement);
  wireRecommendationMode();
  syncRecommendationMode();

  if (!user) {
    return;
  }

  await loadProjects();
  const requestedProjectId = new URLSearchParams(window.location.search).get("project");
  if (requestedProjectId) {
    const requestedProject = state.projects.find((project) => project.id === requestedProjectId);
    if (requestedProject) {
      await selectProject(requestedProject);
      return;
    }
  }

  if (state.projects.length) {
    await selectProject(state.projects[0]);
  } else {
    renderEmpty(document.querySelector("#project-list"), "Create your first project to start the workflow.");
  }
});

function wireProjectForm(statusElement) {
  document
    .querySelector("#project-create-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = document
        .querySelector("#project-create-form")
        .querySelector('button[type="submit"]');
      try {
        setButtonPending(submitButton, true, "Creating...");
        const project = await apiRequest("/projects", {
          method: "POST",
          auth: true,
          body: {
            title: document.querySelector("#project-title").value.trim(),
            description:
              document.querySelector("#project-description").value.trim() || null,
          },
        });
        document.querySelector("#project-create-form").reset();
        await loadProjects();
        await selectProject(project);
        setStatus(statusElement, "Project created.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      } finally {
        setButtonPending(submitButton, false);
      }
    });
}

function wireProjectUpdateForm(statusElement) {
  document
    .querySelector("#project-update-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedProject) {
        setStatus(statusElement, "Select a project before updating it.", "error");
        return;
      }

      const title = document.querySelector("#selected-project-title-input").value.trim();
      const description = document
        .querySelector("#selected-project-description-input")
        .value.trim();
      if (!title) {
        setStatus(statusElement, "Project title cannot be empty.", "error");
        return;
      }
      const submitButton = document
        .querySelector("#project-update-form")
        .querySelector('button[type="submit"]');

      try {
        setButtonPending(submitButton, true, "Saving...");
        await apiRequest(`/projects/${state.selectedProject.id}`, {
          method: "PATCH",
          auth: true,
          body: {
            title,
            description: description || null,
          },
        });
        await loadProjects();
        await selectProject(state.selectedProject.id);
        setStatus(statusElement, "Project details updated.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      } finally {
        setButtonPending(submitButton, false);
      }
    });
}

function wireProjectActions(statusElement) {
  document
    .querySelector("#delete-project-button")
    .addEventListener("click", async () => {
      if (!state.selectedProject) {
        return;
      }
      if (!window.confirm("Delete the selected project and all its workflow records?")) {
        return;
      }
      try {
        await apiRequest(`/projects/${state.selectedProject.id}`, {
          method: "DELETE",
          auth: true,
        });
        await loadProjects();
        if (state.projects.length) {
          await selectProject(state.projects[0]);
        } else {
          clearProjectWorkspace();
          renderEmpty(
            document.querySelector("#project-list"),
            "Create a project to start the workflow.",
          );
        }
        setStatus(statusElement, "Project deleted.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      }
    });
}

function wireReadingListUpdateForm(statusElement) {
  document
    .querySelector("#reading-list-update-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedReadingItem) {
        setStatus(statusElement, "Select a reading-list item first.", "error");
        return;
      }
      try {
        await apiRequest(`/reading-list-items/${state.selectedReadingItem.id}`, {
          method: "PATCH",
          auth: true,
          body: {
            priority: document.querySelector("#selected-reading-priority").value,
            notes:
              document.querySelector("#selected-reading-notes").value.trim() || null,
          },
        });
        await loadReadingList();
        setStatus(statusElement, "Reading-list item updated.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      }
    });

  document
    .querySelector("#delete-reading-item-button")
    .addEventListener("click", async () => {
      if (!state.selectedReadingItem) {
        return;
      }
      try {
        await apiRequest(`/reading-list-items/${state.selectedReadingItem.id}`, {
          method: "DELETE",
          auth: true,
        });
        await loadReadingList();
        setStatus(statusElement, "Reading-list item deleted.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      }
    });
}

function wireRecommendationForm(statusElement) {
  document
    .querySelector("#recommendation-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedProject) {
        setStatus(statusElement, "Select a project before requesting recommendations.", "error");
        return;
      }

      const params = new URLSearchParams();
      const mode = document.querySelector("#recommendation-mode").value;
      params.set("mode", mode);
      params.set("limit", "10");
      params.set(
        "semantic_weight",
        document.querySelector("#recommendation-semantic-weight").value,
      );
      params.set(
        "citation_weight",
        document.querySelector("#recommendation-citation-weight").value,
      );
      const submitButton = document
        .querySelector("#recommendation-form")
        .querySelector('button[type="submit"]');

      try {
        setButtonPending(submitButton, true, "Scoring...");
        const recommendations = await apiRequest(
          `/projects/${state.selectedProject.id}/recommendations?${params.toString()}`,
          { auth: true },
        );
        renderRecommendations(recommendations);
        setStatus(statusElement, "Recommendations updated.", "success");
      } catch (error) {
        const message = toErrorMessage(error);
        renderEmpty(document.querySelector("#recommendation-results"), message);
        setStatus(statusElement, message, "error");
      } finally {
        setButtonPending(submitButton, false);
      }
    });
}

async function loadProjects() {
  state.projects = await apiRequest("/projects", { auth: true });
  renderProjectList();
}

function renderProjectList() {
  const projectList = document.querySelector("#project-list");
  if (!state.projects.length) {
    renderEmpty(projectList, "Create your first project to start the workflow.");
    return;
  }

  projectList.replaceChildren(
    ...state.projects.map((project) => {
      const item = createResultItem({
        title: project.title,
        description: project.description ?? "No description set.",
        selected: state.selectedProject?.id === project.id,
        meta: [`Created ${formatDateTime(project.created_at)}`],
      });
      appendActions(item, [
        {
          label: "Open",
          onClick: async () => {
            await selectProject(project);
          },
        },
      ]);
      return item;
    }),
  );
}

async function selectProject(project) {
  const projectId = typeof project === "string" ? project : project.id;
  state.selectedProject = await apiRequest(`/projects/${projectId}`, { auth: true });
  updateQueryParams({ project: state.selectedProject.id });
  renderProjectSummary();
  renderProjectList();
  await loadReadingList();
  renderEmpty(
    document.querySelector("#recommendation-results"),
    "Choose a recommendation mode and run scoring.",
  );
}

function renderProjectSummary() {
  if (!state.selectedProject) {
    clearProjectWorkspace();
    return;
  }

  document.querySelector("#selected-project-id").value = state.selectedProject.id;
  document.querySelector("#selected-project-title-heading").textContent =
    state.selectedProject.title;
  document.querySelector("#selected-project-title-input").value =
    state.selectedProject.title;
  document.querySelector("#selected-project-description-input").value =
    state.selectedProject.description ?? "";
  document.querySelector("#selected-project-meta").textContent = `Created ${formatDateTime(
    state.selectedProject.created_at,
  )}`;
  document.querySelector("#project-discover-link").href = "/app/discover";
}

async function loadReadingList() {
  const container = document.querySelector("#reading-list-results");
  if (!state.selectedProject) {
    renderEmpty(container, "Select a project first.");
    return;
  }

  state.readingItems = await apiRequest(
    `/projects/${state.selectedProject.id}/reading-list`,
    { auth: true },
  );
  document.querySelector("#selected-project-count").textContent = `${state.readingItems.length} items`;

  if (!state.readingItems.length) {
    state.selectedReadingItem = null;
    clearReadingItemEditor();
    renderEmpty(container, "Add a paper to start the reading list.");
    return;
  }

  if (
    state.selectedReadingItem &&
    !state.readingItems.some((item) => item.id === state.selectedReadingItem.id)
  ) {
    state.selectedReadingItem = null;
  }

  if (!state.selectedReadingItem) {
    state.selectedReadingItem = state.readingItems[0];
  }
  const refreshedSelected = state.readingItems.find(
    (item) => item.id === state.selectedReadingItem.id,
  );
  if (refreshedSelected) {
    state.selectedReadingItem = refreshedSelected;
    populateReadingItemEditor(refreshedSelected);
  }
  renderReadingList();
}

function renderReadingList() {
  const container = document.querySelector("#reading-list-results");
  if (!state.readingItems.length) {
    return;
  }
  container.replaceChildren(
    ...state.readingItems.map((item) => {
      const card = createResultItem({
        title: item.paper.title,
        href: `/app/discover?paper=${encodeURIComponent(item.paper.id)}`,
        selected: state.selectedReadingItem?.id === item.id,
        badges: [item.priority.toUpperCase()],
        description: item.notes ?? "No notes yet.",
        meta: [
          item.paper.publication_year.toString(),
          `${formatNumber(item.paper.citation_count)} citations`,
        ],
      });
      appendActions(card, [
        {
          label: "Edit",
          onClick: () => {
            state.selectedReadingItem = item;
            populateReadingItemEditor(item);
            renderReadingList();
          },
        },
      ]);
      return card;
    }),
  );
}

function populateReadingItemEditor(item) {
  document.querySelector("#selected-reading-item-id").value = item.id;
  document.querySelector("#selected-reading-item-title").textContent = item.paper.title;
  document.querySelector("#selected-reading-priority").value = item.priority;
  document.querySelector("#selected-reading-notes").value = item.notes ?? "";
  const link = document.querySelector("#selected-reading-item-link");
  link.href = `/app/discover?paper=${encodeURIComponent(item.paper.id)}`;
  link.classList.remove("hidden");
}

function clearReadingItemEditor() {
  document.querySelector("#selected-reading-item-id").value = "";
  document.querySelector("#selected-reading-item-title").textContent =
    "No reading-list item selected";
  document.querySelector("#selected-reading-priority").value = "medium";
  document.querySelector("#selected-reading-notes").value = "";
  document.querySelector("#selected-reading-item-link").classList.add("hidden");
}

function clearProjectWorkspace() {
  state.selectedProject = null;
  state.readingItems = [];
  state.selectedReadingItem = null;
  document.querySelector("#selected-project-id").value = "";
  document.querySelector("#selected-project-title-heading").textContent = "No project selected";
  document.querySelector("#selected-project-title-input").value = "";
  document.querySelector("#selected-project-description-input").value = "";
  document.querySelector("#selected-project-meta").textContent = "No project selected.";
  document.querySelector("#selected-project-count").textContent = "0 items";
  clearReadingItemEditor();
  renderEmpty(document.querySelector("#reading-list-results"), "Select a project first.");
  renderEmpty(
    document.querySelector("#recommendation-results"),
    "Select a project before running recommendations.",
  );
}

function renderRecommendations(recommendations) {
  const container = document.querySelector("#recommendation-results");
  if (!recommendations.length) {
    renderEmpty(container, "No recommendations are available for the current context.");
    return;
  }

  container.replaceChildren(
    ...recommendations.map((paper) => {
      const item = createResultItem({
        title: paper.title,
        href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
        description:
          `${paper.scoring_mode} recommendation. ` +
          `Semantic ${paper.semantic_score.toFixed(3)}, citation ${paper.citation_score.toFixed(3)}.`,
        badges: [`Score ${paper.recommendation_score.toFixed(3)}`],
        meta: [
          `${paper.publication_year}`,
          `${formatNumber(paper.citation_count)} citations`,
          paper.topic?.name ?? "No topic",
          `wS=${paper.semantic_weight.toFixed(2)} wC=${paper.citation_weight.toFixed(2)}`,
        ],
      });
      appendActions(item, [
        {
          label: "Open paper",
          onClick: () => {
            window.location.assign(`/app/discover?paper=${encodeURIComponent(paper.id)}`);
          },
        },
      ]);
      return item;
    }),
  );
}

function wireRecommendationMode() {
  document
    .querySelector("#recommendation-mode")
    .addEventListener("change", () => {
      syncRecommendationMode();
    });
}

function syncRecommendationMode() {
  const mode = document.querySelector("#recommendation-mode").value;
  const semanticInput = document.querySelector("#recommendation-semantic-weight");
  const citationInput = document.querySelector("#recommendation-citation-weight");
  const note = document.querySelector("#recommendation-weight-note");

  if (mode === "semantic") {
    semanticInput.value = "1";
    citationInput.value = "0";
    semanticInput.disabled = true;
    citationInput.disabled = true;
    note.textContent = "Semantic mode ignores citation score.";
    return;
  }
  if (mode === "citation") {
    semanticInput.value = "0";
    citationInput.value = "1";
    semanticInput.disabled = true;
    citationInput.disabled = true;
    note.textContent = "Citation mode ignores semantic similarity.";
    return;
  }
  semanticInput.disabled = false;
  citationInput.disabled = false;
  if (!semanticInput.value) {
    semanticInput.value = "0.7";
  }
  if (!citationInput.value) {
    citationInput.value = "0.3";
  }
  note.textContent = "Hybrid mode uses both signals. Weights are normalized server-side.";
}
