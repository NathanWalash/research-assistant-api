import {
  apiRequest,
  appendActions,
  bootstrapPage,
  createResultItem,
  encodePathSegment,
  formatDate,
  formatNumber,
  getQueryParam,
  getSessionUser,
  populateSelect,
  renderEmpty,
  setStatus,
} from "/app/static/shared.js";

const state = {
  selectedPaper: null,
  projects: [],
};

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const searchForm = document.querySelector("#search-form");
  const clearButton = document.querySelector("#clear-search");
  const similarButton = document.querySelector("#load-similar");
  const citationsButton = document.querySelector("#load-citations");
  const pathForm = document.querySelector("#citation-path-form");
  const saveForm = document.querySelector("#save-to-project-form");
  const annotationForm = document.querySelector("#annotation-form");
  const annotationCancelButton = document.querySelector("#annotation-cancel");

  const { user } = await bootstrapPage();

  if (user) {
    await loadProjects();
  }

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runSearch();
  });

  clearButton.addEventListener("click", async () => {
    searchForm.reset();
    await runSearch();
  });

  similarButton.addEventListener("click", async () => {
    if (!state.selectedPaper) {
      setStatus(statusElement, "Choose a paper first.", "error");
      return;
    }
    await loadSimilarPapers(state.selectedPaper.id);
  });

  citationsButton.addEventListener("click", async () => {
    if (!state.selectedPaper) {
      setStatus(statusElement, "Choose a paper first.", "error");
      return;
    }
    await loadCitations(state.selectedPaper.id);
  });

  pathForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedPaper) {
      setStatus(statusElement, "Choose a source paper first.", "error");
      return;
    }
    await loadCitationPath();
  });

  if (saveForm) {
    saveForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedPaper) {
        setStatus(statusElement, "Select a paper before saving it to a project.", "error");
        return;
      }
      const projectId = document.querySelector("#save-project-id").value;
      if (!projectId) {
        setStatus(statusElement, "Create or select a project first.", "error");
        return;
      }

      try {
        await apiRequest(`/projects/${projectId}/reading-list`, {
          method: "POST",
          auth: true,
          body: {
            paper_id: state.selectedPaper.id,
            priority: document.querySelector("#save-priority").value,
            notes: document.querySelector("#save-notes").value.trim() || null,
          },
        });
        saveForm.reset();
        document.querySelector("#save-priority").value = "medium";
        setStatus(statusElement, "Paper added to the selected project.", "success");
      } catch (error) {
        setStatus(statusElement, error.message, "error");
      }
    });
  }

  if (annotationForm) {
    annotationForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!state.selectedPaper) {
        setStatus(statusElement, "Choose a paper before saving annotations.", "error");
        return;
      }

      const annotationId = document.querySelector("#annotation-id").value;
      const text = document.querySelector("#annotation-text").value.trim();

      if (!text) {
        setStatus(statusElement, "Annotation text cannot be empty.", "error");
        return;
      }

      try {
        if (annotationId) {
          await apiRequest(`/annotations/${annotationId}`, {
            method: "PATCH",
            auth: true,
            body: { text },
          });
          setStatus(statusElement, "Annotation updated.", "success");
        } else {
          await apiRequest(`/papers/${encodePathSegment(state.selectedPaper.id)}/annotations`, {
            method: "POST",
            auth: true,
            body: { text },
          });
          setStatus(statusElement, "Annotation created.", "success");
        }
        resetAnnotationEditor();
        await loadAnnotations();
      } catch (error) {
        setStatus(statusElement, error.message, "error");
      }
    });
  }

  annotationCancelButton?.addEventListener("click", () => {
    resetAnnotationEditor();
  });

  const requestedPaper = getQueryParam("paper");
  if (requestedPaper) {
    await loadPaperDetail(requestedPaper);
    await runSearch();
  } else {
    await runSearch();
  }
});

async function loadProjects() {
  try {
    state.projects = await apiRequest("/projects", { auth: true });
    populateSelect(
      document.querySelector("#save-project-id"),
      state.projects.map((project) => ({
        value: project.id,
        label: project.title,
      })),
      "Create a project first",
    );
  } catch {
    populateSelect(document.querySelector("#save-project-id"), [], "Projects unavailable");
  }
}

async function runSearch(prefillQuery = null) {
  const resultsContainer = document.querySelector("#search-results");
  const query = prefillQuery ?? document.querySelector("#search-query").value.trim();
  const topic = document.querySelector("#search-topic").value.trim();
  const year = document.querySelector("#search-year").value.trim();
  const citationCount = document.querySelector("#search-citations").value.trim();
  const params = new URLSearchParams();

  if (query) {
    params.set("query", query);
  }
  if (topic) {
    params.set("topic", topic);
  }
  if (year) {
    params.set("year", year);
  }
  if (citationCount) {
    params.set("citation_count", citationCount);
  }
  params.set("limit", "12");

  try {
    const papers = await apiRequest(`/papers/search?${params.toString()}`);
    if (!papers.length) {
      renderEmpty(resultsContainer, "No papers matched the current filters.");
      return;
    }

    resultsContainer.replaceChildren(
      ...papers.map((paper) => {
        const item = createResultItem({
          title: paper.title,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          selected: state.selectedPaper?.id === paper.id,
          badges: [paper.topic?.name ?? "No topic"],
          meta: [
            `${paper.publication_year}`,
            `${formatNumber(paper.citation_count)} citations`,
            paper.journal ?? "No journal",
          ],
        });
        appendActions(item, [
          {
            label: "Inspect",
            onClick: async () => {
              await loadPaperDetail(paper.id);
              await runSearch();
              await loadSimilarPapers(paper.id);
              await loadCitations(paper.id);
            },
          },
        ]);
        return item;
      }),
    );
  } catch (error) {
    renderEmpty(resultsContainer, error.message);
  }
}

async function loadPaperDetail(paperId) {
  const titleElement = document.querySelector("#paper-title");
  const topicPill = document.querySelector("#paper-topic-pill");
  const metaContainer = document.querySelector("#paper-meta");
  const abstractContainer = document.querySelector("#paper-abstract");
  const authorsContainer = document.querySelector("#paper-authors");

  try {
    const paper = await apiRequest(`/papers/${encodePathSegment(paperId)}`);
    state.selectedPaper = paper;
    window.history.replaceState(
      null,
      "",
      `/app/discover?paper=${encodeURIComponent(paper.id)}`,
    );
    titleElement.textContent = paper.title;
    topicPill.textContent = paper.topic?.name ?? "No topic";
    topicPill.classList.toggle("hidden", !paper.topic?.name);

    metaContainer.replaceChildren(
      createMetaCard("Paper ID", paper.id),
      createMetaCard("Year", String(paper.publication_year)),
      createMetaCard("Citations", formatNumber(paper.citation_count)),
      createMetaCard("Journal", paper.journal ?? "Not available"),
      createMetaCard("DOI", paper.doi ?? "Not available"),
      createMetaCard("Language", paper.language ?? "Not available"),
    );

    abstractContainer.classList.toggle("empty-state", !paper.abstract);
    abstractContainer.textContent = paper.abstract ?? "No abstract is available for this paper.";

    if (!paper.authors.length) {
      renderEmpty(authorsContainer, "No authorship metadata is available.");
    } else {
      authorsContainer.replaceChildren(
        ...paper.authors.map((author) =>
          createResultItem({
            title: author.name,
            description: author.institution?.name ?? "Institution not available",
            meta: [
              author.orcid ?? "No ORCID",
              author.is_corresponding ? "Corresponding author" : "Contributing author",
            ],
          }),
        ),
      );
    }

    if (getSessionUser()) {
      await loadAnnotations();
    } else {
      renderEmpty(document.querySelector("#annotation-results"), "Sign in to manage annotations.");
    }
  } catch (error) {
    titleElement.textContent = "Paper lookup failed";
    abstractContainer.textContent = error.message;
    abstractContainer.classList.add("empty-state");
  }
}

async function loadSimilarPapers(paperId) {
  const container = document.querySelector("#similar-results");
  try {
    const papers = await apiRequest(
      `/papers/${encodePathSegment(paperId)}/similar?limit=6`,
    );
    if (!papers.length) {
      renderEmpty(container, "No similar papers are available.");
      return;
    }
    container.replaceChildren(
      ...papers.map((paper) =>
        createResultItem({
          title: paper.title,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          badges: [`Similarity ${paper.similarity_score.toFixed(3)}`],
          meta: [
            `${paper.publication_year}`,
            `${formatNumber(paper.citation_count)} citations`,
          ],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, error.message);
  }
}

async function loadCitations(paperId) {
  const container = document.querySelector("#citation-results");
  try {
    const citationData = await apiRequest(
      `/papers/${encodePathSegment(paperId)}/citations?limit=5`,
    );
    const items = [];
    citationData.cited_papers.forEach((paper) => {
      items.push(
        createResultItem({
          title: `Cites: ${paper.title}`,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          meta: [`${paper.publication_year}`, `${formatNumber(paper.citation_count)} citations`],
        }),
      );
    });
    citationData.citing_papers.forEach((paper) => {
      items.push(
        createResultItem({
          title: `Cited by: ${paper.title}`,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          meta: [`${paper.publication_year}`, `${formatNumber(paper.citation_count)} citations`],
        }),
      );
    });

    if (!items.length) {
      renderEmpty(container, "No local citation neighbours are available for this paper.");
      return;
    }
    container.replaceChildren(...items);
  } catch (error) {
    renderEmpty(container, error.message);
  }
}

async function loadCitationPath() {
  const container = document.querySelector("#citation-path-results");
  const targetId = document.querySelector("#citation-target-id").value.trim();
  const maxDepth = document.querySelector("#citation-max-depth").value || "6";

  if (!targetId) {
    renderEmpty(container, "Enter a target paper ID to search for a path.");
    return;
  }

  try {
    const pathData = await apiRequest(
      `/papers/${encodePathSegment(state.selectedPaper.id)}/path/${encodePathSegment(targetId)}?max_depth=${maxDepth}`,
    );
    container.replaceChildren(
      ...pathData.path.map((paper, index) =>
        createResultItem({
          title: `${index + 1}. ${paper.title}`,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          badges: [index === 0 ? "Source" : index === pathData.path.length - 1 ? "Target" : "Bridge"],
          meta: [`${paper.publication_year}`, `${formatNumber(paper.citation_count)} citations`],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, error.message);
  }
}

async function loadAnnotations() {
  const container = document.querySelector("#annotation-results");
  if (!state.selectedPaper) {
    renderEmpty(container, "Choose a paper to view annotations.");
    return;
  }

  try {
    const annotations = await apiRequest(
      `/papers/${encodePathSegment(state.selectedPaper.id)}/annotations`,
      { auth: true },
    );
    if (!annotations.length) {
      renderEmpty(container, "No annotations saved for this paper yet.");
      return;
    }
    container.replaceChildren(
      ...annotations.map((annotation) => {
        const item = createResultItem({
          title: `Saved ${formatDate(annotation.created_at)}`,
          description: annotation.text,
        });
        appendActions(item, [
          {
            label: "Edit",
            onClick: () => {
              document.querySelector("#annotation-id").value = annotation.id;
              document.querySelector("#annotation-text").value = annotation.text;
              document.querySelector("#annotation-submit").textContent = "Update annotation";
              document.querySelector("#annotation-cancel").classList.remove("hidden");
            },
          },
          {
            label: "Delete",
            tone: "ghost",
            onClick: async () => {
              await apiRequest(`/annotations/${annotation.id}`, {
                method: "DELETE",
                auth: true,
              });
              resetAnnotationEditor();
              await loadAnnotations();
            },
          },
        ]);
        return item;
      }),
    );
  } catch (error) {
    renderEmpty(container, error.message);
  }
}

function resetAnnotationEditor() {
  document.querySelector("#annotation-id").value = "";
  document.querySelector("#annotation-text").value = "";
  document.querySelector("#annotation-submit").textContent = "Save annotation";
  document.querySelector("#annotation-cancel").classList.add("hidden");
}

function createMetaCard(label, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "meta-card";
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  description.textContent = value;
  wrapper.append(term, description);
  return wrapper;
}
