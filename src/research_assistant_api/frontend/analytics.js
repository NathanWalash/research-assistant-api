import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatNumber,
  renderEmpty,
  setStatus,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  await bootstrapPage();

  document
    .querySelector("#top-papers-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await loadTopPapers();
    });

  document
    .querySelector("#topics-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await loadTopics();
    });

  document
    .querySelector("#trends-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await loadTrends();
    });

  document
    .querySelector("#collaborations-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      await loadCollaborations();
    });

  document
    .querySelector("#refresh-all")
    .addEventListener("click", async () => {
      await refreshAll(statusElement);
    });

  await refreshAll(statusElement);
});

async function refreshAll(statusElement) {
  try {
    await Promise.all([
      loadTopPapers(),
      loadTopics(),
      loadTrends(),
      loadCollaborations(),
    ]);
    setStatus(statusElement, "Analytics refreshed.", "success");
  } catch (error) {
    setStatus(statusElement, error.message, "error");
  }
}

async function loadTopPapers() {
  const container = document.querySelector("#top-papers-results");
  const params = new URLSearchParams({ limit: "8" });
  const topic = document.querySelector("#top-papers-topic").value.trim();
  const year = document.querySelector("#top-papers-year").value.trim();
  if (topic) {
    params.set("topic", topic);
  }
  if (year) {
    params.set("year", year);
  }

  const papers = await apiRequest(`/analytics/top-papers?${params.toString()}`);
  if (!papers.length) {
    renderEmpty(container, "No top-paper results for the current filters.");
    return;
  }
  container.replaceChildren(
    ...papers.map((paper) =>
      createResultItem({
        title: paper.title,
        href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
        badges: [paper.topic?.name ?? "No topic"],
        meta: [
          `${paper.publication_year}`,
          `${formatNumber(paper.citation_count)} citations`,
          paper.journal ?? "No journal",
        ],
      }),
    ),
  );
}

async function loadTopics() {
  const container = document.querySelector("#topics-results");
  const params = new URLSearchParams({ limit: "8" });
  const year = document.querySelector("#topics-year").value.trim();
  if (year) {
    params.set("year", year);
  }

  const topics = await apiRequest(`/analytics/topics?${params.toString()}`);
  if (!topics.length) {
    renderEmpty(container, "No topic analytics for the current filters.");
    return;
  }
  container.replaceChildren(
    ...topics.map((topic) =>
      createResultItem({
        title: topic.name,
        description: topic.field ?? "Field not available.",
        badges: [`${formatNumber(topic.paper_count)} papers`],
        meta: [
          `${formatNumber(topic.total_citation_count)} citations`,
          `${topic.average_citation_count.toFixed(1)} avg citations`,
        ],
      }),
    ),
  );
}

async function loadTrends() {
  const container = document.querySelector("#trends-results");
  const params = new URLSearchParams();
  const startYear = document.querySelector("#trends-start-year").value.trim();
  const endYear = document.querySelector("#trends-end-year").value.trim();
  if (startYear) {
    params.set("start_year", startYear);
  }
  if (endYear) {
    params.set("end_year", endYear);
  }

  const trends = await apiRequest(`/analytics/trends?${params.toString()}`);
  if (!trends.length) {
    renderEmpty(container, "No publication trends are available for the current filters.");
    return;
  }
  container.replaceChildren(
    ...trends.map((trend) =>
      createResultItem({
        title: `${trend.publication_year}`,
        badges: [`${formatNumber(trend.paper_count)} papers`],
        meta: [
          `${formatNumber(trend.total_citation_count)} citations`,
          `${trend.average_citation_count.toFixed(1)} avg citations`,
        ],
      }),
    ),
  );
}

async function loadCollaborations() {
  const container = document.querySelector("#collaborations-results");
  const params = new URLSearchParams({ limit: "8" });
  const minSharedPapers = document
    .querySelector("#collaborations-min-shared")
    .value.trim();
  if (minSharedPapers) {
    params.set("min_shared_papers", minSharedPapers);
  }

  const collaborations = await apiRequest(
    `/analytics/collaborations?${params.toString()}`,
  );
  if (!collaborations.length) {
    renderEmpty(container, "No co-authorship pairs match the current threshold.");
    return;
  }
  container.replaceChildren(
    ...collaborations.map((pair) =>
      createResultItem({
        title: `${pair.author_a_name} + ${pair.author_b_name}`,
        badges: [`${formatNumber(pair.shared_paper_count)} shared papers`],
        meta: [pair.author_a_id, pair.author_b_id],
      }),
    ),
  );
}
