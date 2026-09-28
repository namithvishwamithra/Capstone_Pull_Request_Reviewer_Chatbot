import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { expect } from "vitest";
import { ChatPanel } from "../src/features/chat/ChatPanel";
import { FindingsFilters } from "../src/features/review/FindingsFilters";
import { ReviewForm } from "../src/features/review/ReviewForm";
import type { Finding, Review } from "../src/lib/types";

expect.extend(toHaveNoViolations);

const finding: Finding = {
  severity: "major",
  category: "security",
  file: "src/auth.py",
  line_start: 8,
  line_end: 8,
  title: "Missing permission check",
  explanation: "A caller can access another account.",
  suggested_fix: "Check ownership before returning data.",
};
const review: Review = {
  id: "review-a11y",
  title: "Authorization update",
  summary: "Adds an ownership check.",
  findings: [finding],
  changed_files: ["src/auth.py"],
  excluded_files: [],
  processed_changed_lines: 1,
};

it("exposes labeled, keyboard-operable finding filters without axe violations", async () => {
  const { container } = render(
    <FindingsFilters
      findings={[finding]}
      selectedId={null}
      onSelect={() => undefined}
    />,
  );
  expect(screen.getByLabelText("Filter by severity")).toBeInTheDocument();
  expect(screen.getByLabelText("Filter by category")).toBeInTheDocument();
  expect(await axe(container)).toHaveNoViolations();
});

it("provides an accessible name for the chat input and controls", async () => {
  const { container } = render(<ChatPanel review={review} />);
  expect(
    screen.getByRole("textbox", { name: /ask a question about the review/i }),
  ).toBeInTheDocument();
  expect(await axe(container)).toHaveNoViolations();
});

it("keeps review input and privacy-consent controls accessible", async () => {
  const { container } = render(
    <ReviewForm
      userId="accessibility-test-user"
      onReview={() => undefined}
      onBusyChange={() => undefined}
      onError={() => undefined}
      busy={false}
    />,
  );
  expect(screen.getByLabelText(/pull request url/i)).toBeInTheDocument();
  expect(screen.getByRole("checkbox")).toHaveAccessibleName(/privacy notice/i);
  expect(await axe(container)).toHaveNoViolations();
});
