import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { FindingsFilters } from "../src/features/review/FindingsFilters";
import { ReviewResults } from "../src/features/review/ReviewResults";
import type { Finding } from "../src/lib/types";

const findings: Finding[] = [
  {
    severity: "major",
    category: "security",
    file: "src/auth.py",
    line_start: 8,
    line_end: 8,
    title: "Missing permission check",
    explanation: "An untrusted user can access the resource.",
    suggested_fix: "Check ownership.",
  },
  {
    severity: "nit",
    category: "style",
    file: "src/ui.ts",
    line_start: 2,
    line_end: 2,
    title: "Simplify expression",
    explanation: "This could be clearer.",
    suggested_fix: "",
  },
];

it("filters findings by severity and clears the filter", () => {
  render(
    <FindingsFilters
      findings={findings}
      selectedId={null}
      onSelect={() => undefined}
    />,
  );
  fireEvent.change(screen.getByLabelText("Filter by severity"), {
    target: { value: "major" },
  });
  expect(screen.getByText("Missing permission check")).toBeInTheDocument();
  expect(screen.queryByText("Simplify expression")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /reset filters/i }));
  expect(screen.getByText("Simplify expression")).toBeInTheDocument();
});

it("filters findings by category", () => {
  render(
    <FindingsFilters
      findings={findings}
      selectedId={null}
      onSelect={() => undefined}
    />,
  );
  fireEvent.change(screen.getByLabelText("Filter by category"), {
    target: { value: "security" },
  });
  expect(screen.getByText("Missing permission check")).toBeInTheDocument();
  expect(screen.queryByText("Simplify expression")).not.toBeInTheDocument();
});

it("renders the review summary and highlights the changed line for a selected finding", () => {
  Element.prototype.scrollIntoView = vi.fn();
  render(
    <ReviewResults
      review={{
        id: "review-2",
        title: "Fix authorization",
        summary: "Adds an ownership guard before returning account data.",
        findings: [findings[0]],
        changed_files: ["src/auth.py"],
        excluded_files: [],
        processed_changed_lines: 1,
        diff: "diff --git a/src/auth.py b/src/auth.py\n--- a/src/auth.py\n+++ b/src/auth.py\n@@ -7 +7,2 @@\n existing()\n+check_owner()\n",
      }}
      onStartOver={() => undefined}
    />,
  );
  expect(
    screen.getByText("Adds an ownership guard before returning account data."),
  ).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: /missing permission check/i }),
  );
  expect(document.getElementById("code-line-8")).toHaveClass(
    "line-highlighted",
  );
});

it("shows a clear empty state when a review has no actionable findings", () => {
  render(
    <FindingsFilters
      findings={[]}
      selectedId={null}
      onSelect={() => undefined}
    />,
  );
  expect(screen.getByText(/no actionable findings found/i)).toBeInTheDocument();
});
