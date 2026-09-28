import { afterEach, vi } from "vitest";
import { ApiError, streamChat } from "../src/lib/api";

afterEach(() => vi.unstubAllGlobals());

it("marks a truncated SSE stream as incomplete instead of successful", async () => {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(
        encoder.encode('data: {"type":"token","text":"partial"}\n\n'),
      );
      controller.close();
    },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(body, { status: 200 })),
  );
  const tokens: string[] = [];
  await expect(
    streamChat(
      "review-1",
      "question",
      (text) => tokens.push(text),
      new AbortController().signal,
    ),
  ).rejects.toBeInstanceOf(ApiError);
  expect(tokens).toEqual(["partial"]);
});

it("continues only after an explicit done event", async () => {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(
        encoder.encode('data: {"type":"token","text":"grounded"}\n\n'),
      );
      controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
      controller.close();
    },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(body, { status: 200 })),
  );
  const tokens: string[] = [];
  await streamChat(
    "review-1",
    "question",
    (text) => tokens.push(text),
    new AbortController().signal,
  );
  expect(tokens).toEqual(["grounded"]);
});
