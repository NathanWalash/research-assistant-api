import {
  apiRequest,
  appendActions,
  bootstrapPage,
  createResultItem,
  encodePathSegment,
  formatDate,
  formatNumber,
  getSessionUser,
  populateSelect,
  renderEmpty,
  setButtonPending,
  setStatus,
  toErrorMessage,
  updateQueryParams,
} from "/app/static/shared.js";

const SEARCH_LIMIT = 12;

const state = {
  selectedPaper: null,
  projects: [],
  searchResults: [],
  search: {
    query: "",
    topic: "",
    year: "",
    citationCount: "0",
    offset: 0,
    hasMore: false,
  },
};

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  const searchForm = document.querySelector("#search-form");
  const clearButton = document.querySelector("#clear-search");
  const previousButton = document.querySelector("#search-prev");
  const nextButton = document.querySelector("#search-next");
  const selectedPaperViewButton = document.querySelector("#open-selected-paper");
  const paperModal = document.querySelector("#paper-detail-modal");
  const paperModalCloseButton = document.querySelector("#paper-modal-close");
  const workspaceModal = document.querySelector("#workspace-action-modal");
  const workspaceModalCloseButton = document.querySelector("#workspace-modal-close");
  const saveForm = document.querySelector("#save-to-project-form");
  const annotationForm = document.querySelector("#annotation-form");
  const annotationCancelButton = document.querySelector("#annotation-cancel");
  const citationPathForm = document.querySelector("#citation-path-form");

  const { user } = await bootstrapPage();
  hydrateSearchStateFromUrl();
  applySearchStateToInputs();
  await loadSearchFilters();
  initializeDiscoveryPanels();

  if (user) {
    await loadProjects();
  }

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    state.search.offset = 0;
    await runSearch({ autoSelectFirst: false });
  });

  clearButton.addEventListener("click", async () => {
    searchForm.reset();
    state.search = {
      query: "",
      topic: "",
      year: "",
      citationCount: "0",
      offset: 0,
      hasMore: false,
    };
    state.searchResults = [];
    await runSearch({ autoSelectFirst: false });
  });

  previousButton?.addEventListener("click", async () => {
    if (state.search.offset <= 0) {
      return;
    }
    state.search.offset = Math.max(state.search.offset - SEARCH_LIMIT, 0);
    await runSearch();
  });

  nextButton?.addEventListener("click", async () => {
    if (!state.search.hasMore) {
      return;
    }
    state.search.offset += SEARCH_LIMIT;
    await runSearch();
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
      const submitButton = saveForm.querySelector('button[type="submit"]');

      try {
        setButtonPending(submitButton, true, "Adding...");
        await apiRequest(`/projects/${projectId}/reading-list`, {
          method: "POST",
          auth: true,
          body: {
            paper_id: state.selectedPaper.id,
            priority: document.querySelector("#save-priority").value,
            notes: null,
          },
        });
        saveForm.reset();
        setStatus(statusElement, "Paper added to the selected project.", "success");
      } catch (error) {
        setStatus(statusElement, toErrorMessage(error), "error");
      } finally {
        setButtonPending(submitButton, false);
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
      const submitButton = annotationForm.querySelector("#annotation-submit");

      try {
        setButtonPending(
          submitButton,
          true,
          annotationId ? "Updating..." : "Saving...",
        );
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
        setStatus(statusElement, toErrorMessage(error), "error");
      } finally {
        setButtonPending(submitButton, false);
      }
    });
  }

  annotationCancelButton?.addEventListener("click", () => {
    resetAnnotationEditor();
  });

  selectedPaperViewButton?.addEventListener("click", async () => {
    await openPaperDetailModal();
  });

  paperModalCloseButton?.addEventListener("click", () => {
    closePaperDetailModal();
  });

  paperModal?.addEventListener("click", (event) => {
    if (event.target === paperModal) {
      closePaperDetailModal();
    }
  });

  workspaceModalCloseButton?.addEventListener("click", () => {
    closeWorkspaceActionModal();
  });

  workspaceModal?.addEventListener("click", (event) => {
    if (event.target === workspaceModal) {
      closeWorkspaceActionModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closePaperDetailModal();
      closeWorkspaceActionModal();
    }
  });

  citationPathForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadCitationPath(statusElement);
  });

  const requestedPaper = new URLSearchParams(window.location.search).get("paper");
  if (requestedPaper) {
    await loadPaperDetail(requestedPaper);
  }
  await runSearch({ autoSelectFirst: false });
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

async function loadSearchFilters() {
  try {
    const [topics, trends] = await Promise.all([
      apiRequest("/topics?limit=50"),
      apiRequest("/analytics/trends?start_year=2018"),
    ]);
    const years = [...new Set(trends.map((item) => String(item.publication_year)))].sort(
      (left, right) => Number(right) - Number(left),
    );

    populateSelect(
      document.querySelector("#search-topic"),
      [{ value: "", label: "Any topic" }].concat(
        topics.map((topic) => ({ value: topic.name, label: topic.name })),
      ),
    );
    populateSelect(
      document.querySelector("#search-year"),
      [{ value: "", label: "Any year" }].concat(
        years.map((year) => ({ value: year, label: year })),
      ),
    );
    applySearchStateToInputs();
  } catch {
    populateSelect(document.querySelector("#search-topic"), [
      { value: "", label: "Any topic" },
    ]);
    populateSelect(document.querySelector("#search-year"), [
      { value: "", label: "Any year" },
    ]);
  }
}

async function runSearch({ autoSelectFirst = false } = {}) {
  const resultsContainer = document.querySelector("#search-results");
  const summaryElement = document.querySelector("#search-summary");
  syncSearchStateFromInputs();
  const params = new URLSearchParams();

  if (state.search.query) {
    params.set("query", state.search.query);
  }
  if (state.search.topic) {
    params.set("topic", state.search.topic);
  }
  if (state.search.year) {
    params.set("year", state.search.year);
  }
  if (state.search.citationCount) {
    params.set("citation_count", state.search.citationCount);
  }
  params.set("limit", String(SEARCH_LIMIT));
  params.set("offset", String(state.search.offset));

  try {
    const papers = await apiRequest(`/papers/search?${params.toString()}`);
    state.searchResults = papers;
    state.search.hasMore = papers.length === SEARCH_LIMIT;

    if (!papers.length) {
      renderEmpty(resultsContainer, "No papers matched the current filters.");
      summaryElement.textContent = "No results for the current filters.";
      updateSearchPager();
      syncUrlState();
      return;
    }

    if (
      autoSelectFirst &&
      (!state.selectedPaper || !papers.some((paper) => paper.id === state.selectedPaper.id))
    ) {
      await loadPaperDetail(papers[0].id);
    }

    summaryElement.textContent = `Showing ${papers.length} result(s), offset ${state.search.offset}.`;
    renderSearchResults();
    updateSearchPager();
    syncUrlState();
  } catch (error) {
    renderEmpty(resultsContainer, toErrorMessage(error));
    summaryElement.textContent = "Search failed.";
    updateSearchPager();
  }
}

async function loadPaperDetail(paperId) {
  const titleElement = document.querySelector("#paper-title");
  const metaContainer = document.querySelector("#paper-meta");
  const abstractPanel = document.querySelector("#paper-abstract-panel");
  const abstractContainer = document.querySelector("#paper-abstract");
  const abstractEmptyElement = document.querySelector("#paper-abstract-empty");
  const authorsContainer = document.querySelector("#paper-authors");

  try {
    const paper = await apiRequest(`/papers/${encodePathSegment(paperId)}`);
    state.selectedPaper = paper;
    updateSelectedPaperSummary();
    updateWorkspaceModalSummary();
    titleElement.textContent = paper.title;

    metaContainer.replaceChildren(
      createMetaCard("Paper ID", paper.id),
      createMetaCard("Topic", paper.topic?.name ?? "No topic"),
      createMetaCard("Published", formatDate(paper.publication_date)),
      createMetaCard("Citations", formatNumber(paper.citation_count)),
      createMetaCard("Year", String(paper.publication_year)),
      createMetaCard("Journal", paper.journal ?? "Not available"),
    );

    const abstractText =
      typeof paper.abstract === "string" ? paper.abstract.trim() : "";
    if (abstractText) {
      abstractPanel.classList.remove("hidden");
      abstractPanel.open = false;
      abstractContainer.textContent = abstractText;
      abstractContainer.classList.remove("empty-state");
      abstractEmptyElement.classList.add("hidden");
    } else {
      abstractPanel.classList.add("hidden");
      abstractContainer.textContent = "";
      abstractEmptyElement.textContent = "No abstract is available for this paper.";
      abstractEmptyElement.classList.remove("hidden");
    }

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
    renderSearchResults();
    renderEmpty(
      document.querySelector("#citation-path-results"),
      "Enter a target paper id and run path finding.",
    );
    syncUrlState();
    await Promise.all([loadSimilarPapers(paper.id), loadCitations(paper.id)]);
  } catch (error) {
    state.selectedPaper = null;
    updateSelectedPaperSummary();
    updateWorkspaceModalSummary();
    titleElement.textContent = "Paper lookup failed";
    abstractPanel.classList.add("hidden");
    abstractContainer.textContent = "";
    abstractEmptyElement.textContent = toErrorMessage(error);
    abstractEmptyElement.classList.remove("hidden");
    renderEmpty(authorsContainer, "Paper detail is unavailable.");
    syncUrlState();
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
          meta: [
            `${paper.publication_year}`,
            `${formatNumber(paper.citation_count)} citations`,
            `Similarity ${paper.similarity_score.toFixed(3)}`,
          ],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, toErrorMessage(error));
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
    renderEmpty(container, toErrorMessage(error));
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
    renderEmpty(container, toErrorMessage(error));
  }
}

async function loadCitationPath(statusElement) {
  const container = document.querySelector("#citation-path-results");
  if (!state.selectedPaper) {
    renderEmpty(container, "Select a source paper before finding a path.");
    return;
  }

  const targetPaperId = document.querySelector("#citation-target-paper").value.trim();
  if (!targetPaperId) {
    renderEmpty(container, "Enter a target paper id.");
    return;
  }

  const maxDepth = document.querySelector("#citation-max-depth").value;
  const submitButton = document
    .querySelector("#citation-path-form")
    .querySelector('button[type="submit"]');

  try {
    setButtonPending(submitButton, true, "Finding...");
    const pathData = await apiRequest(
      `/papers/${encodePathSegment(state.selectedPaper.id)}/path/${encodePathSegment(
        targetPaperId,
      )}?max_depth=${encodeURIComponent(maxDepth)}`,
    );
    if (!pathData.path.length) {
      renderEmpty(container, "No path data returned.");
      return;
    }
    container.replaceChildren(
      ...pathData.path.map((paper, index) =>
        createResultItem({
          title: `${index === 0 ? "Source" : `Step ${index}`}: ${paper.title}`,
          href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
          badges: [
            index === pathData.path.length - 1 ? "Target" : "Intermediate",
          ],
          meta: [
            paper.id,
            `${paper.publication_year}`,
            `${formatNumber(paper.citation_count)} citations`,
          ],
        }),
      ),
    );
    setStatus(
      statusElement,
      `Citation path loaded (${pathData.path_length} hop${pathData.path_length === 1 ? "" : "s"}).`,
      "success",
    );
  } catch (error) {
    const message = toErrorMessage(error);
    renderEmpty(container, message);
    setStatus(statusElement, message, "error");
  } finally {
    setButtonPending(submitButton, false);
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

function renderSearchResults() {
  const resultsContainer = document.querySelector("#search-results");
  const canOpenWorkspace = Boolean(getSessionUser());
  if (!state.searchResults.length) {
    renderEmpty(resultsContainer, "No papers matched the current filters.");
    return;
  }
  resultsContainer.replaceChildren(
    ...state.searchResults.map((paper) => {
      const item = createResultItem({
        title: paper.title,
        href: null,
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
          label: "Select",
          onClick: async () => {
            await loadPaperDetail(paper.id);
          },
        },
        {
          label: "View",
          tone: "primary",
          onClick: async () => {
            await openPaperDetailModal(paper.id);
          },
        },
        {
          label: "Workspace",
          tone: "secondary",
          disabled: !canOpenWorkspace,
          title: canOpenWorkspace
            ? "Save this paper or add private notes."
            : "Sign in to use workspace actions.",
          onClick: async () => {
            await openWorkspaceActionModal(paper.id);
          },
        },
      ]);
      return item;
    }),
  );
}

function updateSearchPager() {
  const previousButton = document.querySelector("#search-prev");
  const nextButton = document.querySelector("#search-next");
  const pageElement = document.querySelector("#search-page");
  const pageNumber = Math.floor(state.search.offset / SEARCH_LIMIT) + 1;
  previousButton.disabled = state.search.offset <= 0;
  nextButton.disabled = !state.search.hasMore;
  pageElement.textContent = `Page ${pageNumber}`;
}

function syncSearchStateFromInputs() {
  state.search.query = document.querySelector("#search-query").value.trim();
  state.search.topic = document.querySelector("#search-topic").value.trim();
  state.search.year = document.querySelector("#search-year").value.trim();
  state.search.citationCount = document
    .querySelector("#search-citation-count")
    .value.trim();
}

function hydrateSearchStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  state.search.query = params.get("query") ?? "";
  state.search.topic = params.get("topic") ?? "";
  state.search.year = params.get("year") ?? "";
  state.search.citationCount = params.get("citation_count") ?? "0";
  const offsetValue = params.get("offset") ?? "0";
  const parsedOffset = Number.parseInt(offsetValue, 10);
  state.search.offset = Number.isFinite(parsedOffset) && parsedOffset >= 0 ? parsedOffset : 0;
}

function applySearchStateToInputs() {
  document.querySelector("#search-query").value = state.search.query;
  document.querySelector("#search-topic").value = state.search.topic;
  document.querySelector("#search-year").value = state.search.year;
  document.querySelector("#search-citation-count").value = state.search.citationCount;
}

function syncUrlState() {
  updateQueryParams({
    query: state.search.query || null,
    topic: state.search.topic || null,
    year: state.search.year || null,
    citation_count: state.search.citationCount || null,
    offset: state.search.offset ? state.search.offset : null,
    paper: state.selectedPaper?.id ?? null,
  });
}

function initializeDiscoveryPanels() {
  updateSelectedPaperSummary();
  updateWorkspaceModalSummary();
  renderEmpty(
    document.querySelector("#similar-results"),
    "Select a paper to load embedding-based similar papers.",
  );
  renderEmpty(
    document.querySelector("#citation-results"),
    "Select a paper to load citation neighbours.",
  );
  renderEmpty(
    document.querySelector("#citation-path-results"),
    "Select a source paper before finding a path.",
  );
  renderEmpty(
    document.querySelector("#paper-authors"),
    "Select and view a paper to inspect authorship metadata.",
  );
  const annotationMessage = getSessionUser()
    ? "Select a paper to view annotations."
    : "Sign in to manage annotations.";
  renderEmpty(document.querySelector("#annotation-results"), annotationMessage);
}

function updateSelectedPaperSummary() {
  const summaryElement = document.querySelector("#selected-paper-active");
  const viewButton = document.querySelector("#open-selected-paper");
  if (!summaryElement || !viewButton) {
    return;
  }

  if (!state.selectedPaper) {
    summaryElement.textContent = "Select a paper from the search results to populate this section.";
    viewButton.classList.add("hidden");
    return;
  }

  const year = state.selectedPaper.publication_year ?? "N/A";
  summaryElement.textContent = `Selected: ${state.selectedPaper.title} (${year}).`;
  viewButton.classList.remove("hidden");
}

async function openPaperDetailModal(paperId = null) {
  if (paperId) {
    await loadPaperDetail(paperId);
  }
  if (!state.selectedPaper) {
    return;
  }

  const modal = document.querySelector("#paper-detail-modal");
  if (!modal) {
    return;
  }
  modal.classList.remove("hidden");
  document.body.classList.add("modal-open");
}

function closePaperDetailModal() {
  const modal = document.querySelector("#paper-detail-modal");
  if (!modal || modal.classList.contains("hidden")) {
    return;
  }
  modal.classList.add("hidden");
  document.body.classList.remove("modal-open");
}

async function openWorkspaceActionModal(paperId = null) {
  if (!getSessionUser()) {
    return;
  }
  if (paperId) {
    await loadPaperDetail(paperId);
  }
  if (!state.selectedPaper) {
    return;
  }

  const modal = document.querySelector("#workspace-action-modal");
  if (!modal) {
    return;
  }
  updateWorkspaceModalSummary();
  modal.classList.remove("hidden");
  document.body.classList.add("modal-open");
}

function closeWorkspaceActionModal() {
  const modal = document.querySelector("#workspace-action-modal");
  if (!modal || modal.classList.contains("hidden")) {
    return;
  }
  modal.classList.add("hidden");
  document.body.classList.remove("modal-open");
}

function updateWorkspaceModalSummary() {
  const summaryElement = document.querySelector("#workspace-modal-paper");
  if (!summaryElement) {
    return;
  }

  if (!state.selectedPaper) {
    summaryElement.textContent = "No paper selected.";
    return;
  }

  const year = state.selectedPaper.publication_year ?? "N/A";
  summaryElement.textContent = `${state.selectedPaper.title} (${year})`;
}
