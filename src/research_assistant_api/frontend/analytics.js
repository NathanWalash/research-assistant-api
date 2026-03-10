import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatNumber,
  populateSelect,
  renderEmpty,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#page-status");
  await bootstrapPage();
  await loadAnalyticsFilters();

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
  setStatus(statusElement, "Refreshing analytics...", "neutral");
  const results = await Promise.allSettled([
    loadSummary(),
    loadTopPapers(),
    loadTopics(),
    loadTrends(),
    loadCollaborations(),
  ]);
  const failed = results.filter((result) => result.status === "rejected");
  if (!failed.length) {
    setStatus(statusElement, "Analytics updated.", "success");
    return;
  }
  const firstFailure = failed[0];
  const message =
    firstFailure.status === "rejected"
      ? toErrorMessage(firstFailure.reason)
      : "Analytics refresh failed.";
  setStatus(statusElement, message, "error");
}

async function loadAnalyticsFilters() {
  try {
    const [topics, trends] = await Promise.all([
      apiRequest("/topics?limit=50"),
      apiRequest("/analytics/trends?start_year=2018"),
    ]);
    const years = [...new Set(trends.map((item) => String(item.publication_year)))].sort(
      (left, right) => Number(right) - Number(left),
    );
    const topicOptions = [{ value: "", label: "All topics" }].concat(
      topics.map((topic) => ({ value: topic.name, label: topic.name })),
    );
    const yearOptions = [{ value: "", label: "All years" }].concat(
      years.map((year) => ({ value: year, label: year })),
    );
    const rangedYearOptions = [{ value: "", label: "Any" }].concat(
      years.map((year) => ({ value: year, label: year })),
    );

    populateSelect(document.querySelector("#top-papers-topic"), topicOptions);
    populateSelect(document.querySelector("#top-papers-year"), yearOptions);
    populateSelect(document.querySelector("#topics-year"), yearOptions);
    populateSelect(document.querySelector("#trends-start-year"), rangedYearOptions);
    populateSelect(document.querySelector("#trends-end-year"), rangedYearOptions);
  } catch {
    populateSelect(document.querySelector("#top-papers-topic"), [
      { value: "", label: "All topics" },
    ]);
    populateSelect(document.querySelector("#top-papers-year"), [
      { value: "", label: "All years" },
    ]);
    populateSelect(document.querySelector("#topics-year"), [
      { value: "", label: "All years" },
    ]);
    populateSelect(document.querySelector("#trends-start-year"), [
      { value: "", label: "Any" },
    ]);
    populateSelect(document.querySelector("#trends-end-year"), [
      { value: "", label: "Any" },
    ]);
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

  try {
    const papers = await apiRequest(`/analytics/top-papers?${params.toString()}`);
    if (!papers.length) {
      renderEmpty(container, "No papers match the current filters.");
      return;
    }
    container.replaceChildren(
      ...papers.map((paper, index) =>
        createResultItem({
          title: `${index + 1}. ${paper.title}`,
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
  } catch (error) {
    renderEmpty(container, toErrorMessage(error));
    throw error;
  }
}

async function loadTopics() {
  const container = document.querySelector("#topics-results");
  const params = new URLSearchParams({ limit: "8" });
  const year = document.querySelector("#topics-year").value.trim();
  if (year) {
    params.set("year", year);
  }

  try {
    const topics = await apiRequest(`/analytics/topics?${params.toString()}`);
    if (!topics.length) {
      renderEmpty(container, "No topic data is available for the current filters.");
      return;
    }
    const maxPaperCount = Math.max(...topics.map((topic) => topic.paper_count), 1);
    container.replaceChildren(
      ...topics.map((topic) =>
        createBarItem({
          title: topic.name,
          valueLabel: `${formatNumber(topic.paper_count)} papers`,
          ratio: topic.paper_count / maxPaperCount,
          meta: [
            topic.field ?? "Field not available",
            `${formatNumber(topic.total_citation_count)} citations`,
            `${topic.average_citation_count.toFixed(1)} avg citations`,
          ],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, toErrorMessage(error));
    throw error;
  }
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

  try {
    const trends = await apiRequest(`/analytics/trends?${params.toString()}`);
    if (!trends.length) {
      renderEmpty(container, "No yearly trend data is available for the current filters.");
      return;
    }
    const maxPapers = Math.max(...trends.map((trend) => trend.paper_count), 1);
    container.replaceChildren(
      ...trends.map((trend) =>
        createBarItem({
          title: `${trend.publication_year}`,
          valueLabel: `${formatNumber(trend.paper_count)} papers`,
          ratio: trend.paper_count / maxPapers,
          meta: [
            `${formatNumber(trend.total_citation_count)} citations`,
            `${trend.average_citation_count.toFixed(1)} avg citations`,
          ],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, toErrorMessage(error));
    throw error;
  }
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

  try {
    const collaborations = await apiRequest(
      `/analytics/collaborations?${params.toString()}`,
    );
    if (!collaborations.length) {
      renderEmpty(container, "No collaboration pairs match the current threshold.");
      return;
    }
    const maxShared = Math.max(
      ...collaborations.map((pair) => pair.shared_paper_count),
      1,
    );
    container.replaceChildren(
      ...collaborations.map((pair) =>
        createBarItem({
          title: `${pair.author_a_name} + ${pair.author_b_name}`,
          valueLabel: `${formatNumber(pair.shared_paper_count)} shared papers`,
          ratio: pair.shared_paper_count / maxShared,
          meta: [pair.author_a_id, pair.author_b_id],
        }),
      ),
    );
  } catch (error) {
    renderEmpty(container, toErrorMessage(error));
    throw error;
  }
}

async function loadSummary() {
  try {
    const [trends, topTopicResult] = await Promise.all([
      apiRequest("/analytics/trends?start_year=2018"),
      apiRequest("/analytics/topics?limit=1"),
    ]);
    const summary = trends.reduce(
      (accumulator, trend) => ({
        totalPapers: accumulator.totalPapers + trend.paper_count,
        totalCitations: accumulator.totalCitations + trend.total_citation_count,
        latestYear: Math.max(accumulator.latestYear, trend.publication_year),
      }),
      {
        totalPapers: 0,
        totalCitations: 0,
        latestYear: 0,
      },
    );
    document.querySelector("#summary-total-papers").textContent = formatNumber(summary.totalPapers);
    document.querySelector("#summary-total-citations").textContent = formatNumber(summary.totalCitations);
    document.querySelector("#summary-latest-year").textContent =
      summary.latestYear > 0 ? String(summary.latestYear) : "Unavailable";
    document.querySelector("#summary-top-topic").textContent =
      topTopicResult[0]?.name ?? "Unavailable";
  } catch {
    document.querySelector("#summary-total-papers").textContent = "Unavailable";
    document.querySelector("#summary-total-citations").textContent = "Unavailable";
    document.querySelector("#summary-latest-year").textContent = "Unavailable";
    document.querySelector("#summary-top-topic").textContent = "Unavailable";
  }
}

function createBarItem({ title, valueLabel, ratio, meta }) {
  const item = document.createElement("article");
  item.className = "result-item bar-item";

  const header = document.createElement("div");
  header.className = "bar-header";

  const titleElement = document.createElement("h4");
  titleElement.textContent = title;
  const valueElement = document.createElement("small");
  valueElement.textContent = valueLabel;
  header.append(titleElement, valueElement);
  item.append(header);

  const track = document.createElement("div");
  track.className = "bar-track";
  const fill = document.createElement("span");
  fill.className = "bar-fill";
  fill.style.width = `${Math.max(0, Math.min(100, Math.round(ratio * 100)))}%`;
  track.append(fill);
  item.append(track);

  if (meta.length) {
    const metaRow = document.createElement("div");
    metaRow.className = "result-meta";
    meta.forEach((entry) => {
      const cell = document.createElement("small");
      cell.textContent = entry;
      metaRow.append(cell);
    });
    item.append(metaRow);
  }

  return item;
}
