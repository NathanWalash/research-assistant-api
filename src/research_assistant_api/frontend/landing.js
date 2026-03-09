import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatNumber,
  renderEmpty,
  setStatus,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#landing-status");
  const metrics = document.querySelector("#landing-metrics");
  const featuredPapers = document.querySelector("#featured-papers");
  const featuredTopics = document.querySelector("#featured-topics");

  await bootstrapPage();

  try {
    const [health, trends, topPapers, topTopics] = await Promise.all([
      apiRequest("/health"),
      apiRequest("/analytics/trends?start_year=2018"),
      apiRequest("/analytics/top-papers?limit=3"),
      apiRequest("/analytics/topics?limit=4"),
    ]);

    const paperCount = trends.reduce((total, item) => total + item.paper_count, 0);
    const latestYear = trends.length
      ? Math.max(...trends.map((item) => item.publication_year))
      : "N/A";

    metrics.replaceChildren(
      buildMetricCard("Papers", formatNumber(paperCount)),
      buildMetricCard("Top topic", topTopics[0]?.name ?? "Unavailable"),
      buildMetricCard("Latest year", String(latestYear)),
      buildMetricCard("API", health.status ?? "Unknown"),
    );

    if (!topPapers.length) {
      renderEmpty(featuredPapers, "No featured papers are available yet.");
    } else {
      featuredPapers.replaceChildren(
        ...topPapers.map((paper) =>
          createResultItem({
            title: paper.title,
            href: `/app/discover?paper=${encodeURIComponent(paper.id)}`,
            meta: [
              `${paper.publication_year}`,
              `${formatNumber(paper.citation_count)} citations`,
              paper.topic?.name ?? "No topic",
            ],
          }),
        ),
      );
    }

    if (!topTopics.length) {
      renderEmpty(featuredTopics, "No topic analytics are available yet.");
    } else {
      featuredTopics.replaceChildren(
        ...topTopics.map((topic) =>
          createResultItem({
            title: topic.name,
            description: topic.field ?? "Topic field not available.",
            badges: [`${formatNumber(topic.paper_count)} papers`],
            meta: [
              `${formatNumber(topic.total_citation_count)} total citations`,
              `${topic.average_citation_count.toFixed(1)} avg citations`,
            ],
          }),
        ),
      );
    }

    setStatus(statusElement, "Landing page synced with the live API.", "success");
  } catch (error) {
    setStatus(statusElement, error.message, "error");
    renderEmpty(featuredPapers, "Featured papers are unavailable right now.");
    renderEmpty(featuredTopics, "Topic coverage is unavailable right now.");
  }
});

function buildMetricCard(label, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "metric-card";
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  description.textContent = value;
  wrapper.append(term, description);
  return wrapper;
}
