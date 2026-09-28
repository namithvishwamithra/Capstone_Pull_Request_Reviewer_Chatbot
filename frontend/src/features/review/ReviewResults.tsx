import { useEffect, useMemo, useState } from "react";
import type { Review } from "../../lib/types";
import { FindingsFilters } from "./FindingsFilters";

function mapDiffRows(diff: string) {
  let newLine = 0;
  return diff.split("\n").map((line) => {
    const hunk = line.match(/^@@ .* \+(\d+)/);
    if (line.startsWith("diff --git ")) newLine = 0;
    if (hunk) {
      newLine = Number(hunk[1]);
      return { text: line, lineNumber: null as number | null };
    }
    if (
      line.startsWith("+++ ") ||
      line.startsWith("--- ") ||
      line.startsWith("\\")
    ) {
      return { text: line, lineNumber: null as number | null };
    }
    if (line.startsWith("+")) return { text: line, lineNumber: newLine++ };
    if (line.startsWith(" ")) return { text: line, lineNumber: newLine++ };
    return { text: line, lineNumber: null as number | null };
  });
}

interface ReviewResultsProps {
  review: Review;
  onStartOver: () => void;
}

function exportMarkdown(review: Review) {
  const escape = (value: string) =>
    value
      .replaceAll("\\", "\\\\")
      .replaceAll("`", "\\`")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  const findings = review.findings.length
    ? review.findings
        .map((finding) =>
          [
            `### [${finding.severity.toUpperCase()}] ${escape(finding.title)}`,
            `**${escape(finding.category)}** · \`${escape(finding.file)}:${finding.line_start}-${finding.line_end}\``,
            escape(finding.explanation),
            finding.suggested_fix
              ? `**Suggested fix:** ${escape(finding.suggested_fix)}`
              : "",
          ]
            .filter(Boolean)
            .join("\n\n"),
        )
        .join("\n\n")
    : "No actionable findings were identified.";
  const markdown = `# ${escape(review.title)}\n\n${escape(review.summary)}\n\n## Findings\n\n${findings}\n`;
  const url = URL.createObjectURL(
    new Blob([markdown], { type: "text/markdown;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "pull-request-review.md";
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ReviewResults({ review, onStartOver }: ReviewResultsProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const selectedFinding = selected === null ? null : review.findings[selected];
  const codeRows = useMemo(() => mapDiffRows(review.diff ?? ""), [review.diff]);

  useEffect(() => {
    if (selectedFinding) {
      document
        .getElementById(`code-line-${selectedFinding.line_start}`)
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [selectedFinding]);

  return (
    <div className="review-results">
      <header className="results-header">
        <div>
          <p className="eyebrow">
            REVIEW COMPLETE · {review.processed_changed_lines} CHANGED LINES
          </p>
          <h1>{review.title}</h1>
          <p className="review-summary">{review.summary}</p>
        </div>
        <div className="result-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => exportMarkdown(review)}
          >
            Export Markdown
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={onStartOver}
          >
            New review
          </button>
        </div>
      </header>
      {review.excluded_files.length > 0 && (
        <p className="coverage-note">
          Skipped by default: {review.excluded_files.join(", ")}
        </p>
      )}
      <div className="review-columns">
        <div className="findings-column">
          <FindingsFilters
            findings={review.findings}
            selectedId={selected}
            onSelect={(index) => setSelected(index)}
          />
        </div>
        <section className="diff-column" aria-labelledby="diff-heading">
          <div className="section-heading">
            <div>
              <p className="eyebrow">CHANGESET</p>
              <h2 id="diff-heading">
                Diff{" "}
                <span className="count-pill">
                  {review.changed_files.length} files
                </span>
              </h2>
            </div>
          </div>
          <div
            className="diff-viewer"
            role="region"
            aria-label="Pull request diff"
            tabIndex={0}
          >
            {codeRows.map(({ text, lineNumber }, index) => {
              const addedLines =
                text.startsWith("+") && !text.startsWith("+++");
              const active =
                addedLines &&
                selectedFinding &&
                lineNumber !== null &&
                lineNumber >= selectedFinding.line_start &&
                lineNumber <= selectedFinding.line_end;
              return (
                <div
                  id={
                    addedLines && lineNumber
                      ? `code-line-${lineNumber}`
                      : undefined
                  }
                  key={index}
                  className={`diff-line ${addedLines ? "line-added" : text.startsWith("-") && !text.startsWith("---") ? "line-removed" : ""} ${active ? "line-highlighted" : ""}`}
                >
                  <span className="line-number" aria-hidden="true">
                    {lineNumber ?? ""}
                  </span>
                  <code>{text || " "}</code>
                </div>
              );
            })}
            {!review.diff && (
              <p className="empty-state">
                Diff text is not available in this active review.
              </p>
            )}
          </div>
          {selectedFinding && (
            <aside className="suggestion-card">
              <p className="eyebrow">SUGGESTED FIX</p>
              <p>
                {selectedFinding.suggested_fix ||
                  "Review the finding and apply an appropriate fix."}
              </p>
            </aside>
          )}
        </section>
      </div>
    </div>
  );
}
