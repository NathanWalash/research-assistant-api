import {
  apiRequest,
  appendActions,
  bootstrapPage,
  createResultItem,
  formatNumber,
  getQueryParam,
  renderEmpty,
  setStatus,
} from "/app/static/shared.js";

const state = {
  projects: [],
  selectedProject: null,
  selectedReadingItem: null,
};

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const userContext = await bootstrapPage();
  const suggestedPaperId = getQueryParam("paper");

  if (suggestedPaperId) {
    document.querySelector("#reading-paper-id").value = suggestedPaperId;
  }

  wireProjectForm(statusElement);
  wireProjectUpdateForm(statusElement);
  wireReadingListCreateForm(statusElement);
  wireReadingListUpdateForm(statusElement);
  wireRecommendationForm(statusElement);

  if (!userContext.user) {
    return;
  }

  await loadProjects();
  const requestedProjectId = getQueryParam("project");
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
      try {
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
        setStatus(statusElement, error.message, "error");
      }
    });
}

function wireProjectUpdateForm(statusElement) {
  document
    .querySelector("#project-update-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedProject) {
        setStatus(statusElement, "Select a project first.", "error");
        return;
      }

      try {
        await apiRequest(`/projects/${state.selectedProject.id}`, {
          method: "PATCH",
          auth: true,
          body: {
            title: document.querySelector("#selected-project-title-input").value.trim(),
            description:
              document.querySelector("#selected-project-description-input").value.trim() ||
              null,
          },
        });
        await loadProjects();
        const updated = state.projects.find(
          (project) => project.id === state.selectedProject.id,
        );
        if (updated) {
          await selectProject(updated);
        }
        setStatus(statusElement, "Project updated.", "success");
      } catch (error) {
        setStatus(statusElement, error.message, "error");
      }
    });

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
      } catch (error) {
        setStatus(statusElement, error.message, "error");
      }
    });
}

function wireReadingListCreateForm(statusElement) {
  document
    .querySelector("#reading-list-create-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedProject) {
        setStatus(statusElement, "Select a project first.", "error");
        return;
      }
      try {
        await apiRequest(`/projects/${state.selectedProject.id}/reading-list`, {
          method: "POST",
          auth: true,
          body: {
            paper_id: document.querySelector("#reading-paper-id").value.trim(),
            priority: document.querySelector("#reading-priority").value,
            notes: document.querySelector("#reading-notes").value.trim() || null,
          },
        });
        document.querySelector("#reading-list-create-form").reset();
        document.querySelector("#reading-priority").value = "medium";
        await loadReadingList();
        setStatus(statusElement, "Reading-list item added.", "success");
      } catch (error) {
        setStatus(statusElement, error.message, "error");
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
        setStatus(statusElement, error.message, "error");
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
        setStatus(statusElement, error.message, "error");
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
      params.set("mode", document.querySelector("#recommendation-mode").value);
      params.set("limit", "10");

      const semanticWeight = document.querySelector("#semantic-weight").value;
      const citationWeight = document.querySelector("#citation-weight").value;
      if (semanticWeight !== "") {
        params.set("semantic_weight", semanticWeight);
      }
      if (citationWeight !== "") {
        params.set("citation_weight", citationWeight);
      }

      try {
        const recommendations = await apiRequest(
          `/projects/${state.selectedProject.id}/recommendations?${params.toString()}`,
          { auth: true },
        );
        renderRecommendations(recommendations);
        setStatus(statusElement, "Recommendations updated.", "success");
      } catch (error) {
        renderEmpty(document.querySelector("#recommendation-results"), error.message);
        setStatus(statusElement, error.message, "error");
      }
    });
}

async function loadProjects() {
  state.projects = await apiRequest("/projects", { auth: true });
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
        meta: [formatDateTime(project.created_at)],
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
  document.querySelector("#selected-project-id").value = state.selectedProject.id;
  document.querySelector("#selected-project-title").textContent = state.selectedProject.title;
  document.querySelector("#selected-project-title-input").value =
    state.selectedProject.title;
  document.querySelector("#selected-project-description-input").value =
    state.selectedProject.description ?? "";
  await loadProjects();
  await loadReadingList();
  renderEmpty(
    document.querySelector("#recommendation-results"),
    "Choose a recommendation mode and run scoring.",
  );
}

async function loadReadingList() {
  const container = document.querySelector("#reading-list-results");
  if (!state.selectedProject) {
    renderEmpty(container, "Select a project first.");
    return;
  }

  const items = await apiRequest(
    `/projects/${state.selectedProject.id}/reading-list`,
    { auth: true },
  );
  document.querySelector("#selected-project-count").textContent = `${items.length} items`;

  if (!items.length) {
    state.selectedReadingItem = null;
    clearReadingItemEditor();
    renderEmpty(container, "Add a paper to start the reading list.");
    return;
  }

  if (
    state.selectedReadingItem &&
    !items.some((item) => item.id === state.selectedReadingItem.id)
  ) {
    state.selectedReadingItem = null;
  }

  container.replaceChildren(
    ...items.map((item) => {
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
            void loadReadingList();
          },
        },
      ]);
      return card;
    }),
  );

  if (!state.selectedReadingItem) {
    state.selectedReadingItem = items[0];
    populateReadingItemEditor(items[0]);
    await loadReadingList();
    return;
  }

  const refreshedSelected = items.find((item) => item.id === state.selectedReadingItem.id);
  if (refreshedSelected) {
    state.selectedReadingItem = refreshedSelected;
    populateReadingItemEditor(refreshedSelected);
  }
}

function populateReadingItemEditor(item) {
  document.querySelector("#selected-reading-item-id").value = item.id;
  document.querySelector("#selected-reading-item-title").textContent = item.paper.title;
  document.querySelector("#selected-reading-priority").value = item.priority;
  document.querySelector("#selected-reading-notes").value = item.notes ?? "";
}

function clearReadingItemEditor() {
  document.querySelector("#selected-reading-item-id").value = "";
  document.querySelector("#selected-reading-item-title").textContent =
    "No reading-list item selected";
  document.querySelector("#selected-reading-priority").value = "medium";
  document.querySelector("#selected-reading-notes").value = "";
}

function clearProjectWorkspace() {
  state.selectedProject = null;
  state.selectedReadingItem = null;
  document.querySelector("#selected-project-id").value = "";
  document.querySelector("#selected-project-title").textContent = "No project selected";
  document.querySelector("#selected-project-title-input").value = "";
  document.querySelector("#selected-project-description-input").value = "";
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
        description: `${paper.scoring_mode} score ${paper.recommendation_score.toFixed(3)}`,
        badges: [
          `Semantic ${paper.semantic_score.toFixed(3)}`,
          `Citation ${paper.citation_score.toFixed(3)}`,
        ],
        meta: [
          `${paper.publication_year}`,
          `${formatNumber(paper.citation_count)} citations`,
          paper.topic?.name ?? "No topic",
        ],
      });
      appendActions(item, [
        {
          label: "Use paper ID",
          onClick: () => {
            document.querySelector("#reading-paper-id").value = paper.id;
            document.querySelector("#reading-paper-id").focus();
          },
        },
      ]);
      return item;
    }),
  );
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Created date unavailable";
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
