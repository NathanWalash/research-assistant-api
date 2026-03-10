import React, { createContext, useContext, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  ApiError,
  apiRequest,
  cleanText,
  clearSession,
  formatDate,
  formatDateTime,
  formatNumber,
  getAccessTokenExpiry,
  getSession,
  saveSession,
  toErrorMessage,
} from "./session.js";
import {
  BarItem,
  EmptyState,
  MetaCard,
  MetricCard,
  Modal,
  ResultItem,
  StatusBanner,
  WorkspaceNav,
} from "./components.jsx";

const SEARCH_LIMIT = 3;
const ANALYTICS_PAGE_LIMIT = 3;
const GRAPH_PAGE_LIMIT = 3;
const CITATION_SIDE_LIMIT = GRAPH_PAGE_LIMIT;
const DISCOVER_IDLE_SUMMARY = "Run a search to load papers.";
const METHOD_ORDER = ["GET", "POST", "PATCH", "PUT", "DELETE"];
const TAG_ORDER = [
  "meta",
  "health",
  "auth",
  "papers",
  "authors",
  "topics",
  "analytics",
  "projects",
  "reading-list",
  "annotations",
];
const TAG_LABELS = {
  meta: "Meta",
  health: "Health",
  auth: "Authentication",
  papers: "Paper Discovery",
  authors: "Author Discovery",
  topics: "Topic Discovery",
  analytics: "Corpus Analytics",
  projects: "Projects and Reading Lists (Authenticated)",
  "reading-list": "Reading List Items (Authenticated)",
  annotations: "Annotations (Authenticated)",
};

const AuthContext = createContext(null);

function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}

function AuthProvider({ children }) {
  const [sessionState, setSessionState] = useState(() => getSession());
  const [currentUser, setCurrentUser] = useState(() => getSession()?.user ?? null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function refreshUser() {
      const session = getSession();
      if (!session?.access_token) {
        if (!cancelled) {
          setSessionState(null);
          setCurrentUser(null);
          setLoading(false);
        }
        return;
      }

      try {
        const user = await apiRequest("/auth/me", {
          auth: true,
          accessToken: session.access_token,
        });
        if (cancelled) {
          return;
        }
        const updatedSession = { ...session, user };
        saveSession(updatedSession);
        setSessionState(updatedSession);
        setCurrentUser(user);
      } catch {
        if (cancelled) {
          return;
        }
        clearSession();
        setSessionState(null);
        setCurrentUser(null);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void refreshUser();
    return () => {
      cancelled = true;
    };
  }, []);

  function saveAuthSession(nextSession) {
    saveSession(nextSession);
    setSessionState(nextSession);
    setCurrentUser(nextSession?.user ?? null);
  }

  function signOut() {
    clearSession();
    setSessionState(null);
    setCurrentUser(null);
  }

  async function request(path, options = {}) {
    const accessToken = options.accessToken ?? sessionState?.access_token ?? null;
    try {
      return await apiRequest(path, { ...options, accessToken });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401 && options.auth) {
        signOut();
      }
      throw error;
    }
  }

  return (
    <AuthContext.Provider
      value={{
        session: sessionState,
        currentUser,
        loading,
        request,
        saveAuthSession,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

function pageFromPath(pathname) {
  if (pathname === "/" || pathname === "") {
    return "home";
  }
  if (pathname === "/discover") {
    return "discover";
  }
  if (pathname === "/endpoints") {
    return "endpoints";
  }
  if (pathname === "/projects") {
    return "projects";
  }
  if (pathname === "/analytics") {
    return "analytics";
  }
  if (pathname === "/account") {
    return "account";
  }
  if (pathname === "/login") {
    return "login";
  }
  if (pathname === "/register") {
    return "register";
  }
  return "home";
}

function usePageDataset() {
  const location = useLocation();

  useEffect(() => {
    document.body.dataset.page = pageFromPath(location.pathname);
  }, [location.pathname]);
}

function WorkspaceLayout({ children }) {
  const { currentUser, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate("/");
  }

  return (
    <div className="page-shell">
      <WorkspaceNav currentUser={currentUser} onSignOut={handleSignOut} />
      <main className="workspace-stack">{children}</main>
    </div>
  );
}

function HomePage() {
  const { request } = useAuth();
  const [status, setStatus] = useState({
    message: "Loading live summary data from the application.",
    tone: "neutral",
  });
  const [metrics, setMetrics] = useState({ paperCount: "Loading", latestYear: "Loading" });
  const [featuredPapers, setFeaturedPapers] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function loadLanding() {
      try {
        const [trends, topPapers] = await Promise.all([
          request("/analytics/trends?start_year=2018"),
          request("/analytics/top-papers?limit=2"),
        ]);
        if (cancelled) {
          return;
        }

        const paperCount = trends.reduce((total, item) => total + item.paper_count, 0);
        const latestYear = trends.length
          ? Math.max(...trends.map((item) => item.publication_year))
          : "N/A";

        setMetrics({
          paperCount: formatNumber(paperCount),
          latestYear: String(latestYear),
        });
        setFeaturedPapers(topPapers);
        setStatus({
          message: "Live corpus snapshot and top-cited papers.",
          tone: "success",
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setStatus({ message: toErrorMessage(error), tone: "error" });
        setFeaturedPapers([]);
      }
    }

    void loadLanding();
    return () => {
      cancelled = true;
    };
  }, [request]);

  return (
    <>
      <section className="hero-card hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Research Assistant</p>
          <h1>Find papers, save what matters, and move faster.</h1>
          <p className="hero-text">
            This workspace gives you a direct way into the application: discover papers,
            save the useful ones into projects, and review simple analytics without
            needing to think about the API underneath.
          </p>
          <div className="hero-actions">
            <Link className="button primary" to="/discover">
              Start discovering papers
            </Link>
            <Link className="button secondary" to="/register">
              Create account
            </Link>
          </div>
        </div>

        <aside className="surface-card emphasis-card landing-overview">
          <p className="section-eyebrow">At a glance</p>
          <h2>Live dataset snapshot.</h2>
          <div className="metric-grid">
            <MetricCard label="Papers" value={metrics.paperCount} />
            <MetricCard label="Latest year" value={metrics.latestYear} />
          </div>
          <p className="helper-text">{status.message}</p>
          <div className="landing-picks">
            <p className="landing-picks-label">Top papers right now</p>
            <div className="mini-paper-list">
              {featuredPapers.length ? (
                featuredPapers.map((paper) => (
                  <ResultItem
                    key={paper.id}
                    title={paper.title}
                    href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                    meta={[
                      `${paper.publication_year}`,
                      `${formatNumber(paper.citation_count)} citations`,
                    ]}
                  />
                ))
              ) : (
                <EmptyState message="Featured papers are unavailable right now." />
              )}
            </div>
          </div>
        </aside>
      </section>

      <section className="quick-grid">
        <article className="surface-card action-card">
          <p className="section-eyebrow">Discovery</p>
          <h2>Inspect papers fast.</h2>
          <p className="prose-block">
            Search papers, inspect context, and trace related work quickly.
          </p>
          <Link className="button secondary" to="/discover">
            Open discovery
          </Link>
        </article>

        <article className="surface-card action-card">
          <p className="section-eyebrow">Projects</p>
          <h2>Organise reading work.</h2>
          <p className="prose-block">
            Create projects, rank saved papers, and grow reading lists.
          </p>
          <Link className="button secondary" to="/projects">
            Open projects
          </Link>
        </article>

        <article className="surface-card action-card">
          <p className="section-eyebrow">Analytics</p>
          <h2>Track corpus trends.</h2>
          <p className="prose-block">
            View top papers, topic spread, and yearly publication trends.
          </p>
          <Link className="button secondary" to="/analytics">
            Open analytics
          </Link>
        </article>
      </section>
    </>
  );
}

function LoginPage() {
  const { currentUser, request, saveAuthSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState("Use an existing account or create a new one first.");

  if (currentUser) {
    return <Navigate to="/projects" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    try {
      const tokenResponse = await request("/auth/login", {
        method: "POST",
        body: { email: email.trim(), password },
      });
      saveAuthSession(tokenResponse);
      setStatus("Signed in. Redirecting to projects.");
      navigate("/projects");
    } catch (error) {
      setStatus(toErrorMessage(error));
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page-shell auth-shell">
      <Link className="back-link" to="/">
        Back
      </Link>
      <main className="hero-card auth-grid">
        <section className="hero-copy">
          <p className="eyebrow">Authentication</p>
          <h1>Log in to manage projects, reading lists, and annotations.</h1>
          <p className="hero-text">
            The frontend stores only the bearer token and current user in browser storage.
            All protected actions continue to flow through the FastAPI backend.
          </p>
          <ul className="hero-points">
            <li>Create and update private research projects.</li>
            <li>Attach notes to papers and reading-list items.</li>
            <li>Run semantic, citation, and hybrid recommendations.</li>
          </ul>
        </section>

        <section className="auth-card">
          <div className="section-header compact">
            <div>
              <p className="section-eyebrow">Sign in</p>
              <h2>Continue to your workspace.</h2>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleSubmit}>
            <label>
              <span>Email</span>
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <button className="button primary" type="submit" disabled={pending}>
              {pending ? "Signing in..." : "Log in"}
            </button>
          </form>
          <p className="helper-text">{status}</p>
          <div className="button-row">
            <Link className="button secondary compact" to="/register">
              Create account
            </Link>
            <Link className="button alt compact" to="/discover">
              Browse as guest
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

function RegisterPage() {
  const { currentUser, request, saveAuthSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState("After signup you will be redirected to the project workspace.");

  if (currentUser) {
    return <Navigate to="/projects" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    try {
      const tokenResponse = await request("/auth/register", {
        method: "POST",
        body: { email: email.trim(), password },
      });
      saveAuthSession(tokenResponse);
      setStatus("Account created. Redirecting to projects.");
      navigate("/projects");
    } catch (error) {
      setStatus(toErrorMessage(error));
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page-shell auth-shell">
      <Link className="back-link" to="/">
        Back
      </Link>
      <main className="hero-card auth-grid">
        <section className="hero-copy">
          <p className="eyebrow">Account setup</p>
          <h1>Create a user account and jump straight into the workspace.</h1>
          <p className="hero-text">
            Registration returns a bearer token immediately, so the frontend can take the
            user directly into their project dashboard after signup.
          </p>
          <ul className="hero-points">
            <li>Projects are fully user-scoped.</li>
            <li>Reading lists and annotations remain private to the owner.</li>
            <li>The same account works locally and on Railway once deployed.</li>
          </ul>
        </section>

        <section className="auth-card">
          <div className="section-header compact">
            <div>
              <p className="section-eyebrow">Register</p>
              <h2>Set up a new workspace.</h2>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleSubmit}>
            <label>
              <span>Email</span>
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                minLength={8}
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <button className="button primary" type="submit" disabled={pending}>
              {pending ? "Creating..." : "Create account"}
            </button>
          </form>
          <p className="helper-text">{status}</p>
          <div className="button-row">
            <Link className="button secondary compact" to="/login">
              Sign in instead
            </Link>
            <Link className="button alt compact" to="/discover">
              Browse as guest
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

function EndpointsPage() {
  const { request } = useAuth();
  const [status, setStatus] = useState({ message: "", tone: "neutral" });
  const [endpoints, setEndpoints] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function loadEndpoints() {
      try {
        const schema = await request("/openapi.json");
        if (cancelled) {
          return;
        }
        const extracted = extractEndpoints(schema);
        setEndpoints(extracted);
        const endpointCount = extracted.filter((entry) => entry.kind === "endpoint").length;
        const categoryCount = extracted.length - endpointCount;
        setStatus({
          message: `Loaded ${endpointCount} API endpoints from backend schema across ${categoryCount} categories.`,
          tone: "success",
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        setEndpoints([]);
        setStatus({ message: toErrorMessage(error), tone: "error" });
      }
    }

    void loadEndpoints();
    return () => {
      cancelled = true;
    };
  }, [request]);

  return (
    <>
      <section className="section-header">
        <div>
          <p className="section-eyebrow">API reference</p>
          <h1 className="page-title">Full endpoint inventory</h1>
        </div>
      </section>

      <section className="surface-card endpoints-surface">
        <p className="helper-text">
          This table is generated from the backend OpenAPI schema, so it always includes every API endpoint.
        </p>
        <StatusBanner message={status.message} tone={status.tone} />
        <div className="api-table-wrap">
          <table className="api-table">
            <thead>
              <tr>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Auth</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.length ? (
                endpoints.map((endpoint, index) =>
                  endpoint.kind === "category" ? (
                    <tr className="api-category-row" key={`category-${endpoint.tag}-${index}`}>
                      <td colSpan={4}>{endpoint.label}</td>
                    </tr>
                  ) : (
                    <tr
                      data-method={endpoint.method}
                      data-endpoint={endpoint.path}
                      key={`${endpoint.path}-${endpoint.method}`}
                    >
                      <td>
                        <span className={`pill method-pill ${endpoint.method.toLowerCase()}`}>
                          {endpoint.method}
                        </span>
                      </td>
                      <td>
                        <code>{endpoint.path}</code>
                      </td>
                      <td>{endpoint.auth}</td>
                      <td>{endpoint.description}</td>
                    </tr>
                  ),
                )
              ) : (
                <tr>
                  <td colSpan={4}>Loading endpoint inventory...</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function extractEndpoints(schema) {
  const paths = schema?.paths ?? {};
  const rows = [];
  const items = [];

  Object.entries(paths).forEach(([path, operations]) => {
    Object.entries(operations).forEach(([method, operation]) => {
      const methodName = method.toUpperCase();
      if (!METHOD_ORDER.includes(methodName)) {
        return;
      }
      const tag = Array.isArray(operation?.tags) && operation.tags.length
        ? operation.tags[0]
        : "meta";
      const description =
        cleanText(operation?.description) ||
        cleanText(operation?.summary) ||
        "No description available.";
      const authenticated =
        Array.isArray(operation?.security) && operation.security.length > 0;
      items.push({
        kind: "endpoint",
        tag,
        method: methodName,
        path,
        auth: authenticated ? "Yes" : "No",
        description,
      });
    });
  });

  items.sort((left, right) => {
    const leftTagIndex = tagIndex(left.tag);
    const rightTagIndex = tagIndex(right.tag);
    if (leftTagIndex !== rightTagIndex) {
      return leftTagIndex - rightTagIndex;
    }
    if (left.path !== right.path) {
      return left.path.localeCompare(right.path);
    }
    return METHOD_ORDER.indexOf(left.method) - METHOD_ORDER.indexOf(right.method);
  });

  let currentTag = null;
  items.forEach((item) => {
    if (item.tag !== currentTag) {
      currentTag = item.tag;
      rows.push({
        kind: "category",
        tag: currentTag,
        label: TAG_LABELS[currentTag] ?? currentTag,
      });
    }
    rows.push(item);
  });

  return rows;
}

function tagIndex(tag) {
  const index = TAG_ORDER.indexOf(tag);
  return index === -1 ? TAG_ORDER.length + 1 : index;
}

function formatAuthorPreview(authors) {
  if (!Array.isArray(authors) || !authors.length) {
    return "No authors";
  }

  const names = authors
    .map((author) => cleanText(author?.name ?? "").trim())
    .filter(Boolean);

  if (!names.length) {
    return "No authors";
  }
  if (names.length >= 3) {
    return `${names[0]} et al.`;
  }
  return names.join(", ");
}

function resolvePaperIdQuery(rawQuery) {
  const normalized = cleanText(rawQuery ?? "").trim();
  if (!normalized) {
    return null;
  }

  const urlMatch = normalized.match(/^https?:\/\/openalex\.org\/(w[0-9a-z-]+)$/i);
  if (urlMatch) {
    return `https://openalex.org/${urlMatch[1].toUpperCase()}`;
  }

  const idMatch = normalized.match(/^(w[0-9a-z-]+)$/i);
  if (idMatch) {
    return `https://openalex.org/${idMatch[1].toUpperCase()}`;
  }

  return null;
}

function resolveAuthorIdQuery(rawQuery) {
  const normalized = cleanText(rawQuery ?? "").trim();
  if (!normalized) {
    return null;
  }

  const urlMatch = normalized.match(/^https?:\/\/openalex\.org\/(a\d+)$/i);
  if (urlMatch) {
    return `https://openalex.org/${urlMatch[1].toUpperCase()}`;
  }

  const idMatch = normalized.match(/^(a\d+)$/i);
  if (idMatch) {
    return `https://openalex.org/${idMatch[1].toUpperCase()}`;
  }

  return null;
}

function AnalyticsPage() {
  const { request } = useAuth();
  const [status, setStatus] = useState({ message: "", tone: "neutral" });
  const [topicOptions, setTopicOptions] = useState([{ value: "", label: "All topics" }]);
  const [yearOptions, setYearOptions] = useState([{ value: "", label: "All years" }]);
  const [rangedYearOptions, setRangedYearOptions] = useState([{ value: "", label: "Any" }]);
  const [topPaperTopic, setTopPaperTopic] = useState("");
  const [topPaperYear, setTopPaperYear] = useState("");
  const [topicsYear, setTopicsYear] = useState("");
  const [trendsStartYear, setTrendsStartYear] = useState("");
  const [trendsEndYear, setTrendsEndYear] = useState("");
  const [summary, setSummary] = useState({
    totalPapers: "Loading",
    totalCitations: "Loading",
    latestYear: "Loading",
    topTopic: "Loading",
  });
  const [topPapers, setTopPapers] = useState([]);
  const [topPaperAuthorPreviewById, setTopPaperAuthorPreviewById] = useState({});
  const [topPapersOffset, setTopPapersOffset] = useState(0);
  const [topPapersHasMore, setTopPapersHasMore] = useState(false);
  const [topics, setTopics] = useState([]);
  const [topicsOffset, setTopicsOffset] = useState(0);
  const [topicsHasMore, setTopicsHasMore] = useState(false);
  const [trends, setTrends] = useState([]);
  const [trendsOffset, setTrendsOffset] = useState(0);
  const [authorSearchQuery, setAuthorSearchQuery] = useState("");
  const [authorMatches, setAuthorMatches] = useState([]);
  const [authorSearchPending, setAuthorSearchPending] = useState(false);
  const [selectedAuthorId, setSelectedAuthorId] = useState("");
  const [selectedAuthorDetail, setSelectedAuthorDetail] = useState(null);
  const [authorPapers, setAuthorPapers] = useState([]);
  const [authorPapersOffset, setAuthorPapersOffset] = useState(0);
  const [authorPapersHasMore, setAuthorPapersHasMore] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadFiltersAndData() {
      try {
        const [rawTopics, rawTrends] = await Promise.all([
          request("/topics?limit=50"),
          request("/analytics/trends?start_year=2018"),
        ]);
        if (cancelled) {
          return;
        }

        const years = [...new Set(rawTrends.map((item) => String(item.publication_year)))].sort(
          (left, right) => Number(right) - Number(left),
        );
        setTopicOptions(
          [{ value: "", label: "All topics" }].concat(
            rawTopics.map((topic) => ({ value: topic.name, label: topic.name })),
          ),
        );
        setYearOptions(
          [{ value: "", label: "All years" }].concat(
            years.map((year) => ({ value: year, label: year })),
          ),
        );
        setRangedYearOptions(
          [{ value: "", label: "Any" }].concat(
            years.map((year) => ({ value: year, label: year })),
          ),
        );
      } catch {
        if (!cancelled) {
          setTopicOptions([{ value: "", label: "All topics" }]);
          setYearOptions([{ value: "", label: "All years" }]);
          setRangedYearOptions([{ value: "", label: "Any" }]);
        }
      }
      if (!cancelled) {
        await Promise.allSettled([refreshAll()]);
      }
    }

    void loadFiltersAndData();
    return () => {
      cancelled = true;
    };
  }, [request]);

  useEffect(() => {
    const paperIds = [...new Set(topPapers.map((paper) => paper.id))];
    if (!paperIds.length) {
      return;
    }

    const pendingPaperIds = paperIds.filter((paperId) => !topPaperAuthorPreviewById[paperId]);
    if (!pendingPaperIds.length) {
      return;
    }

    let cancelled = false;

    async function loadAuthorPreviews() {
      const previews = await Promise.all(
        pendingPaperIds.map(async (paperId) => {
          try {
            const paperDetail = await request(`/papers/${encodeURIComponent(paperId)}`);
            return [paperId, formatAuthorPreview(paperDetail.authors ?? [])];
          } catch {
            return [paperId, "Authors unavailable"];
          }
        }),
      );

      if (cancelled) {
        return;
      }

      setTopPaperAuthorPreviewById((previous) => {
        const next = { ...previous };
        previews.forEach(([paperId, preview]) => {
          next[paperId] = preview;
        });
        return next;
      });
    }

    void loadAuthorPreviews();
    return () => {
      cancelled = true;
    };
  }, [topPapers, request, topPaperAuthorPreviewById]);

  useEffect(() => {
    const normalizedQuery = cleanText(authorSearchQuery ?? "").trim();
    if (!normalizedQuery || resolveAuthorIdQuery(normalizedQuery) || selectedAuthorId) {
      setAuthorMatches([]);
      return;
    }

    let active = true;
    const timeoutId = window.setTimeout(async () => {
      try {
        const params = new URLSearchParams({
          query: normalizedQuery,
          limit: "8",
          offset: "0",
        });
        const matches = await request(`/authors/search?${params.toString()}`);
        if (active) {
          setAuthorMatches(matches);
        }
      } catch {
        if (active) {
          setAuthorMatches([]);
        }
      }
    }, 220);

    return () => {
      active = false;
      window.clearTimeout(timeoutId);
    };
  }, [authorSearchQuery, request, selectedAuthorId]);

  async function refreshAll() {
    const results = await Promise.allSettled([
      loadSummary(),
      loadTopPapers({ offset: 0 }),
      loadTopics({ offset: 0 }),
      loadTrends({ offset: 0 }),
    ]);
    const failed = results.filter((result) => result.status === "rejected");
    if (!failed.length) {
      setStatus({ message: "", tone: "neutral" });
      return;
    }
    const firstFailure = failed[0];
    const message =
      firstFailure.status === "rejected"
        ? toErrorMessage(firstFailure.reason)
        : "Analytics refresh failed.";
    setStatus({ message, tone: "error" });
  }

  async function loadTopPapers({
    topic = topPaperTopic,
    year = topPaperYear,
    offset = topPapersOffset,
  } = {}) {
    const params = new URLSearchParams({
      limit: String(ANALYTICS_PAGE_LIMIT + 1),
      offset: String(offset),
    });
    if (topic.trim()) {
      params.set("topic", topic.trim());
    }
    if (year.trim()) {
      params.set("year", year.trim());
    }
    const response = await request(`/analytics/top-papers?${params.toString()}`);
    setTopPapers(response.slice(0, ANALYTICS_PAGE_LIMIT));
    setTopPapersHasMore(response.length > ANALYTICS_PAGE_LIMIT);
    setTopPapersOffset(offset);
  }

  async function loadTopics({ year = topicsYear, offset = topicsOffset } = {}) {
    const params = new URLSearchParams({
      limit: String(ANALYTICS_PAGE_LIMIT + 1),
      offset: String(offset),
    });
    if (year.trim()) {
      params.set("year", year.trim());
    }
    const response = await request(`/analytics/topics?${params.toString()}`);
    setTopics(response.slice(0, ANALYTICS_PAGE_LIMIT));
    setTopicsHasMore(response.length > ANALYTICS_PAGE_LIMIT);
    setTopicsOffset(offset);
  }

  async function loadTrends({
    startYear = trendsStartYear,
    endYear = trendsEndYear,
    offset = trendsOffset,
  } = {}) {
    const params = new URLSearchParams();
    if (startYear.trim()) {
      params.set("start_year", startYear.trim());
    }
    if (endYear.trim()) {
      params.set("end_year", endYear.trim());
    }
    const response = await request(`/analytics/trends?${params.toString()}`);
    setTrends(response);
    setTrendsOffset(offset >= response.length ? 0 : offset);
  }

  async function searchAuthors(queryText, limit = 8) {
    const normalizedQuery = cleanText(queryText ?? "").trim();
    if (!normalizedQuery) {
      return [];
    }
    const params = new URLSearchParams({
      query: normalizedQuery,
      limit: String(limit),
      offset: "0",
    });
    return request(`/authors/search?${params.toString()}`);
  }

  async function loadAuthorInsight({
    authorId = selectedAuthorId,
    offset = authorPapersOffset,
  } = {}) {
    if (!authorId) {
      setSelectedAuthorDetail(null);
      setAuthorPapers([]);
      setAuthorPapersOffset(0);
      setAuthorPapersHasMore(false);
      return;
    }

    const [authorDetail, papers] = await Promise.all([
      request(`/authors/${encodeURIComponent(authorId)}`),
      request(
        `/authors/${encodeURIComponent(authorId)}/papers?limit=${
          ANALYTICS_PAGE_LIMIT + 1
        }&offset=${offset}`,
      ),
    ]);

    setSelectedAuthorDetail(authorDetail);
    setAuthorPapers(papers.slice(0, ANALYTICS_PAGE_LIMIT));
    setAuthorPapersHasMore(papers.length > ANALYTICS_PAGE_LIMIT);
    setAuthorPapersOffset(offset);
  }

  async function handleAuthorSearchSubmit(event) {
    event.preventDefault();
    const normalizedQuery = cleanText(authorSearchQuery ?? "").trim();
    if (!normalizedQuery) {
      setStatus({
        message: "Enter an author name or OpenAlex author ID to search.",
        tone: "error",
      });
      return;
    }

    setAuthorSearchPending(true);
    try {
      const directAuthorId = resolveAuthorIdQuery(normalizedQuery);
      if (directAuthorId) {
        setSelectedAuthorId(directAuthorId);
        setAuthorSearchQuery(directAuthorId);
        setAuthorMatches([]);
        await loadAuthorInsight({ authorId: directAuthorId, offset: 0 });
        setStatus({ message: "", tone: "neutral" });
        return;
      }

      const matches = await searchAuthors(normalizedQuery, 8);
      setAuthorMatches(matches);
      if (!matches.length) {
        setStatus({
          message: "No authors matched that search query.",
          tone: "error",
        });
        return;
      }
      setStatus({
        message: "Select an author from the results below.",
        tone: "neutral",
      });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setAuthorSearchPending(false);
    }
  }

  async function handleAuthorSelect(author) {
    if (!author?.id) {
      return;
    }
    setAuthorSearchPending(true);
    try {
      const label = cleanText(author.name ?? "").trim() || author.id;
      setSelectedAuthorId(author.id);
      setAuthorSearchQuery(label);
      setAuthorMatches([]);
      await loadAuthorInsight({ authorId: author.id, offset: 0 });
      setStatus({ message: "", tone: "neutral" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setAuthorSearchPending(false);
    }
  }

  function handleAuthorSearchClear() {
    setAuthorSearchQuery("");
    setAuthorMatches([]);
    setSelectedAuthorId("");
    setStatus({ message: "", tone: "neutral" });
    void loadAuthorInsight({ authorId: "", offset: 0 }).catch((error) => {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    });
  }

  async function loadSummary() {
    try {
      const [trendsData, topTopicResult] = await Promise.all([
        request("/analytics/trends?start_year=2018"),
        request("/analytics/topics?limit=1"),
      ]);
      const reduced = trendsData.reduce(
        (accumulator, trend) => ({
          totalPapers: accumulator.totalPapers + trend.paper_count,
          totalCitations: accumulator.totalCitations + trend.total_citation_count,
          latestYear: Math.max(accumulator.latestYear, trend.publication_year),
        }),
        { totalPapers: 0, totalCitations: 0, latestYear: 0 },
      );
      setSummary({
        totalPapers: formatNumber(reduced.totalPapers),
        totalCitations: formatNumber(reduced.totalCitations),
        latestYear: reduced.latestYear > 0 ? String(reduced.latestYear) : "Unavailable",
        topTopic: topTopicResult[0]?.name ?? "Unavailable",
      });
    } catch {
      setSummary({
        totalPapers: "Unavailable",
        totalCitations: "Unavailable",
        latestYear: "Unavailable",
        topTopic: "Unavailable",
      });
    }
  }

  const visibleTrends = trends.slice(trendsOffset, trendsOffset + ANALYTICS_PAGE_LIMIT);
  const trendsHasMore = trendsOffset + ANALYTICS_PAGE_LIMIT < trends.length;

  return (
    <>
      <StatusBanner message={status.message} tone={status.tone} />
      <section className="section-header">
        <div>
          <p className="section-eyebrow">Analytics</p>
          <h1 className="page-title">Review the main patterns in the corpus.</h1>
        </div>
        <button className="button primary compact" type="button" onClick={() => void refreshAll()}>
          Refresh
        </button>
      </section>

      <section className="summary-grid">
        <MetricCard label="Total papers" value={summary.totalPapers} />
        <MetricCard label="Total citations" value={summary.totalCitations} />
        <MetricCard label="Latest year" value={summary.latestYear} />
        <MetricCard label="Top topic" value={summary.topTopic} />
      </section>

      <section className="analytics-stack">
        <article className="surface-card analytics-wide-card">
          <div className="card-header">
            <div>
              <p className="section-eyebrow">Top papers</p>
              <h2>Most cited papers</h2>
            </div>
          </div>
          <div className="stack-form compact-form analytics-card-controls">
            <div className="inline-grid analytics-top-paper-filters">
              <label>
                <span>Topic</span>
                <select
                  value={topPaperTopic}
                  onChange={(event) => {
                    const nextTopic = event.target.value;
                    setTopPaperTopic(nextTopic);
                    void loadTopPapers({ topic: nextTopic, year: topPaperYear, offset: 0 }).catch((error) => {
                      setStatus({ message: toErrorMessage(error), tone: "error" });
                    });
                  }}
                >
                  {topicOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Year</span>
                <select
                  value={topPaperYear}
                  onChange={(event) => {
                    const nextYear = event.target.value;
                    setTopPaperYear(nextYear);
                    void loadTopPapers({ topic: topPaperTopic, year: nextYear, offset: 0 }).catch((error) => {
                      setStatus({ message: toErrorMessage(error), tone: "error" });
                    });
                  }}
                >
                  {yearOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="result-list compact-list analytics-top-papers-results" id="analytics-top-papers-results">
            {topPapers.length ? (
              topPapers.map((paper, index) => (
                <ResultItem
                  key={paper.id}
                  title={paper.title}
                  href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                  badges={[
                    `#${topPapersOffset + index + 1}`,
                    `${formatNumber(paper.citation_count)} citations`,
                    paper.topic?.name ?? "No topic",
                  ]}
                  meta={[
                    `${paper.publication_year}`,
                    paper.journal ?? "No journal",
                    topPaperAuthorPreviewById[paper.id] ?? "Loading authors...",
                  ]}
                />
              ))
            ) : (
              <EmptyState message="No papers match the current filters." />
            )}
          </div>
          {topPapers.length ? (
            <div className="toolbar analytics-toolbar">
              <button
                className="button ghost compact"
                type="button"
                disabled={topPapersOffset <= 0}
                onClick={() => {
                  const nextOffset = Math.max(topPapersOffset - ANALYTICS_PAGE_LIMIT, 0);
                  void loadTopPapers({ offset: nextOffset }).catch((error) => {
                    setStatus({ message: toErrorMessage(error), tone: "error" });
                  });
                }}
              >
                Previous
              </button>
              <p className="helper-text">Page {Math.floor(topPapersOffset / ANALYTICS_PAGE_LIMIT) + 1}</p>
              <button
                className="button ghost compact"
                type="button"
                disabled={!topPapersHasMore}
                onClick={() => {
                  void loadTopPapers({ offset: topPapersOffset + ANALYTICS_PAGE_LIMIT }).catch((error) => {
                    setStatus({ message: toErrorMessage(error), tone: "error" });
                  });
                }}
              >
                Next
              </button>
            </div>
          ) : null}
        </article>

        <section className="analytics-grid analytics-mid-grid">
          <article className="surface-card analytics-mid-card">
            <div className="card-header">
              <div>
                <p className="section-eyebrow">Topics</p>
                <h2>Topic coverage</h2>
                <p className="helper-text">
                  Grouped by OpenAlex topic labels in the loaded corpus subset.
                </p>
              </div>
            </div>
            <div className="stack-form compact-form analytics-card-controls">
              <label>
                <span>Year</span>
                <select
                  value={topicsYear}
                  onChange={(event) => {
                    const nextYear = event.target.value;
                    setTopicsYear(nextYear);
                    void loadTopics({ year: nextYear, offset: 0 }).catch((error) => {
                      setStatus({ message: toErrorMessage(error), tone: "error" });
                    });
                  }}
                >
                  {yearOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="result-list compact-list analytics-mid-results analytics-topics-results">
              {topics.length ? (
                topics.map((topic) => {
                  const maxPaperCount = Math.max(...topics.map((entry) => entry.paper_count), 1);
                  return (
                    <BarItem
                      key={topic.id}
                      title={topic.name}
                      valueLabel={`${formatNumber(topic.paper_count)} papers`}
                      ratio={topic.paper_count / maxPaperCount}
                      meta={[
                        topic.field ? `Field: ${topic.field}` : `Topic ID: ${topic.id}`,
                        `${formatNumber(topic.total_citation_count)} citations`,
                        `${topic.average_citation_count.toFixed(1)} avg citations`,
                      ]}
                    />
                  );
                })
              ) : (
                <EmptyState message="No topic data is available for the current filters." />
              )}
            </div>
            {topics.length ? (
              <div className="toolbar analytics-toolbar">
                <button
                  className="button ghost compact"
                  type="button"
                  disabled={topicsOffset <= 0}
                  onClick={() => {
                    const nextOffset = Math.max(topicsOffset - ANALYTICS_PAGE_LIMIT, 0);
                    void loadTopics({ offset: nextOffset }).catch((error) => {
                      setStatus({ message: toErrorMessage(error), tone: "error" });
                    });
                  }}
                >
                  Previous
                </button>
                <p className="helper-text">Page {Math.floor(topicsOffset / ANALYTICS_PAGE_LIMIT) + 1}</p>
                <button
                  className="button ghost compact"
                  type="button"
                  disabled={!topicsHasMore}
                  onClick={() => {
                    void loadTopics({ offset: topicsOffset + ANALYTICS_PAGE_LIMIT }).catch((error) => {
                      setStatus({ message: toErrorMessage(error), tone: "error" });
                    });
                  }}
                >
                  Next
                </button>
              </div>
            ) : null}
          </article>

          <article className="surface-card analytics-mid-card">
            <div className="card-header">
              <div>
                <p className="section-eyebrow">Trends</p>
                <h2>Yearly output</h2>
                <p className="helper-text">
                  Publication and citation totals grouped by year for the selected range.
                </p>
              </div>
            </div>
            <div className="stack-form compact-form analytics-card-controls">
              <div className="inline-grid analytics-range-filters">
                <label>
                  <span>Start year</span>
                  <select
                    value={trendsStartYear}
                    onChange={(event) => {
                      const nextStartYear = event.target.value;
                      setTrendsStartYear(nextStartYear);
                      void loadTrends({
                        startYear: nextStartYear,
                        endYear: trendsEndYear,
                        offset: 0,
                      }).catch((error) => {
                        setStatus({ message: toErrorMessage(error), tone: "error" });
                      });
                    }}
                  >
                    {rangedYearOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>End year</span>
                  <select
                    value={trendsEndYear}
                    onChange={(event) => {
                      const nextEndYear = event.target.value;
                      setTrendsEndYear(nextEndYear);
                      void loadTrends({
                        startYear: trendsStartYear,
                        endYear: nextEndYear,
                        offset: 0,
                      }).catch((error) => {
                        setStatus({ message: toErrorMessage(error), tone: "error" });
                      });
                    }}
                  >
                    {rangedYearOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            <div className="result-list compact-list analytics-mid-results analytics-trends-results">
              {visibleTrends.length ? (
                visibleTrends.map((trend) => {
                  const maxPapers = Math.max(...visibleTrends.map((entry) => entry.paper_count), 1);
                  return (
                    <BarItem
                      key={trend.publication_year}
                      title={`${trend.publication_year}`}
                      valueLabel={`${formatNumber(trend.paper_count)} papers`}
                      ratio={trend.paper_count / maxPapers}
                      meta={[
                        `${formatNumber(trend.total_citation_count)} citations`,
                        `${trend.average_citation_count.toFixed(1)} avg citations`,
                      ]}
                    />
                  );
                })
              ) : (
                <EmptyState message="No yearly trend data is available for the current filters." />
              )}
            </div>
            {trends.length ? (
              <div className="toolbar analytics-toolbar">
                <button
                  className="button ghost compact"
                  type="button"
                  disabled={trendsOffset <= 0}
                  onClick={() => {
                    setTrendsOffset((current) => Math.max(current - ANALYTICS_PAGE_LIMIT, 0));
                  }}
                >
                  Previous
                </button>
                <p className="helper-text">Page {Math.floor(trendsOffset / ANALYTICS_PAGE_LIMIT) + 1}</p>
                <button
                  className="button ghost compact"
                  type="button"
                  disabled={!trendsHasMore}
                  onClick={() => {
                    setTrendsOffset((current) => current + ANALYTICS_PAGE_LIMIT);
                  }}
                >
                  Next
                </button>
              </div>
            ) : null}
          </article>
        </section>

        <section className="analytics-grid analytics-bottom-grid analytics-single-grid">
          <article className="surface-card analytics-bottom-card">
            <div className="card-header">
              <div>
                <p className="section-eyebrow">Authors</p>
                <h2>Author lookup</h2>
                <p className="helper-text">
                  Search by author name or ID using the API, then view profile and papers.
                </p>
              </div>
            </div>
            <div className="stack-form compact-form analytics-card-controls">
              <form className="analytics-author-search-form" onSubmit={handleAuthorSearchSubmit}>
                <label>
                  <span>Author</span>
                  <input
                    type="search"
                    value={authorSearchQuery}
                    placeholder="Search by name or https://openalex.org/A..."
                    onChange={(event) => {
                      if (selectedAuthorId) {
                        setSelectedAuthorId("");
                      }
                      setAuthorSearchQuery(event.target.value);
                    }}
                  />
                </label>
                <button className="button primary" type="submit" disabled={authorSearchPending}>
                  Find author
                </button>
                <button className="button secondary" type="button" onClick={handleAuthorSearchClear}>
                  Clear
                </button>
              </form>
            </div>

            {!selectedAuthorId ? (
              <div className="result-list compact-list analytics-author-search-results">
                {authorSearchQuery.trim() ? (
                  authorMatches.length ? (
                    authorMatches.map((author) => (
                      <ResultItem
                        key={author.id}
                        title={author.name}
                        badges={[`${formatNumber(author.paper_count)} papers`]}
                        meta={[
                          author.institution?.name ?? "Institution not available",
                          author.id,
                        ]}
                        actions={[
                          {
                            label: "Select author",
                            tone: "primary",
                            disabled: authorSearchPending,
                            onClick: () => {
                              void handleAuthorSelect(author);
                            },
                          },
                        ]}
                      />
                    ))
                  ) : (
                    <EmptyState message="No matching authors yet. Try another search term." />
                  )
                ) : (
                  <EmptyState message="Type a name, run search, then pick an author." />
                )}
              </div>
            ) : (
              <>
                <div className="toolbar analytics-author-selected-toolbar">
                  <p className="helper-text">
                    Showing profile and papers for the selected author.
                  </p>
                  <button className="button ghost compact" type="button" onClick={handleAuthorSearchClear}>
                    Search another author
                  </button>
                </div>
                {selectedAuthorDetail ? (
                  <div className="meta-grid analytics-author-meta">
                    <MetaCard label="Author" value={selectedAuthorDetail.name} />
                    <MetaCard label="Papers" value={formatNumber(selectedAuthorDetail.paper_count)} />
                    <MetaCard
                      label="Institution"
                      value={selectedAuthorDetail.institution?.name ?? "Not available"}
                    />
                    <MetaCard label="ORCID" value={selectedAuthorDetail.orcid ?? "Not available"} />
                  </div>
                ) : null}

                <div className="result-list compact-list analytics-author-results" id="analytics-author-papers-results">
                  {authorPapers.length ? (
                    authorPapers.map((paper) => (
                      <ResultItem
                        key={paper.id}
                        title={paper.title}
                        href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                        badges={[
                          `${formatNumber(paper.citation_count)} citations`,
                          paper.topic?.name ?? "No topic",
                        ]}
                        meta={[
                          `${paper.publication_year}`,
                          paper.journal ?? "No journal",
                          paper.id,
                        ]}
                      />
                    ))
                  ) : (
                    <EmptyState message="No papers found for this author." />
                  )}
                </div>

                {selectedAuthorId ? (
                  <div className="toolbar analytics-toolbar">
                    <button
                      className="button ghost compact"
                      type="button"
                      disabled={authorPapersOffset <= 0}
                      onClick={() => {
                        const nextOffset = Math.max(authorPapersOffset - ANALYTICS_PAGE_LIMIT, 0);
                        void loadAuthorInsight({ offset: nextOffset }).catch((error) => {
                          setStatus({ message: toErrorMessage(error), tone: "error" });
                        });
                      }}
                    >
                      Previous
                    </button>
                    <p className="helper-text">Page {Math.floor(authorPapersOffset / ANALYTICS_PAGE_LIMIT) + 1}</p>
                    <button
                      className="button ghost compact"
                      type="button"
                      disabled={!authorPapersHasMore}
                      onClick={() => {
                        void loadAuthorInsight({ offset: authorPapersOffset + ANALYTICS_PAGE_LIMIT }).catch((error) => {
                          setStatus({ message: toErrorMessage(error), tone: "error" });
                        });
                      }}
                    >
                      Next
                    </button>
                  </div>
                ) : null}
              </>
            )}
          </article>
        </section>
      </section>
    </>
  );
}

function AccountPage() {
  const { currentUser, request, session } = useAuth();
  const [status, setStatus] = useState({ message: "", tone: "neutral" });
  const [health, setHealth] = useState("Loading");
  const [environment, setEnvironment] = useState("Loading");
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const healthResult = await request("/health");
        if (!cancelled) {
          setHealth(healthResult.status ?? "Unavailable");
          setEnvironment(healthResult.environment ?? "Unavailable");
        }
      } catch (error) {
        if (!cancelled) {
          setHealth("Unavailable");
          setEnvironment("Unavailable");
          setStatus({ message: toErrorMessage(error), tone: "error" });
        }
      }

      if (!currentUser || cancelled) {
        return;
      }

      try {
        const userProjects = await request("/projects", { auth: true });
        if (cancelled) {
          return;
        }
        setProjects(userProjects);
        setStatus({ message: "Account summary loaded.", tone: "success" });
      } catch (error) {
        if (!cancelled) {
          setProjects([]);
          setStatus({ message: toErrorMessage(error), tone: "error" });
        }
      }
    }

    void loadData();
    return () => {
      cancelled = true;
    };
  }, [currentUser, request]);

  const tokenExpiry = getAccessTokenExpiry(session?.access_token ?? null);
  const latestProjectDate = projects.length
    ? projects
      .map((project) => new Date(project.created_at))
      .filter((value) => !Number.isNaN(value.getTime()))
      .sort((left, right) => right.getTime() - left.getTime())[0]
    : null;

  return (
    <>
      <StatusBanner message={status.message} tone={status.tone} />
      <section className="section-header">
        <div>
          <p className="section-eyebrow">Account</p>
          <h1 className="page-title">Check your session and jump back into the workspace.</h1>
        </div>
      </section>

      <section className="content-grid">
        <article className="surface-card">
          <div className="card-header">
            <div>
              <p className="section-eyebrow">Session</p>
              <h2>Current user</h2>
            </div>
          </div>
          <dl className="summary-list">
            <div>
              <dt>Email</dt>
              <dd>{currentUser?.email ?? "Guest"}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{currentUser ? "Authenticated" : "Signed out"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{currentUser ? formatDate(currentUser.created_at) : "Not available"}</dd>
            </div>
            <div>
              <dt>Token expires</dt>
              <dd>{tokenExpiry ? formatDateTime(tokenExpiry.toISOString()) : "Not available"}</dd>
            </div>
            <div>
              <dt>Frontend</dt>
              <dd>
                Served by FastAPI at <code>/app</code>
              </dd>
            </div>
          </dl>
          <div className="button-row">
            {!currentUser ? (
              <>
                <Link className="button secondary compact" to="/login">
                  Sign in
                </Link>
                <Link className="button primary compact" to="/register">
                  Create account
                </Link>
              </>
            ) : (
              <Link className="button secondary compact" to="/projects">
                Open projects
              </Link>
            )}
          </div>
        </article>

        <article className="surface-card">
          <div className="card-header">
            <div>
              <p className="section-eyebrow">System</p>
              <h2>Runtime status</h2>
            </div>
          </div>
          <dl className="summary-list">
            <div>
              <dt>Health</dt>
              <dd>{health}</dd>
            </div>
            <div>
              <dt>Environment</dt>
              <dd>{environment}</dd>
            </div>
          </dl>
          <div className="surface-subsection">
            <h3>Quick actions</h3>
          </div>
          <div className="link-list">
            <Link to="/discover">Open discovery</Link>
            <Link to="/projects">Open projects</Link>
            <Link to="/analytics">Open analytics</Link>
          </div>
        </article>
      </section>

      <section className="surface-card">
        <div className="card-header">
          <div>
            <p className="section-eyebrow">Workspace summary</p>
            <h2>Your current projects</h2>
          </div>
        </div>
        {!currentUser ? (
          <div className="callout visible">Sign in to view your project summary here.</div>
        ) : (
          <>
            <div className="summary-grid">
              <MetricCard label="Projects" value={formatNumber(projects.length)} />
              <MetricCard
                label="Latest project"
                value={latestProjectDate ? formatDate(latestProjectDate.toISOString()) : "Not available"}
              />
            </div>
            <div className="result-list">
              {projects.length ? (
                projects.map((project) => (
                  <ResultItem
                    key={project.id}
                    title={project.title}
                    description={project.description ?? "No description set."}
                    href={`/app/projects?project=${encodeURIComponent(project.id)}`}
                    meta={[formatDate(project.created_at)]}
                  />
                ))
              ) : (
                <EmptyState message="You have not created any projects yet." />
              )}
            </div>
          </>
        )}
      </section>
    </>
  );
}

function ProjectsPage() {
  const { currentUser, request } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState({ message: "", tone: "neutral" });
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [readingItems, setReadingItems] = useState([]);
  const [selectedReadingItemId, setSelectedReadingItemId] = useState("");
  const [createTitle, setCreateTitle] = useState("");
  const [createDescription, setCreateDescription] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [notes, setNotes] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationMode, setRecommendationMode] = useState("hybrid");
  const [semanticWeight, setSemanticWeight] = useState("0.7");
  const [citationWeight, setCitationWeight] = useState("0.3");
  const [pendingCreate, setPendingCreate] = useState(false);
  const [pendingUpdate, setPendingUpdate] = useState(false);
  const [pendingRecommendations, setPendingRecommendations] = useState(false);

  useEffect(() => {
    if (!currentUser) {
      setProjects([]);
      setSelectedProject(null);
      setReadingItems([]);
      setSelectedReadingItemId("");
      setRecommendations([]);
      return;
    }
    void loadProjects();
  }, [currentUser]);

  async function loadProjects() {
    const loadedProjects = await request("/projects", { auth: true });
    setProjects(loadedProjects);

    if (!loadedProjects.length) {
      setSelectedProject(null);
      setReadingItems([]);
      setSelectedReadingItemId("");
      setRecommendations([]);
      return;
    }

    const params = new URLSearchParams(location.search);
    const requestedProject = params.get("project");
    const selected =
      loadedProjects.find((project) => project.id === requestedProject) ?? loadedProjects[0];
    await selectProject(selected.id);
  }

  async function selectProject(projectId) {
    const project = await request(`/projects/${projectId}`, { auth: true });
    setSelectedProject(project);
    setEditTitle(project.title);
    setEditDescription(project.description ?? "");
    setRecommendations([]);
    const params = new URLSearchParams(location.search);
    params.set("project", project.id);
    navigate({ pathname: location.pathname, search: params.toString() }, { replace: true });
    await loadReadingList(project.id);
  }

  async function loadReadingList(projectId) {
    const items = await request(`/projects/${projectId}/reading-list`, { auth: true });
    setReadingItems(items);
    if (!items.length) {
      setSelectedReadingItemId("");
      setPriority("medium");
      setNotes("");
      return;
    }

    const selected = items.find((item) => item.id === selectedReadingItemId) ?? items[0];
    setSelectedReadingItemId(selected.id);
    setPriority(selected.priority);
    setNotes(selected.notes ?? "");
  }

  const selectedReadingItem = readingItems.find((item) => item.id === selectedReadingItemId) ?? null;

  useEffect(() => {
    if (!selectedReadingItem) {
      return;
    }
    setPriority(selectedReadingItem.priority);
    setNotes(selectedReadingItem.notes ?? "");
  }, [selectedReadingItemId]);

  function recommendationWeightNote() {
    if (recommendationMode === "semantic") {
      return "Semantic mode ignores citation score.";
    }
    if (recommendationMode === "citation") {
      return "Citation mode ignores semantic similarity.";
    }
    return "Hybrid mode uses both signals. Weights are normalized server-side.";
  }

  useEffect(() => {
    if (recommendationMode === "semantic") {
      setSemanticWeight("1");
      setCitationWeight("0");
      return;
    }
    if (recommendationMode === "citation") {
      setSemanticWeight("0");
      setCitationWeight("1");
      return;
    }
    if (!semanticWeight) {
      setSemanticWeight("0.7");
    }
    if (!citationWeight) {
      setCitationWeight("0.3");
    }
  }, [recommendationMode]);

  async function handleCreateProject(event) {
    event.preventDefault();
    if (!createTitle.trim()) {
      setStatus({ message: "Project title cannot be empty.", tone: "error" });
      return;
    }
    setPendingCreate(true);
    try {
      const project = await request("/projects", {
        method: "POST",
        auth: true,
        body: {
          title: createTitle.trim(),
          description: createDescription.trim() || null,
        },
      });
      setCreateTitle("");
      setCreateDescription("");
      await loadProjects();
      await selectProject(project.id);
      setStatus({ message: "Project created.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setPendingCreate(false);
    }
  }

  async function handleUpdateProject(event) {
    event.preventDefault();
    if (!selectedProject) {
      setStatus({ message: "Select a project before updating it.", tone: "error" });
      return;
    }
    if (!editTitle.trim()) {
      setStatus({ message: "Project title cannot be empty.", tone: "error" });
      return;
    }
    setPendingUpdate(true);
    try {
      await request(`/projects/${selectedProject.id}`, {
        method: "PATCH",
        auth: true,
        body: {
          title: editTitle.trim(),
          description: editDescription.trim() || null,
        },
      });
      await loadProjects();
      await selectProject(selectedProject.id);
      setStatus({ message: "Project details updated.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setPendingUpdate(false);
    }
  }

  async function handleDeleteProject() {
    if (!selectedProject) {
      return;
    }
    if (!window.confirm("Delete the selected project and all its workflow records?")) {
      return;
    }
    try {
      await request(`/projects/${selectedProject.id}`, {
        method: "DELETE",
        auth: true,
      });
      await loadProjects();
      setStatus({ message: "Project deleted.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function handleUpdateReadingItem(event) {
    event.preventDefault();
    if (!selectedReadingItem) {
      setStatus({ message: "Select a reading-list item first.", tone: "error" });
      return;
    }
    try {
      await request(`/reading-list-items/${selectedReadingItem.id}`, {
        method: "PATCH",
        auth: true,
        body: {
          priority,
          notes: notes.trim() || null,
        },
      });
      await loadReadingList(selectedProject.id);
      setStatus({ message: "Reading-list item updated.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function handleDeleteReadingItem() {
    if (!selectedReadingItem) {
      return;
    }
    try {
      await request(`/reading-list-items/${selectedReadingItem.id}`, {
        method: "DELETE",
        auth: true,
      });
      await loadReadingList(selectedProject.id);
      setStatus({ message: "Reading-list item deleted.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function handleRunRecommendations(event) {
    event.preventDefault();
    if (!selectedProject) {
      setStatus({ message: "Select a project before requesting recommendations.", tone: "error" });
      return;
    }
    const params = new URLSearchParams();
    params.set("mode", recommendationMode);
    params.set("limit", "10");
    params.set("semantic_weight", semanticWeight);
    params.set("citation_weight", citationWeight);

    setPendingRecommendations(true);
    try {
      const result = await request(
        `/projects/${selectedProject.id}/recommendations?${params.toString()}`,
        { auth: true },
      );
      setRecommendations(result);
      setStatus({ message: "Recommendations updated.", tone: "success" });
    } catch (error) {
      setRecommendations([]);
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setPendingRecommendations(false);
    }
  }

  return (
    <>
      <StatusBanner message={status.message} tone={status.tone} />
      <section className="section-header">
        <div>
          <p className="section-eyebrow">Projects</p>
          <h1 className="page-title">Choose a project and manage the saved papers.</h1>
        </div>
      </section>

      {!currentUser ? (
        <div className="callout visible">
          Sign in to create projects and manage a private reading list workspace.
        </div>
      ) : (
        <>
          <section className="workspace-grid projects-grid projects-top-grid">
            <article className="surface-card project-pane project-pane--catalog">
              <div className="card-header">
                <div>
                  <p className="section-eyebrow">Projects</p>
                  <h2>Create or select a project</h2>
                </div>
              </div>
              <p className="helper-text">
                Start a new project here, then switch between saved projects below.
              </p>
              <form className="stack-form project-create-form" onSubmit={handleCreateProject}>
                <label>
                  <span>Title</span>
                  <input
                    type="text"
                    placeholder="Dissertation on retrieval methods"
                    value={createTitle}
                    onChange={(event) => setCreateTitle(event.target.value)}
                    required
                  />
                </label>
                <label>
                  <span>Description</span>
                  <textarea
                    rows={4}
                    placeholder="Scope, theme, or question."
                    value={createDescription}
                    onChange={(event) => setCreateDescription(event.target.value)}
                  ></textarea>
                </label>
                <button className="button primary" type="submit" disabled={pendingCreate}>
                  {pendingCreate ? "Creating..." : "Create project"}
                </button>
              </form>

              <div className="card-header section-gap">
                <div>
                  <h3>Your projects</h3>
                </div>
              </div>
              <div className="result-list compact-list project-list" id="projects-list">
                {projects.length ? (
                  projects.map((project) => (
                    <ResultItem
                      key={project.id}
                      title={project.title}
                      description={project.description ?? "No description set."}
                      selected={selectedProject?.id === project.id}
                      meta={[`Created ${formatDateTime(project.created_at)}`]}
                      actions={[
                        {
                          label: "Open",
                          tone: "primary",
                          onClick: () => {
                            void selectProject(project.id).catch((error) => {
                              setStatus({ message: toErrorMessage(error), tone: "error" });
                            });
                          },
                        },
                      ]}
                    />
                  ))
                ) : (
                  <EmptyState message="Create your first project to start the workflow." />
                )}
              </div>
            </article>

            <article className="surface-card project-pane project-pane--current">
              <div className="card-header">
                <div>
                  <p className="section-eyebrow">Current project</p>
                  <h2>{selectedProject?.title ?? "No project selected"}</h2>
                </div>
                <span className="pill">
                  {selectedProject ? `${readingItems.length} items` : "0 items"}
                </span>
              </div>
              <form className="stack-form project-edit-form" onSubmit={handleUpdateProject}>
                <label>
                  <span>Title</span>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(event) => setEditTitle(event.target.value)}
                    disabled={!selectedProject}
                  />
                </label>
                <label>
                  <span>Description</span>
                  <textarea
                    rows={4}
                    value={editDescription}
                    onChange={(event) => setEditDescription(event.target.value)}
                    disabled={!selectedProject}
                  ></textarea>
                </label>
                <button className="button primary" type="submit" disabled={!selectedProject || pendingUpdate}>
                  {pendingUpdate ? "Saving..." : "Save project details"}
                </button>
              </form>
              <p className="helper-text">
                {selectedProject ? `Created ${formatDateTime(selectedProject.created_at)}` : "No project selected."}
              </p>
              <div className="button-row project-actions">
                <Link className="button secondary compact" to="/discover">
                  Add papers from Discover
                </Link>
                <button className="button danger" type="button" onClick={handleDeleteProject} disabled={!selectedProject}>
                  Delete project
                </button>
              </div>
            </article>
          </section>

          <section className="workspace-grid projects-grid projects-bottom-grid">
            <article className="surface-card project-pane project-pane--reading">
              <div className="card-header">
                <div>
                  <p className="section-eyebrow">Reading list</p>
                  <h2>Saved papers</h2>
                </div>
              </div>
              <p className="helper-text">
                Add papers from the Discover page, then use this page to review and tidy them.
              </p>

              <div className="card-header section-gap">
                <div>
                  <h3>Items in this project</h3>
                </div>
              </div>
              <div className="result-list compact-list reading-list-results" id="reading-items-list">
                {selectedProject ? (
                  readingItems.length ? (
                    readingItems.map((item) => (
                      <ResultItem
                        key={item.id}
                        title={item.paper.title}
                        href={`/app/discover?paper=${encodeURIComponent(item.paper.id)}`}
                        selected={selectedReadingItemId === item.id}
                        badges={[item.priority.toUpperCase()]}
                        description={item.notes ?? "No notes yet."}
                        meta={[
                          `${item.paper.publication_year}`,
                          `${formatNumber(item.paper.citation_count)} citations`,
                        ]}
                        actions={[
                          {
                            label: "Edit",
                            tone: "secondary",
                            onClick: () => {
                              setSelectedReadingItemId(item.id);
                              setPriority(item.priority);
                              setNotes(item.notes ?? "");
                            },
                          },
                        ]}
                      />
                    ))
                  ) : (
                    <EmptyState message="Add a paper to start the reading list." />
                  )
                ) : (
                  <EmptyState message="Select a project first." />
                )}
              </div>
            </article>

            <article className="surface-card project-pane project-pane--item">
              <div className="card-header">
                <div>
                  <p className="section-eyebrow">Selected paper</p>
                  <h2>{selectedReadingItem?.paper.title ?? "No reading-list item selected"}</h2>
                </div>
              </div>
              <div className="button-row project-selected-paper-actions">
                {selectedReadingItem ? (
                  <Link
                    className="button secondary compact"
                    to={`/discover?paper=${encodeURIComponent(selectedReadingItem.paper.id)}`}
                  >
                    Open paper
                  </Link>
                ) : null}
              </div>
              <form className="stack-form project-item-form" onSubmit={handleUpdateReadingItem}>
                <div className="inline-grid">
                  <label>
                    <span>Priority</span>
                    <select
                      value={priority}
                      onChange={(event) => setPriority(event.target.value)}
                      disabled={!selectedReadingItem}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </label>
                </div>
                <label>
                  <span>Notes</span>
                  <textarea
                    rows={5}
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    disabled={!selectedReadingItem}
                  ></textarea>
                </label>
                <div className="button-row project-item-actions">
                  <button className="button primary" type="submit" disabled={!selectedReadingItem}>
                    Save changes
                  </button>
                  <button className="button danger" type="button" onClick={handleDeleteReadingItem} disabled={!selectedReadingItem}>
                    Delete item
                  </button>
                </div>
              </form>
            </article>
          </section>

          <section className="surface-card project-recommend-card">
            <div className="card-header">
              <div>
                <p className="section-eyebrow">Recommendations</p>
                <h2>Suggested papers</h2>
              </div>
            </div>
            <p className="helper-text">
              Use a balanced, semantic, or citation-led view depending on what you want to surface.
            </p>
            <form className="stack-form project-recommend-form" onSubmit={handleRunRecommendations}>
              <label>
                <span>Mode</span>
                <select
                  value={recommendationMode}
                  onChange={(event) => setRecommendationMode(event.target.value)}
                >
                  <option value="hybrid">Balanced</option>
                  <option value="semantic">Semantic only</option>
                  <option value="citation">Citation only</option>
                </select>
              </label>
              <div className="inline-grid">
                <label>
                  <span>Semantic weight</span>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={semanticWeight}
                    onChange={(event) => setSemanticWeight(event.target.value)}
                    disabled={recommendationMode !== "hybrid"}
                  />
                </label>
                <label>
                  <span>Citation weight</span>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={citationWeight}
                    onChange={(event) => setCitationWeight(event.target.value)}
                    disabled={recommendationMode !== "hybrid"}
                  />
                </label>
              </div>
              <p className="helper-text">{recommendationWeightNote()}</p>
              <button className="button primary" type="submit" disabled={!selectedProject || pendingRecommendations}>
                {pendingRecommendations ? "Scoring..." : "Load recommendations"}
              </button>
            </form>
            <div className="result-list compact-list project-recommend-results" id="project-recommend-results">
              {recommendations.length ? (
                recommendations.map((paper) => (
                  <ResultItem
                    key={paper.id}
                    title={paper.title}
                    href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                    description={`${paper.scoring_mode} recommendation. Semantic ${paper.semantic_score.toFixed(3)}, citation ${paper.citation_score.toFixed(3)}.`}
                    badges={[`Score ${paper.recommendation_score.toFixed(3)}`]}
                    meta={[
                      `${paper.publication_year}`,
                      `${formatNumber(paper.citation_count)} citations`,
                      paper.topic?.name ?? "No topic",
                      `wS=${paper.semantic_weight.toFixed(2)} wC=${paper.citation_weight.toFixed(2)}`,
                    ]}
                  />
                ))
              ) : (
                <EmptyState message="Choose a recommendation mode and run scoring." />
              )}
            </div>
          </section>
        </>
      )}
    </>
  );
}

function DiscoverPage() {
  const { currentUser, request } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);

  const [status, setStatus] = useState({ message: "", tone: "neutral" });
  const [topicOptions, setTopicOptions] = useState([{ value: "", label: "Any topic" }]);
  const [yearOptions, setYearOptions] = useState([{ value: "", label: "Any year" }]);
  const [query, setQuery] = useState(params.get("query") ?? "");
  const [topic, setTopic] = useState(params.get("topic") ?? "");
  const [year, setYear] = useState(params.get("year") ?? "");
  const [citationCount, setCitationCount] = useState(params.get("citation_count") ?? "0");
  const [offset, setOffset] = useState(Number.parseInt(params.get("offset") ?? "0", 10) || 0);
  const [hasSearched, setHasSearched] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [searchSummary, setSearchSummary] = useState(DISCOVER_IDLE_SUMMARY);
  const [searchResults, setSearchResults] = useState([]);
  const [authorPreviewByPaperId, setAuthorPreviewByPaperId] = useState({});
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [similarOffset, setSimilarOffset] = useState(0);
  const [similarHasMore, setSimilarHasMore] = useState(false);
  const [similarPapers, setSimilarPapers] = useState([]);
  const [citationOffset, setCitationOffset] = useState(0);
  const [citationHasMore, setCitationHasMore] = useState(false);
  const [citationItems, setCitationItems] = useState([]);
  const [pathTarget, setPathTarget] = useState("");
  const [pathDepth, setPathDepth] = useState("6");
  const [pathResults, setPathResults] = useState([]);
  const [paperModalOpen, setPaperModalOpen] = useState(false);
  const [workspaceModalOpen, setWorkspaceModalOpen] = useState(false);
  const [projects, setProjects] = useState([]);
  const [saveProjectId, setSaveProjectId] = useState("");
  const [savePriority, setSavePriority] = useState("medium");
  const [annotations, setAnnotations] = useState([]);
  const [annotationId, setAnnotationId] = useState("");
  const [annotationText, setAnnotationText] = useState("");
  const [pendingSearch, setPendingSearch] = useState(false);
  const [pendingSimilar, setPendingSimilar] = useState(false);
  const [pendingCitations, setPendingCitations] = useState(false);
  const [pendingPath, setPendingPath] = useState(false);

  useEffect(() => {
    if (paperModalOpen || workspaceModalOpen) {
      document.body.classList.add("modal-open");
    } else {
      document.body.classList.remove("modal-open");
    }
    return () => {
      document.body.classList.remove("modal-open");
    };
  }, [paperModalOpen, workspaceModalOpen]);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Escape") {
        setPaperModalOpen(false);
        setWorkspaceModalOpen(false);
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadFilters() {
      try {
        const [topics, trends] = await Promise.all([
          request("/topics?limit=50"),
          request("/analytics/trends?start_year=2018"),
        ]);
        if (cancelled) {
          return;
        }
        const years = [...new Set(trends.map((entry) => String(entry.publication_year)))].sort(
          (left, right) => Number(right) - Number(left),
        );
        setTopicOptions(
          [{ value: "", label: "Any topic" }].concat(
            topics.map((entry) => ({ value: entry.name, label: entry.name })),
          ),
        );
        setYearOptions(
          [{ value: "", label: "Any year" }].concat(
            years.map((entry) => ({ value: entry, label: entry })),
          ),
        );
      } catch {
        if (!cancelled) {
          setTopicOptions([{ value: "", label: "Any topic" }]);
          setYearOptions([{ value: "", label: "Any year" }]);
        }
      }
    }

    void loadFilters();
    return () => {
      cancelled = true;
    };
  }, [request]);

  useEffect(() => {
    if (!currentUser) {
      setProjects([]);
      setSaveProjectId("");
      setAnnotations([]);
      return;
    }

    void request("/projects", { auth: true })
      .then((projectList) => {
        setProjects(projectList);
        if (projectList.length) {
          setSaveProjectId(projectList[0].id);
        }
      })
      .catch(() => {
        setProjects([]);
        setSaveProjectId("");
      });
  }, [currentUser, request]);

  useEffect(() => {
    const requestedPaper = params.get("paper");
    const hasQueryParams =
      Boolean((params.get("query") ?? "").trim()) ||
      Boolean((params.get("topic") ?? "").trim()) ||
      Boolean((params.get("year") ?? "").trim()) ||
      ((params.get("citation_count") ?? "").trim() !== "" &&
        (params.get("citation_count") ?? "0").trim() !== "0");

    if (!hasQueryParams) {
      setHasSearched(false);
      setSearchSummary(DISCOVER_IDLE_SUMMARY);
      setSearchResults([]);
      setHasMore(false);
      if (requestedPaper) {
        void loadPaperDetail(requestedPaper);
      }
      return;
    }

    void runSearch({ nextOffset: offset, autoSelectFirst: false }).then(() => {
      if (requestedPaper) {
        void loadPaperDetail(requestedPaper);
      }
    });
  }, []);

  useEffect(() => {
    const visiblePaperIds = [
      ...searchResults.map((paper) => paper.id),
      ...similarPapers.map((paper) => paper.id),
      ...citationItems.map((entry) => entry.paper.id),
    ];

    const uniquePaperIds = [...new Set(visiblePaperIds)];

    if (!uniquePaperIds.length) {
      setAuthorPreviewByPaperId({});
      return;
    }

    let cancelled = false;
    const pendingPaperIds = uniquePaperIds.filter((paperId) => !authorPreviewByPaperId[paperId]);

    if (!pendingPaperIds.length) {
      return;
    }

    async function loadAuthorPreviews() {
      const previews = await Promise.all(
        pendingPaperIds.map(async (paperId) => {
          try {
            const paperDetail = await request(`/papers/${encodeURIComponent(paperId)}`);
            return [paperId, formatAuthorPreview(paperDetail.authors ?? [])];
          } catch {
            return [paperId, "Authors unavailable"];
          }
        }),
      );

      if (cancelled) {
        return;
      }

      setAuthorPreviewByPaperId((previous) => {
        const next = { ...previous };
        previews.forEach(([paperId, preview]) => {
          next[paperId] = preview;
        });
        return next;
      });
    }

    void loadAuthorPreviews();
    return () => {
      cancelled = true;
    };
  }, [searchResults, similarPapers, citationItems, request, authorPreviewByPaperId]);

  function syncUrlState(nextValues) {
    const nextParams = new URLSearchParams(location.search);
    Object.entries(nextValues).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") {
        nextParams.delete(key);
      } else {
        nextParams.set(key, String(value));
      }
    });
    navigate({ pathname: location.pathname, search: nextParams.toString() }, { replace: true });
  }

  async function runSearch({
    nextOffset = offset,
    autoSelectFirst = false,
    filters = null,
  } = {}) {
    setPendingSearch(true);
    const activeQuery = filters?.query ?? query;
    const activeTopic = filters?.topic ?? topic;
    const activeYear = filters?.year ?? year;
    const activeCitationCount = filters?.citationCount ?? citationCount;
    const directPaperId = resolvePaperIdQuery(activeQuery);
    const canUseDirectPaperLookup =
      Boolean(directPaperId) &&
      !activeTopic.trim() &&
      !activeYear.trim() &&
      (!activeCitationCount.trim() || activeCitationCount.trim() === "0");

    if (canUseDirectPaperLookup) {
      try {
        const paper = await request(`/papers/${encodeURIComponent(directPaperId)}`);
        setHasSearched(true);
        setSearchResults([paper]);
        setHasMore(false);
        setOffset(0);
        setAuthorPreviewByPaperId((previous) => ({
          ...previous,
          [paper.id]: formatAuthorPreview(paper.authors ?? []),
        }));
        setSearchSummary("Page 1: 1 result (direct paper ID match).");
        syncUrlState({
          query: activeQuery.trim() || null,
          topic: null,
          year: null,
          citation_count: null,
          offset: null,
        });

        if (autoSelectFirst) {
          await loadPaperDetail(paper.id);
        }
      } catch (error) {
        setHasSearched(true);
        setSearchResults([]);
        setHasMore(false);
        setOffset(0);
        setSearchSummary("No paper found for that ID.");
        setStatus({ message: toErrorMessage(error), tone: "error" });
      } finally {
        setPendingSearch(false);
      }
      return;
    }

    const requestParams = new URLSearchParams();
    if (activeQuery.trim()) {
      requestParams.set("query", activeQuery.trim());
    }
    if (activeTopic.trim()) {
      requestParams.set("topic", activeTopic.trim());
    }
    if (activeYear.trim()) {
      requestParams.set("year", activeYear.trim());
    }
    if (activeCitationCount.trim()) {
      requestParams.set("citation_count", activeCitationCount.trim());
    }
    requestParams.set("limit", String(SEARCH_LIMIT));
    requestParams.set("offset", String(nextOffset));

    try {
      const papers = await request(`/papers/search?${requestParams.toString()}`);
      setHasSearched(true);
      setSearchResults(papers);
      setHasMore(papers.length === SEARCH_LIMIT);
      setOffset(nextOffset);
      if (!papers.length) {
        setSearchSummary("No results for the current filters.");
        if (nextOffset === 0) {
          setSelectedPaper(null);
          setSimilarPapers([]);
          setSimilarOffset(0);
          setSimilarHasMore(false);
          setCitationItems([]);
          setCitationOffset(0);
          setCitationHasMore(false);
          setPathResults([]);
          setAnnotations([]);
          syncUrlState({ paper: null });
        }
      } else {
        const currentPage = Math.floor(nextOffset / SEARCH_LIMIT) + 1;
        const resultLabel = papers.length === 1 ? "result" : "results";
        const hasAdditionalPages = papers.length === SEARCH_LIMIT;
        setSearchSummary(
          `Page ${currentPage}: ${papers.length} ${resultLabel}.${hasAdditionalPages ? " More available." : ""}`,
        );
      }

      syncUrlState({
        query: activeQuery.trim() || null,
        topic: activeTopic.trim() || null,
        year: activeYear.trim() || null,
        citation_count: activeCitationCount.trim() || null,
        offset: nextOffset || null,
      });

      if (
        autoSelectFirst &&
        papers.length &&
        (!selectedPaper || !papers.some((paper) => paper.id === selectedPaper.id))
      ) {
        await loadPaperDetail(papers[0].id);
      }
    } catch (error) {
      setHasSearched(true);
      setSearchResults([]);
      setSearchSummary("Search failed.");
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setPendingSearch(false);
    }
  }

  async function loadPaperDetail(paperId) {
    try {
      const paper = await request(`/papers/${encodeURIComponent(paperId)}`);
      setSelectedPaper(paper);
      syncUrlState({ paper: paper.id });

      await Promise.all([
        loadSimilarPapers(paper.id),
        loadCitations(paper.id),
        currentUser ? loadAnnotations(paper.id) : Promise.resolve(),
      ]);
      if (!currentUser) {
        setAnnotations([]);
      }
      setPathResults([]);
    } catch (error) {
      setSelectedPaper(null);
      setSimilarPapers([]);
      setSimilarOffset(0);
      setSimilarHasMore(false);
      setCitationItems([]);
      setCitationOffset(0);
      setCitationHasMore(false);
      setAnnotations([]);
      setPathResults([]);
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function loadSimilarPapers(paperId, nextOffset = 0) {
    setPendingSimilar(true);
    try {
      const papers = await request(
        `/papers/${encodeURIComponent(paperId)}/similar?limit=${GRAPH_PAGE_LIMIT}&offset=${nextOffset}`,
      );
      setSimilarPapers(papers);
      setSimilarOffset(nextOffset);
      setSimilarHasMore(papers.length === GRAPH_PAGE_LIMIT);
    } finally {
      setPendingSimilar(false);
    }
  }

  async function loadCitations(paperId, nextOffset = 0) {
    setPendingCitations(true);
    try {
      const citationData = await request(
        `/papers/${encodeURIComponent(paperId)}/citations?limit=${CITATION_SIDE_LIMIT}&offset=${nextOffset}`,
      );
      const items = [];
      citationData.cited_papers.forEach((paper) => {
        items.push({
          id: `cites-${paper.id}`,
          relation: "Cites",
          paper,
        });
      });
      citationData.citing_papers.forEach((paper) => {
        items.push({
          id: `cited-by-${paper.id}`,
          relation: "Cited by",
          paper,
        });
      });
      setCitationItems(items.slice(0, GRAPH_PAGE_LIMIT));
      setCitationOffset(nextOffset);
      setCitationHasMore(
        citationData.cited_papers.length === CITATION_SIDE_LIMIT ||
          citationData.citing_papers.length === CITATION_SIDE_LIMIT ||
          items.length > GRAPH_PAGE_LIMIT,
      );
    } finally {
      setPendingCitations(false);
    }
  }

  async function loadAnnotations(paperId) {
    if (!currentUser) {
      setAnnotations([]);
      return;
    }
    const noteItems = await request(`/papers/${encodeURIComponent(paperId)}/annotations`, {
      auth: true,
    });
    setAnnotations(noteItems);
  }

  function handleSimilarPageChange(nextOffset) {
    if (!selectedPaper) {
      return;
    }
    void loadSimilarPapers(selectedPaper.id, nextOffset).catch((error) => {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    });
  }

  function handleCitationPageChange(nextOffset) {
    if (!selectedPaper) {
      return;
    }
    void loadCitations(selectedPaper.id, nextOffset).catch((error) => {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    });
  }

  async function handlePathSubmit(event) {
    event.preventDefault();
    if (!selectedPaper) {
      setPathResults([]);
      return;
    }
    if (!pathTarget.trim()) {
      setPathResults([]);
      return;
    }

    setPendingPath(true);
    try {
      const data = await request(
        `/papers/${encodeURIComponent(selectedPaper.id)}/path/${encodeURIComponent(pathTarget.trim())}?max_depth=${encodeURIComponent(pathDepth)}`,
      );
      setPathResults(data.path);
      setStatus({
        message: `Citation path loaded (${data.path_length} hop${data.path_length === 1 ? "" : "s"}).`,
        tone: "success",
      });
    } catch (error) {
      setPathResults([]);
      setStatus({ message: toErrorMessage(error), tone: "error" });
    } finally {
      setPendingPath(false);
    }
  }

  async function handleSaveToProject(event) {
    event.preventDefault();
    if (!selectedPaper) {
      setStatus({ message: "Select a paper before saving it to a project.", tone: "error" });
      return;
    }
    if (!saveProjectId) {
      setStatus({ message: "Create or select a project first.", tone: "error" });
      return;
    }
    try {
      await request(`/projects/${saveProjectId}/reading-list`, {
        method: "POST",
        auth: true,
        body: {
          paper_id: selectedPaper.id,
          priority: savePriority,
          notes: null,
        },
      });
      setStatus({ message: "Paper added to the selected project.", tone: "success" });
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function handleSaveAnnotation(event) {
    event.preventDefault();
    if (!selectedPaper) {
      setStatus({ message: "Choose a paper before saving annotations.", tone: "error" });
      return;
    }
    if (!annotationText.trim()) {
      setStatus({ message: "Annotation text cannot be empty.", tone: "error" });
      return;
    }
    try {
      if (annotationId) {
        await request(`/annotations/${annotationId}`, {
          method: "PATCH",
          auth: true,
          body: { text: annotationText.trim() },
        });
        setStatus({ message: "Annotation updated.", tone: "success" });
      } else {
        await request(`/papers/${encodeURIComponent(selectedPaper.id)}/annotations`, {
          method: "POST",
          auth: true,
          body: { text: annotationText.trim() },
        });
        setStatus({ message: "Annotation created.", tone: "success" });
      }
      setAnnotationId("");
      setAnnotationText("");
      await loadAnnotations(selectedPaper.id);
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  async function handleDeleteAnnotation(id) {
    try {
      await request(`/annotations/${id}`, {
        method: "DELETE",
        auth: true,
      });
      setAnnotationId("");
      setAnnotationText("");
      await loadAnnotations(selectedPaper.id);
    } catch (error) {
      setStatus({ message: toErrorMessage(error), tone: "error" });
    }
  }

  const selectedPaperSummary = selectedPaper
    ? `Selected: ${selectedPaper.title} (${selectedPaper.publication_year ?? "N/A"}).`
    : "Select a paper from the search results to populate this section.";

  return (
    <>
      <StatusBanner message={status.message} tone={status.tone} />

      <section className="section-header">
        <div>
          <p className="section-eyebrow">Discovery</p>
          <h1 className="page-title">Search papers and inspect graph context clearly.</h1>
        </div>
      </section>

      <section className="surface-card discover-search-card">
        <div className="card-header">
          <div>
            <p className="section-eyebrow">Search</p>
            <h2>Find papers</h2>
          </div>
        </div>
        <p className="helper-text">
          Enter a topic or keywords, then filter by year and citations to search the corpus.
        </p>
        <form
          className="stack-form"
          onSubmit={(event) => {
            event.preventDefault();
            void runSearch({ nextOffset: 0, autoSelectFirst: false });
          }}
        >
          <div className="inline-grid discover-search-filters">
            <label>
              <span>Search text or paper ID</span>
              <input
                type="text"
                placeholder="e.g. climate change, Roman Empire, or https://openalex.org/W3"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <label>
              <span>Topic</span>
              <select value={topic} onChange={(event) => setTopic(event.target.value)}>
                {topicOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Year</span>
              <select value={year} onChange={(event) => setYear(event.target.value)}>
                {yearOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Minimum citations</span>
              <input
                type="number"
                min="0"
                step="1"
                value={citationCount}
                onChange={(event) => setCitationCount(event.target.value)}
              />
            </label>
          </div>
          <div className="button-row discover-search-actions">
            <button className="button primary" type="submit" disabled={pendingSearch}>
              {pendingSearch ? "Running..." : "Run search"}
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => {
                setQuery("");
                setTopic("");
                setYear("");
                setCitationCount("0");
                setOffset(0);
                setHasSearched(false);
                setSearchSummary(DISCOVER_IDLE_SUMMARY);
                setSearchResults([]);
                setHasMore(false);
                setSelectedPaper(null);
                setSimilarPapers([]);
                setSimilarOffset(0);
                setSimilarHasMore(false);
                setCitationItems([]);
                setCitationOffset(0);
                setCitationHasMore(false);
                setPathResults([]);
                setAnnotations([]);
                setPaperModalOpen(false);
                setWorkspaceModalOpen(false);
                setStatus({ message: "", tone: "neutral" });
                syncUrlState({
                  query: null,
                  topic: null,
                  year: null,
                  citation_count: null,
                  offset: null,
                  paper: null,
                });
              }}
            >
              Clear
            </button>
          </div>
        </form>
        <p className="helper-text">{searchSummary}</p>
        <div className="result-list discover-results-list" id="search-results">
          {searchResults.length ? (
            searchResults.map((paper) => {
              const canOpenWorkspace = Boolean(currentUser);
              return (
                <ResultItem
                  key={paper.id}
                  title={paper.title}
                  selected={selectedPaper?.id === paper.id}
                  badges={[paper.topic?.name ?? "No topic"]}
                  meta={[
                    `${paper.publication_year}`,
                    `${formatNumber(paper.citation_count)} citations`,
                    paper.journal ?? "No journal",
                    authorPreviewByPaperId[paper.id] ?? "Loading authors...",
                  ]}
                  actions={[
                    {
                      label: "Select",
                      onClick: () => {
                        void loadPaperDetail(paper.id);
                      },
                    },
                    {
                      label: "View",
                      tone: "primary",
                      onClick: () => {
                        void loadPaperDetail(paper.id).then(() => {
                          setPaperModalOpen(true);
                        });
                      },
                    },
                    {
                      label: "Workspace",
                      tone: "secondary",
                      disabled: !canOpenWorkspace,
                      title: canOpenWorkspace
                        ? "Save this paper or add private notes."
                        : "Sign in to use workspace actions.",
                      onClick: () => {
                        void loadPaperDetail(paper.id).then(() => {
                          if (canOpenWorkspace) {
                            setWorkspaceModalOpen(true);
                          }
                        });
                      },
                    },
                  ]}
                />
              );
            })
          ) : (
            <EmptyState
              message={
                hasSearched
                  ? "No papers matched the current filters."
                  : "Search results will appear here."
              }
            />
          )}
        </div>
        {hasSearched ? (
          <div className="toolbar">
            <button
              className="button ghost compact"
              type="button"
              id="search-prev"
              disabled={offset <= 0 || pendingSearch}
              onClick={() => {
                const nextOffset = Math.max(offset - SEARCH_LIMIT, 0);
                void runSearch({ nextOffset, autoSelectFirst: false });
              }}
            >
              Previous
            </button>
            <p className="helper-text">Page {Math.floor(offset / SEARCH_LIMIT) + 1}</p>
            <button
              className="button ghost compact"
              type="button"
              id="search-next"
              disabled={!hasMore || pendingSearch}
              onClick={() => {
                void runSearch({ nextOffset: offset + SEARCH_LIMIT, autoSelectFirst: false });
              }}
            >
              Next
            </button>
          </div>
        ) : null}
      </section>

      <section className="surface-card discover-graph-card">
        <div className="card-header">
          <div>
            <p className="section-eyebrow">Similarity and citation graph</p>
            <h2>Embedding neighbours and citation paths</h2>
            <p className="helper-text discover-selected-paper">{selectedPaperSummary}</p>
          </div>
          {selectedPaper ? (
            <button
              className="button alt compact discover-view-selected"
              type="button"
              onClick={() => setPaperModalOpen(true)}
            >
              View selected paper
            </button>
          ) : null}
        </div>
        <div className="split-columns">
          <section className="discover-graph-section discover-graph-block">
            <h3>Similar papers</h3>
            <p className="helper-text">Embedding neighbours for the selected paper.</p>
            <div
              className={`result-list compact-list discover-results-list graph-results-list ${
                selectedPaper ? "with-selection" : "no-selection"
              }`}
              id="similar-results"
            >
              {selectedPaper ? (
                similarPapers.length ? (
                  similarPapers.map((paper) => {
                    const canOpenWorkspace = Boolean(currentUser);
                    return (
                      <ResultItem
                        key={paper.id}
                        title={paper.title}
                        href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                        badges={[paper.topic?.name ?? "No topic"]}
                        meta={[
                          `${paper.publication_year}`,
                          `${formatNumber(paper.citation_count)} citations`,
                          paper.journal ?? "No journal",
                          authorPreviewByPaperId[paper.id] ?? "Loading authors...",
                        ]}
                        actions={[
                          {
                            label: "View",
                            tone: "primary",
                            onClick: () => {
                              void loadPaperDetail(paper.id).then(() => {
                                setPaperModalOpen(true);
                              });
                            },
                          },
                          {
                            label: "Workspace",
                            tone: "secondary",
                            disabled: !canOpenWorkspace,
                            title: canOpenWorkspace
                              ? "Save this paper or add private notes."
                              : "Sign in to use workspace actions.",
                            onClick: () => {
                              void loadPaperDetail(paper.id).then(() => {
                                if (canOpenWorkspace) {
                                  setWorkspaceModalOpen(true);
                                }
                              });
                            },
                          },
                        ]}
                      />
                    );
                  })
                ) : (
                  <EmptyState message="No similar papers are available." />
                )
              ) : (
                <EmptyState message="Select a paper to see similar papers." />
              )}
            </div>
            {selectedPaper ? (
              <div className="toolbar discover-subtoolbar">
                <button
                  className="button ghost compact"
                  type="button"
                  id="similar-prev"
                  disabled={similarOffset <= 0 || pendingSimilar}
                  onClick={() => {
                    const nextOffset = Math.max(similarOffset - GRAPH_PAGE_LIMIT, 0);
                    handleSimilarPageChange(nextOffset);
                  }}
                >
                  Previous
                </button>
                <p className="helper-text">Page {Math.floor(similarOffset / GRAPH_PAGE_LIMIT) + 1}</p>
                <button
                  className="button ghost compact"
                  type="button"
                  id="similar-next"
                  disabled={!similarHasMore || pendingSimilar}
                  onClick={() => {
                    handleSimilarPageChange(similarOffset + GRAPH_PAGE_LIMIT);
                  }}
                >
                  Next
                </button>
              </div>
            ) : null}
          </section>
          <section className="discover-graph-section discover-graph-block">
            <h3>Citation neighbourhood</h3>
            <p className="helper-text">Directly cited and citing papers in the local graph.</p>
            <div
              className={`result-list compact-list discover-results-list graph-results-list ${
                selectedPaper ? "with-selection" : "no-selection"
              }`}
              id="citation-results"
            >
              {selectedPaper ? (
                citationItems.length ? (
                  citationItems.map((entry) => {
                    const canOpenWorkspace = Boolean(currentUser);
                    return (
                      <ResultItem
                        key={entry.id}
                        title={`${entry.relation}: ${entry.paper.title}`}
                        href={`/app/discover?paper=${encodeURIComponent(entry.paper.id)}`}
                        badges={[entry.paper.topic?.name ?? "No topic"]}
                        meta={[
                          `${entry.paper.publication_year}`,
                          `${formatNumber(entry.paper.citation_count)} citations`,
                          entry.paper.journal ?? "No journal",
                          authorPreviewByPaperId[entry.paper.id] ?? "Loading authors...",
                        ]}
                        actions={[
                          {
                            label: "View",
                            tone: "primary",
                            onClick: () => {
                              void loadPaperDetail(entry.paper.id).then(() => {
                                setPaperModalOpen(true);
                              });
                            },
                          },
                          {
                            label: "Workspace",
                            tone: "secondary",
                            disabled: !canOpenWorkspace,
                            title: canOpenWorkspace
                              ? "Save this paper or add private notes."
                              : "Sign in to use workspace actions.",
                            onClick: () => {
                              void loadPaperDetail(entry.paper.id).then(() => {
                                if (canOpenWorkspace) {
                                  setWorkspaceModalOpen(true);
                                }
                              });
                            },
                          },
                        ]}
                      />
                    );
                  })
                ) : (
                  <EmptyState message="No local citation neighbours are available for this paper." />
                )
              ) : (
                <EmptyState message="Select a paper to see citation neighbours." />
              )}
            </div>
            {selectedPaper ? (
              <div className="toolbar discover-subtoolbar">
                <button
                  className="button ghost compact"
                  type="button"
                  id="citation-prev"
                  disabled={citationOffset <= 0 || pendingCitations}
                  onClick={() => {
                    const nextOffset = Math.max(citationOffset - CITATION_SIDE_LIMIT, 0);
                    handleCitationPageChange(nextOffset);
                  }}
                >
                  Previous
                </button>
                <p className="helper-text">Page {Math.floor(citationOffset / CITATION_SIDE_LIMIT) + 1}</p>
                <button
                  className="button ghost compact"
                  type="button"
                  id="citation-next"
                  disabled={!citationHasMore || pendingCitations}
                  onClick={() => {
                    handleCitationPageChange(citationOffset + CITATION_SIDE_LIMIT);
                  }}
                >
                  Next
                </button>
              </div>
            ) : null}
          </section>
        </div>
        <section className="surface-subsection discover-path-panel">
          <p className="section-eyebrow">Path finder</p>
          <h3>Find a citation path to another paper id</h3>
          <p className="helper-text">
            Runs directed shortest-path lookup within the Leeds citation subgraph.
          </p>
          <form className="stack-form discover-path-form" onSubmit={handlePathSubmit}>
            <label className="discover-path-target">
              <span>Target paper id</span>
              <input
                type="text"
                placeholder="https://openalex.org/W..."
                autoComplete="off"
                value={pathTarget}
                onChange={(event) => setPathTarget(event.target.value)}
              />
            </label>
            <label className="discover-path-depth">
              <span>Max depth</span>
              <select value={pathDepth} onChange={(event) => setPathDepth(event.target.value)}>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="6">6</option>
                <option value="8">8</option>
                <option value="12">12</option>
              </select>
            </label>
            <button
              className="button primary"
              type="submit"
              disabled={pendingPath || !selectedPaper}
            >
              {pendingPath ? "Finding..." : "Find path"}
            </button>
          </form>
          <div className="result-list compact-list discover-path-results" id="citation-path-results">
            {pathResults.length ? (
              pathResults.map((paper, index) => (
                <ResultItem
                  key={`${paper.id}-${index}`}
                  title={`${index === 0 ? "Source" : `Step ${index}`}: ${paper.title}`}
                  href={`/app/discover?paper=${encodeURIComponent(paper.id)}`}
                  badges={[index === pathResults.length - 1 ? "Target" : "Intermediate"]}
                  meta={[
                    paper.id,
                    `${paper.publication_year}`,
                    `${formatNumber(paper.citation_count)} citations`,
                  ]}
                />
              ))
            ) : (
              <EmptyState message="Select a source paper, enter a target ID, then click Find path." />
            )}
          </div>
        </section>
      </section>

      <Modal open={paperModalOpen} onClose={() => setPaperModalOpen(false)} labelledBy="paper-title">
        <article className="surface-card modal-card">
          <div className="card-header modal-header">
            <div>
              <p className="section-eyebrow">Paper detail</p>
              <h2 id="paper-title">{selectedPaper?.title ?? "Choose a paper from the search results"}</h2>
            </div>
            <button className="button compact modal-close" type="button" onClick={() => setPaperModalOpen(false)}>
              Close
            </button>
          </div>
          <div className="meta-grid discover-meta-grid">
            <MetaCard label="Paper ID" value={selectedPaper?.id ?? "Not available"} />
            <MetaCard label="Topic" value={selectedPaper?.topic?.name ?? "No topic"} />
            <MetaCard label="Published" value={formatDate(selectedPaper?.publication_date)} />
            <MetaCard label="Citations" value={formatNumber(selectedPaper?.citation_count)} />
            <MetaCard label="Year" value={selectedPaper?.publication_year ?? "Not available"} />
            <MetaCard label="Journal" value={selectedPaper?.journal ?? "Not available"} />
          </div>
          {selectedPaper?.abstract?.trim() ? (
            <details className="paper-abstract-panel">
              <summary>Abstract</summary>
              <div className="prose-block">{selectedPaper.abstract}</div>
            </details>
          ) : (
            <p className="helper-text">No abstract is available for this paper.</p>
          )}
          <section className="surface-subsection">
            <article className="modal-subcard">
              <h3>Authors</h3>
              <div className="result-list compact-list discover-scroll-window authors-window" id="paper-authors">
                {selectedPaper?.authors?.length ? (
                  selectedPaper.authors.map((author) => (
                    <ResultItem
                      key={author.id}
                      title={author.name}
                      description={author.institution?.name ?? "Institution not available"}
                      meta={[
                        author.orcid ?? "No ORCID",
                        author.is_corresponding ? "Corresponding author" : "Contributing author",
                      ]}
                    />
                  ))
                ) : (
                  <EmptyState message="No authorship metadata is available." />
                )}
              </div>
            </article>
          </section>
        </article>
      </Modal>

      <Modal open={workspaceModalOpen} onClose={() => setWorkspaceModalOpen(false)} labelledBy="workspace-modal-title">
        <article className="surface-card modal-card workspace-modal-card">
          <div className="card-header modal-header">
            <div>
              <p className="section-eyebrow">Workspace actions</p>
              <h2 id="workspace-modal-title">Save and annotate this paper</h2>
              <p className="helper-text">
                {selectedPaper
                  ? `${selectedPaper.title} (${selectedPaper.publication_year ?? "N/A"})`
                  : "No paper selected."}
              </p>
            </div>
            <button className="button compact modal-close" type="button" onClick={() => setWorkspaceModalOpen(false)}>
              Close
            </button>
          </div>
          <div className="workspace-action-grid">
            <article className="modal-subcard workspace-action-card">
              <h3>Save to project</h3>
              <p className="helper-text workspace-action-context">
                {selectedPaper
                  ? `${selectedPaper.title} (${selectedPaper.publication_year ?? "N/A"})`
                  : "No paper selected."}
              </p>
              {!currentUser ? (
                <div className="callout visible">Sign in to save papers to a project.</div>
              ) : (
                <form className="stack-form workspace-save-form" onSubmit={handleSaveToProject}>
                  <label>
                    <span>Project</span>
                    <select value={saveProjectId} onChange={(event) => setSaveProjectId(event.target.value)}>
                      {projects.length ? (
                        projects.map((project) => (
                          <option key={project.id} value={project.id}>
                            {project.title}
                          </option>
                        ))
                      ) : (
                        <option value="">Create a project first</option>
                      )}
                    </select>
                  </label>
                  <label>
                    <span>Priority</span>
                    <select value={savePriority} onChange={(event) => setSavePriority(event.target.value)}>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </label>
                  <button className="button primary" type="submit">
                    Add to project
                  </button>
                </form>
              )}
            </article>

            <article className="modal-subcard workspace-action-card workspace-notes-section">
              <h3>Write note</h3>
              <p className="helper-text workspace-action-context">
                Add a private note linked to this paper.
              </p>
              {!currentUser ? (
                <div className="callout visible">Sign in to add notes to this paper.</div>
              ) : (
                <form className="stack-form workspace-notes-form" onSubmit={handleSaveAnnotation}>
                  <label>
                    <span>Note</span>
                    <textarea
                      className="workspace-notes-input"
                      rows={4}
                      placeholder="Record why this paper matters or what to follow up."
                      value={annotationText}
                      onChange={(event) => setAnnotationText(event.target.value)}
                    ></textarea>
                  </label>
                  <div className="button-row">
                    <button className="button primary" type="submit">
                      {annotationId ? "Update note" : "Save note"}
                    </button>
                    {annotationId ? (
                      <button
                        className="button ghost"
                        type="button"
                        onClick={() => {
                          setAnnotationId("");
                          setAnnotationText("");
                        }}
                      >
                        Cancel edit
                      </button>
                    ) : null}
                  </div>
                </form>
              )}
            </article>
          </div>

          <article className="modal-subcard workspace-notes-board">
            <div className="workspace-notes-board-header">
              <h3>Saved notes</h3>
              {currentUser ? (
                <p className="helper-text">
                  {annotations.length} note{annotations.length === 1 ? "" : "s"}
                </p>
              ) : null}
            </div>
            {!currentUser ? (
              <div className="callout visible">Sign in to view notes for this paper.</div>
            ) : (
              <div
                className="result-list compact-list discover-scroll-window notes-window workspace-notes-list"
                id="workspace-notes-results"
              >
                {annotations.length ? (
                  annotations.map((note) => (
                    <ResultItem
                      key={note.id}
                      title={`Saved ${formatDate(note.created_at)}`}
                      description={note.text}
                      richText={false}
                      actions={[
                        {
                          label: "Edit",
                          onClick: () => {
                            setAnnotationId(note.id);
                            setAnnotationText(note.text);
                          },
                        },
                        {
                          label: "Delete",
                          tone: "ghost",
                          onClick: () => {
                            void handleDeleteAnnotation(note.id);
                          },
                        },
                      ]}
                    />
                  ))
                ) : (
                  <EmptyState message="No annotations saved for this paper yet." />
                )}
              </div>
            )}
          </article>
        </article>
      </Modal>
    </>
  );
}

function NotFoundPage() {
  return (
    <section className="surface-card">
      <h2>Page not found</h2>
      <p className="helper-text">This route is not part of the frontend app.</p>
      <Link className="button secondary compact" to="/">
        Back home
      </Link>
    </section>
  );
}

function AppRouter() {
  usePageDataset();

  return (
    <Routes>
      <Route
        path="/"
        element={(
          <WorkspaceLayout>
            <HomePage />
          </WorkspaceLayout>
        )}
      />
      <Route
        path="/discover"
        element={(
          <WorkspaceLayout>
            <DiscoverPage />
          </WorkspaceLayout>
        )}
      />
      <Route
        path="/endpoints"
        element={(
          <WorkspaceLayout>
            <EndpointsPage />
          </WorkspaceLayout>
        )}
      />
      <Route
        path="/projects"
        element={(
          <WorkspaceLayout>
            <ProjectsPage />
          </WorkspaceLayout>
        )}
      />
      <Route
        path="/analytics"
        element={(
          <WorkspaceLayout>
            <AnalyticsPage />
          </WorkspaceLayout>
        )}
      />
      <Route
        path="/account"
        element={(
          <WorkspaceLayout>
            <AccountPage />
          </WorkspaceLayout>
        )}
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="*"
        element={(
          <WorkspaceLayout>
            <NotFoundPage />
          </WorkspaceLayout>
        )}
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter basename="/app">
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

const mountNode = document.querySelector("#app-root");
if (mountNode) {
  createRoot(mountNode).render(<App />);
}
