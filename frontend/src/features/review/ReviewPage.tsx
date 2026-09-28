import { useState } from "react";
import type { Review } from "../../lib/types";
import { ChatPanel } from "../chat/ChatPanel";
import { ReviewForm } from "./ReviewForm";
import { ReviewResults } from "./ReviewResults";
import { endActiveSession } from "./reviewApi";

interface ReviewPageProps {
  onSignOut: () => void;
  login: string;
  userId: string;
}

export function ReviewPage({ onSignOut, login, userId }: ReviewPageProps) {
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function startOver() {
    try {
      await endActiveSession();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not clear the active review session.",
      );
      return;
    }
    setReview(null);
    setError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Patchwork home">
          <span className="brand-mark">✳</span>
          <span>
            patchwork<span className="brand-period">.</span>
          </span>
        </a>
        <nav className="top-actions" aria-label="Account">
          <span className="account-chip">
            <span className="online-dot" aria-hidden="true" />
            {login}
          </span>
          <button
            type="button"
            className="icon-button"
            onClick={onSignOut}
            aria-label="Sign out"
            title="Sign out"
          >
            ↗
          </button>
        </nav>
      </header>
      <main id="top" className="main-content">
        {!review ? (
          <section className="welcome-layout">
            <div className="welcome-copy">
              <p className="eyebrow">
                <span className="eyebrow-star">✳</span> YOUR THOUGHTFUL REVIEW
                PARTNER
              </p>
              <h1>
                Ship with
                <br />
                <span>more confidence.</span>
              </h1>
              <p className="welcome-lede">
                A calmer first pass for your pull request. Find the important
                things, understand the why, and keep the conversation close to
                the code.
              </p>
              <div className="trust-points">
                <span>
                  <b>01</b> Grounded in your diff
                </span>
                <span>
                  <b>02</b> Private by default
                </span>
                <span>
                  <b>03</b> You stay in control
                </span>
              </div>
            </div>
            <section
              className="review-card"
              aria-labelledby="start-review-heading"
            >
              <div className="card-heading">
                <span className="card-icon" aria-hidden="true">
                  ⌘
                </span>
                <div>
                  <p className="eyebrow">START A REVIEW</p>
                  <h2 id="start-review-heading">What are we looking at?</h2>
                </div>
              </div>
              {error && (
                <p className="inline-error" role="alert">
                  {error}
                </p>
              )}
              <ReviewForm
                userId={userId}
                onReview={setReview}
                onBusyChange={setBusy}
                onError={setError}
                busy={busy}
              />
              {busy && (
                <div className="progress-state" role="status">
                  <span className="spinner" /> Reading the changes and preparing
                  your review…
                </div>
              )}
              <p className="size-note">
                Up to 1,000 changed lines <span>·</span> GitHub only{" "}
                <span>·</span> No code execution
              </p>
            </section>
          </section>
        ) : (
          <>
            <ReviewResults review={review} onStartOver={startOver} />
            <ChatPanel key={review.id} review={review} />
          </>
        )}
      </main>
      <footer className="footer">
        <span>Made for the careful reviewer.</span>
        <span>CAPSTONE · Human judgment stays in the loop</span>
      </footer>
    </div>
  );
}
