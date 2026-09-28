import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";
import { PrivacyConsent } from "../src/components/PrivacyConsent";
import { ReviewForm } from "../src/features/review/ReviewForm";

vi.mock("../src/lib/api", () => ({ startReview: vi.fn() }));

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

it("discloses Google AI Studio processing before review consent", () => {
  const onChange = vi.fn();
  render(<PrivacyConsent accepted={false} onChange={onChange} />);
  expect(screen.getByText(/sent to Google AI Studio/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox"));
  expect(onChange).toHaveBeenCalledWith(true);
});

it("does not submit review code until privacy consent is accepted", async () => {
  const onError = vi.fn();
  render(
    <ReviewForm
      userId="github-user-1"
      onReview={vi.fn()}
      onBusyChange={vi.fn()}
      onError={onError}
      busy={false}
    />,
  );
  fireEvent.change(screen.getByLabelText(/pull request url/i), {
    target: { value: "https://github.com/example/project/pull/1" },
  });
  fireEvent.click(screen.getByRole("button", { name: /review changes/i }));
  const { startReview } = await import("../src/lib/api");
  expect(startReview).not.toHaveBeenCalled();
  await waitFor(() =>
    expect(onError).toHaveBeenCalledWith(
      expect.stringMatching(/accept the privacy notice/i),
    ),
  );
});

it("does not reuse one GitHub account's AI consent for another account", () => {
  localStorage.setItem("capstone-ai-consent:github-user-2", "accepted");
  render(
    <ReviewForm
      userId="github-user-1"
      onReview={vi.fn()}
      onBusyChange={vi.fn()}
      onError={vi.fn()}
      busy={false}
    />,
  );
  expect(screen.getByRole("checkbox")).not.toBeChecked();
});

it("surfaces review API failures and always clears the busy state", async () => {
  const onError = vi.fn();
  const onBusyChange = vi.fn();
  const { startReview } = await import("../src/lib/api");
  vi.mocked(startReview).mockRejectedValueOnce(
    new Error("Reviewer service unavailable."),
  );
  render(
    <ReviewForm
      userId="github-user-1"
      onReview={vi.fn()}
      onBusyChange={onBusyChange}
      onError={onError}
      busy={false}
    />,
  );
  fireEvent.change(screen.getByLabelText(/pull request url/i), {
    target: { value: "https://github.com/example/project/pull/1" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: /review changes/i }));
  await waitFor(() =>
    expect(onError).toHaveBeenCalledWith("Reviewer service unavailable."),
  );
  expect(onBusyChange).toHaveBeenNthCalledWith(1, true);
  expect(onBusyChange).toHaveBeenLastCalledWith(false);
});
