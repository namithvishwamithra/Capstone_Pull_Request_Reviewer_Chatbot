import { useMemo, useState } from "react";
import type { Category, Finding, Severity } from "../../lib/types";

const severities: Severity[] = ["critical", "major", "minor", "nit"];
const categories: Category[] = [
  "bug",
  "security",
  "performance",
  "style",
  "missing_tests",
];
const categoryLabels: Record<Category, string> = {
  bug: "Bug",
  security: "Security",
  performance: "Performance",
  style: "Style",
  missing_tests: "Missing tests",
};

interface FindingsFiltersProps {
  findings: Finding[];
  selectedId: number | null;
  onSelect: (index: number) => void;
}

export function FindingsFilters({
  findings,
  selectedId,
  onSelect,
}: FindingsFiltersProps) {
  const [severity, setSeverity] = useState("all");
  const [category, setCategory] = useState("all");
  const visible = useMemo(
    () =>
      findings
        .map((finding, index) => ({ finding, index }))
        .filter(
          ({ finding }) =>
            (severity === "all" || finding.severity === severity) &&
            (category === "all" || finding.category === category),
        ),
    [findings, severity, category],
  );

  return (
    <section aria-labelledby="findings-heading" className="findings-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">WHAT TO LOOK AT</p>
          <h2 id="findings-heading">
            Findings <span className="count-pill">{visible.length}</span>
          </h2>
        </div>
        <button
          className="text-button"
          type="button"
          onClick={() => {
            setSeverity("all");
            setCategory("all");
          }}
        >
          Reset filters
        </button>
      </div>
      <div className="filter-row">
        <label>
          Severity
          <select
            aria-label="Filter by severity"
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="all">All levels</option>
            {severities.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Category
          <select
            aria-label="Filter by category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="all">All categories</option>
            {categories.map((value) => (
              <option key={value} value={value}>
                {categoryLabels[value]}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="finding-list">
        {visible.length ? (
          visible.map(({ finding, index }) => (
            <button
              key={`${finding.file}:${finding.line_start}:${index}`}
              type="button"
              className={`finding-card ${selectedId === index ? "is-selected" : ""}`}
              onClick={() => onSelect(index)}
            >
              <span
                className={`severity-dot severity-${finding.severity}`}
                aria-hidden="true"
              />
              <span className="finding-content">
                <span className="finding-topline">
                  <span className={`severity-label text-${finding.severity}`}>
                    {finding.severity}
                  </span>
                  <span className="category-label">
                    {categoryLabels[finding.category]}
                  </span>
                </span>
                <strong>{finding.title}</strong>
                <span className="finding-location">
                  {finding.file}:{finding.line_start}
                  {finding.line_end !== finding.line_start
                    ? `–${finding.line_end}`
                    : ""}
                </span>
                <span className="finding-explanation">
                  {finding.explanation}
                </span>
              </span>
              <span className="finding-arrow" aria-hidden="true">
                ↗
              </span>
            </button>
          ))
        ) : (
          <div className="empty-findings">
            {findings.length
              ? "No findings match these filters."
              : "No actionable findings found. Your changes are looking good."}
          </div>
        )}
      </div>
    </section>
  );
}
