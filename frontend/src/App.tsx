import { useEffect, useState } from "react";
import { getCurrentUser, logout } from "./lib/api";
import type { User } from "./lib/types";
import { ReviewPage } from "./features/review/ReviewPage";
import "./App.css";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((response) => {
        if (active) setUser(response.user);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not check your sign-in status.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function signOut() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  if (loading)
    return (
      <main className="center-state" role="status">
        <span className="spinner" /> Checking your session…
      </main>
    );
  if (!user)
    return (
      <main className="auth-screen">
        <div className="auth-card">
          <a className="brand" href="#top">
            <span className="brand-mark">✳</span>
            <span>
              patchwork<span className="brand-period">.</span>
            </span>
          </a>
          <div className="auth-art" aria-hidden="true">
            <span>✳</span>
            <span>⌁</span>
            <span>↗</span>
          </div>
          <p className="eyebrow">A BETTER FIRST PASS</p>
          <h1>
            Review with
            <br />a little more clarity.
          </h1>
          <p className="welcome-lede">
            Connect GitHub to review public pull requests and start a grounded
            conversation about the changes.
          </p>
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          <a
            className="primary-button github-button"
            href={`${(import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, "") ?? ""}/api/auth/login`}
          >
            <span aria-hidden="true">◉</span> Continue with GitHub
          </a>
          <p className="auth-footnote">
            Your review data stays in this active session unless you choose to
            save it.
          </p>
        </div>
      </main>
    );
  return <ReviewPage onSignOut={signOut} login={user.login} userId={user.id} />;
}

export default App;
