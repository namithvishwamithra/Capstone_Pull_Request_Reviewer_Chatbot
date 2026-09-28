import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ChatPanel } from "../src/features/chat/ChatPanel";
import { streamChat } from "../src/features/chat/chatApi";
import type { Review } from "../src/lib/types";

vi.mock("../src/features/chat/chatApi", () => ({ streamChat: vi.fn() }));

const review: Review = {
  id: "r1",
  title: "Example",
  summary: "Summary",
  findings: [],
  changed_files: [],
  excluded_files: [],
  processed_changed_lines: 0,
};

it("explains that chat answers use the current review context", () => {
  render(<ChatPanel review={review} />);
  expect(
    screen.getByText(/use this review's diff and findings/i),
  ).toBeInTheDocument();
});

it("marks partial assistant output incomplete when the stream fails", async () => {
  vi.mocked(streamChat).mockImplementation(async (_id, _message, onToken) => {
    onToken("partial answer");
    throw new Error("The chat response was interrupted before it completed.");
  });
  render(<ChatPanel review={review} />);
  fireEvent.change(screen.getByLabelText(/ask a question about the review/i), {
    target: { value: "Why is this risky?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
  await waitFor(() =>
    expect(screen.getByText(/incomplete response/i)).toBeInTheDocument(),
  );
  expect(screen.getByText("partial answer")).toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent(/interrupted/i);
});

it("cancels a pending stream when the user selects Stop", async () => {
  vi.mocked(streamChat).mockImplementation(
    (_id, _message, _onToken, signal) =>
      new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        );
      }),
  );
  render(<ChatPanel review={review} />);
  fireEvent.change(screen.getByLabelText(/ask a question about the review/i), {
    target: { value: "Explain the change" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
  fireEvent.click(await screen.findByRole("button", { name: "Stop" }));
  await waitFor(() =>
    expect(screen.getByText(/incomplete response/i)).toBeInTheDocument(),
  );
  const signal = vi.mocked(streamChat).mock.calls[0][3];
  expect(signal.aborted).toBe(true);
});
