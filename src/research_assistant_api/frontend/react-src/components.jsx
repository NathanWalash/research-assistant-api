import React from "react";
import { Link, NavLink } from "react-router-dom";

const INLINE_ALLOWED_TAGS = new Set(["i", "em", "b", "strong", "sub", "sup"]);

function renderInlineRichText(value) {
  if (typeof value !== "string") {
    return value ?? "";
  }
  if (!value.includes("<")) {
    return value;
  }

  const template = document.createElement("template");
  template.innerHTML = value;

  let keyIndex = 0;
  const toNodes = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent ?? "";
    }
    if (node.nodeType !== Node.ELEMENT_NODE) {
      return "";
    }

    const tagName = node.tagName.toLowerCase();
    const children = Array.from(node.childNodes).map(toNodes);

    if (INLINE_ALLOWED_TAGS.has(tagName)) {
      return React.createElement(tagName, { key: `inline-${keyIndex++}` }, ...children);
    }
    return children;
  };

  const output = Array.from(template.content.childNodes).map(toNodes).flat();
  return output.length ? output : value;
}

export function StatusBanner({ message, tone = "neutral" }) {
  if (!message) {
    return null;
  }
  const toneProps = tone === "neutral" ? {} : { "data-tone": tone };
  return (
    <p className="global-status" aria-live="polite" {...toneProps}>
      {message}
    </p>
  );
}

export function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

export function ResultItem({
  title,
  href = null,
  description = "",
  meta = [],
  badges = [],
  selected = false,
  actions = [],
  richText = true,
}) {
  const renderContent = (value) => (richText ? renderInlineRichText(value) : (value ?? ""));

  return (
    <article className="result-item" data-selected={selected ? "true" : undefined}>
      <h4>
        {href ? (
          <a href={href}>{renderContent(title)}</a>
        ) : (
          renderContent(title)
        )}
      </h4>
      {description ? <p>{renderContent(description)}</p> : null}
      {badges.length ? (
        <div className="badge-row">
          {badges.map((badge, index) => (
            <span className="badge" key={`${badge}-${index}`}>
              {renderContent(badge)}
            </span>
          ))}
        </div>
      ) : null}
      {meta.length ? (
        <div className="result-meta">
          {meta.map((entry, index) => (
            <small key={`${entry}-${index}`}>{renderContent(entry)}</small>
          ))}
        </div>
      ) : null}
      {actions.length ? (
        <div className="result-actions">
          {actions.map((action) => (
            <button
              key={action.label}
              className={`button ${action.tone ?? "secondary"} compact`}
              type="button"
              disabled={Boolean(action.disabled)}
              title={action.title ?? ""}
              onClick={action.onClick}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function MetricCard({ label, value }) {
  return (
    <article className="metric-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </article>
  );
}

export function MetaCard({ label, value }) {
  return (
    <div className="meta-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function BarItem({ title, valueLabel, ratio, meta = [] }) {
  const width = `${Math.max(0, Math.min(100, Math.round(ratio * 100)))}%`;
  return (
    <article className="result-item bar-item">
      <div className="bar-header">
        <h4>{title}</h4>
        <small>{valueLabel}</small>
      </div>
      <div className="bar-track">
        <span className="bar-fill" style={{ width }}></span>
      </div>
      {meta.length ? (
        <div className="result-meta">
          {meta.map((entry, index) => (
            <small key={`${entry}-${index}`}>{entry}</small>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function WorkspaceNav({ currentUser, onSignOut }) {
  const isAuthed = Boolean(currentUser);
  const accountLabel = "My account";

  return (
    <header className="workspace-nav">
      <Link className="brand-block brand-link" to="/">
        <p className="brand-title">
          <span className="brand-word-main">Research</span>
          <span className="brand-word-accent">Assistant</span>
        </p>
        <p className="brand-subtitle">Research workspace</p>
      </Link>
      <nav className="nav-actions" aria-label="Primary">
        <NavLink className="nav-link" to="/">
          Home
        </NavLink>
        <NavLink className="nav-link" to="/endpoints">
          Endpoints
        </NavLink>
        <NavLink className="nav-link" to="/discover">
          Discover
        </NavLink>
        <NavLink className="nav-link" to="/analytics">
          Analytics
        </NavLink>
        <NavLink className="nav-link" to="/projects">
          Projects
        </NavLink>
      </nav>
      <div className="nav-meta">
        {!isAuthed ? (
          <>
            <Link className="button secondary compact" to="/login">
              Sign in
            </Link>
            <Link className="button primary compact" to="/register">
              Create account
            </Link>
          </>
        ) : (
          <>
            <Link
              className="button secondary compact"
              to="/account"
              title={`Signed in as ${currentUser.email}`}
            >
              {accountLabel}
            </Link>
            <button className="button danger compact" type="button" onClick={onSignOut}>
              Sign out
            </button>
          </>
        )}
      </div>
    </header>
  );
}

export function Modal({ open, onClose, children, labelledBy }) {
  if (!open) {
    return null;
  }

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelledBy}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      {children}
    </div>
  );
}
