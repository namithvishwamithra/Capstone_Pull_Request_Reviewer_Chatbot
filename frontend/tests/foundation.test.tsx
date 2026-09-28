import { render, screen } from "@testing-library/react";
import { FindingsFilters } from "../src/features/review/FindingsFilters";
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

it("shows findings and exposes severity and category filter controls", () => {
  render(
    <FindingsFilters
      findings={findings}
      selectedId={null}
      onSelect={() => undefined}
    />,
  );
  expect(screen.getByText("Missing permission check")).toBeInTheDocument();
  expect(screen.getByLabelText("Filter by severity")).toBeInTheDocument();
  expect(screen.getByLabelText("Filter by category")).toBeInTheDocument();
});
