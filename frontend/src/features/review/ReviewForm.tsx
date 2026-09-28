import { useState, type FormEvent } from "react";
import { PrivacyConsent } from "../../components/PrivacyConsent";
import type { Review } from "../../lib/types";
import { requestReview } from "./reviewApi";

interface ReviewFormProps {
  userId: string;
  onReview: (review: Review) => void;
  onBusyChange: (busy: boolean) => void;
  onError: (message: string) => void;
  busy: boolean;
}

export function ReviewForm({
  userId,
  onReview,
  onBusyChange,
  onError,
  busy,
}: ReviewFormProps) {
  const [source, setSource] = useState<"url" | "diff">("url");
  const [prUrl, setPrUrl] = useState("");
  const [diff, setDiff] = useState("");
  const [consent, setConsent] = useState(
    () => localStorage.getItem(`capstone-ai-consent:${userId}`) === "accepted",
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onError("");
    if (busy) return;
    if (!consent) {
      onError(
        "Please review and accept the privacy notice before starting a review.",
      );
      return;
    }
    onBusyChange(true);
    try {
      const result = await requestReview({
        ...(source === "url"
          ? { pr_url: prUrl.trim() }
          : { diff: diff.trim() }),
        consent_to_ai_processing: true,
      });
      localStorage.setItem(`capstone-ai-consent:${userId}`, "accepted");
      onReview(result);
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "The review could not be completed. Please retry.",
      );
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <form className="review-form" onSubmit={submit}>
      <div
        className="source-tabs"
        role="tablist"
        aria-label="Review input type"
      >
        <button
          type="button"
          role="tab"
          aria-selected={source === "url"}
          onClick={() => setSource("url")}
        >
          GitHub pull request
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={source === "diff"}
          onClick={() => setSource("diff")}
        >
          Paste a diff
        </button>
      </div>
      {source === "url" ? (
        <label className="field-label" htmlFor="pr-url">
          Pull request URL
          <input
            id="pr-url"
            type="url"
            autoComplete="url"
            placeholder="https://github.com/owner/repo/pull/123"
            value={prUrl}
            onChange={(event) => setPrUrl(event.target.value)}
            required
          />
          <small>
            Public GitHub pull requests are supported with the current minimal
            OAuth permissions.
          </small>
        </label>
      ) : (
        <label className="field-label" htmlFor="review-diff">
          Unified diff
          <textarea
            id="review-diff"
            className="diff-input"
            placeholder={
              "Paste a unified diff…\n\n--- a/src/example.ts\n+++ b/src/example.ts"
            }
            value={diff}
            onChange={(event) => setDiff(event.target.value)}
            required
          />
          <small>
            Maximum input: 1,000 changed lines. Lockfiles and generated files
            are skipped.
          </small>
        </label>
      )}
      <PrivacyConsent accepted={consent} onChange={setConsent} />
      <button
        className="primary-button review-button"
        type="submit"
        disabled={busy}
      >
        {busy ? (
          <span className="spinner" aria-hidden="true" />
        ) : (
          <span aria-hidden="true">✳</span>
        )}
        {busy ? "Reviewing changes…" : "Review changes"}
      </button>
    </form>
  );
}
