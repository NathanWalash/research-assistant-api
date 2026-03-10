import {
  apiRequest,
  bootstrapPage,
  createResultItem,
  formatNumber,
  renderEmpty,
  setStatus,
  toErrorMessage,
} from "/app/static/shared.js";

document.addEventListener("DOMContentLoaded", async () => {
  const statusElement = document.querySelector("#landing-status");
  const metrics = document.querySelector("#landing-metrics");
  const featuredPapers = document.querySelector("#landing-featured-papers");

  await bootstrapPage();

  try {
    const [trends, topPapers] = await Promise.all([
      apiRequest("/analytics/trends?start_year=2018"),
      apiRequest("/analytics/top-papers?limit=2"),
    ]);

    const paperCount = trends.reduce((total, item) => total + item.paper_count, 0);
    const latestYear = trends.length
      ? Math.max(...trends.map((item) => item.publication_year))
      : "N/A";

    metrics.replaceChildren(
      buildMetricCard("Papers", formatNumber(paperCount)),
      buildMetricCard("Latest year", String(latestYear)),
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
            ],
          }),
        ),
      );
    }

    setStatus(
      statusElement,
      "Live corpus snapshot and top-cited papers.",
      "success",
    );
  } catch (error) {
    setStatus(statusElement, toErrorMessage(error), "error");
    renderEmpty(featuredPapers, "Featured papers are unavailable right now.");
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
