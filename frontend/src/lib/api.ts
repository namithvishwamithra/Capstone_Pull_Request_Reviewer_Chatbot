import type { AuthResponse, Review } from "./types";

const apiOrigin =
  (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, "") ??
  "";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiOrigin}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "fetch",
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Could not connect to the reviewer service. Check your connection and retry.",
      0,
    );
  }
  if (!response.ok) {
    let message =
      response.status === 502
        ? "The reviewer API is unavailable. Start the backend and try again."
        : "The request could not be completed. Please retry.";
    try {
      const body = (await response.json()) as {
        detail?: { message?: string } | string;
      };
      if (typeof body.detail === "object" && body.detail?.message)
        message = body.detail.message;
      else if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Keep the safe generic message if the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

export const getCurrentUser = () => request<AuthResponse>("/api/auth/me");
export const logout = () =>
  request<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
export const endActiveSession = () =>
  request<{ ok: boolean }>("/api/reviews/active", { method: "DELETE" });

export function startReview(input: {
  pr_url?: string;
  diff?: string;
  consent_to_ai_processing: boolean;
}) {
  return request<Review>("/api/reviews", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getReview(id: string) {
  return request<Review>(`/api/reviews/${encodeURIComponent(id)}`);
}

export async function streamChat(
  reviewId: string,
  message: string,
  onToken: (text: string) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(
    `${apiOrigin}/api/reviews/${encodeURIComponent(reviewId)}/chat`,
    {
      method: "POST",
      credentials: "include",
      signal,
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "fetch",
      },
      body: JSON.stringify({ message }),
    },
  );
  if (!response.ok || !response.body) {
    throw new ApiError(
      "The chat request failed. Please retry.",
      response.status,
    );
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  let completed = false;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    pending += decoder.decode(value, { stream: true });
    const frames = pending.split(/\r?\n\r?\n/);
    pending = frames.pop() ?? "";
    for (const frame of frames) {
      const data = frame
        .split(/\r?\n/)
        .find((line) => line.startsWith("data:"))
        ?.slice(5)
        .trim();
      if (!data) continue;
      const event = JSON.parse(data) as {
        type: string;
        text?: string;
        message?: string;
      };
      if (event.type === "token" && event.text) onToken(event.text);
      if (event.type === "done") completed = true;
      if (event.type === "error")
        throw new ApiError(
          event.message ?? "The chat response was interrupted.",
          502,
        );
    }
  }
  if (!completed)
    throw new ApiError(
      "The chat response was interrupted before it completed.",
      502,
    );
}
