import { useMemo, useState } from "react";
import { API_BASE_URL } from "../config";


const css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap');

  .signup-root {
    min-height: 100vh;
    background: #050505;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Space Grotesk', sans-serif;
    position: relative;
    overflow: hidden;
  }

  .signup-grid-bg {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(223,255,47,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(223,255,47,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  .signup-radial {
    position: absolute;
    top: -20%;
    left: 50%;
    transform: translateX(-50%);
    width: 80vw;
    height: 80vw;
    background: radial-gradient(ellipse, rgba(223,255,47,0.05) 0%, transparent 60%);
    pointer-events: none;
  }

  .signup-card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 460px;
    padding: 0 24px;
  }

  .signup-wordmark {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 56px;
    color: #ffffff;
    letter-spacing: 4px;
    line-height: 1;
    margin-bottom: 4px;
    position: relative;
    display: inline-block;
  }

  .signup-wordmark::before {
    content: 'KLYSEARCH';
    position: absolute;
    inset: 0;
    color: #DFFF2F;
    clip-path: polygon(0 0, 100% 0, 100% 40%, 0 40%);
  }

  .signup-sub {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.22em;
    color: #666666;
    text-transform: uppercase;
    margin-bottom: 48px;
  }

  .signup-panel {
    background: #111111;
    border: 1px solid rgba(255,255,255,0.08);
    position: relative;
  }

  .signup-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: #DFFF2F;
  }

  .signup-panel-header {
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .signup-panel-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.22em;
    color: #DFFF2F;
    text-transform: uppercase;
  }

  .signup-panel-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #666666;
    letter-spacing: 0.1em;
  }

  .signup-status-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #65FF8A;
    box-shadow: 0 0 6px #65FF8A;
    animation: signup-pulse 2s ease-in-out infinite;
  }

  @keyframes signup-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .signup-form {
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .signup-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .signup-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.2em;
    color: #666666;
    text-transform: uppercase;
  }

  .signup-input {
    background: #0a0a0a;
    border: 1px solid rgba(255,255,255,0.1);
    color: #ffffff;
    font-family: 'Space Mono', monospace;
    font-size: 14px;
    padding: 14px 16px;
    outline: none;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s;
    letter-spacing: 0.04em;
  }

  .signup-input:focus { border-color: rgba(223,255,47,0.5); }
  .signup-input::placeholder { color: #333333; }
  .signup-input.error { border-color: rgba(255,90,90,0.5); }

  .signup-error {
    background: rgba(255,90,90,0.07);
    border: 1px solid rgba(255,90,90,0.3);
    border-left: 3px solid #FF5A5A;
    padding: 12px 16px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .signup-error-icon {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #FF5A5A;
    flex-shrink: 0;
    padding-top: 1px;
  }

  .signup-error-text {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #FF5A5A;
    line-height: 1.5;
    letter-spacing: 0.04em;
  }

  .signup-btn {
    background: #DFFF2F;
    color: #000000;
    border: none;
    padding: 16px 24px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    cursor: pointer;
    width: 100%;
    transition: opacity 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }

  .signup-btn:hover:not(:disabled) { opacity: 0.88; }
  .signup-btn:disabled { opacity: 0.45; cursor: not-allowed; }

  .signup-btn-spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(0,0,0,0.3);
    border-top-color: #000000;
    border-radius: 50%;
    animation: signup-spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  @keyframes signup-spin { to { transform: rotate(360deg); } }

  .signup-links {
    margin-top: 10px;
    display: flex;
    justify-content: center;
  }

  .signup-link {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: rgba(223,255,47,0.75);
    letter-spacing: 0.08em;
    text-decoration: none;
    cursor: pointer;
    user-select: none;
  }

  .signup-link:hover { text-decoration: underline; }

  .signup-footer {
    padding: 14px 24px;
    border-top: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .signup-footer-text {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #333333;
    letter-spacing: 0.1em;
  }

  .signup-footer-hint {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #DFFF2F;
    letter-spacing: 0.1em;
    opacity: 0.5;
  }
`;

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function normaliseBackendDetail(detail) {
  if (!detail) return "Signup failed.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(d => d?.msg || d?.message || String(d)).join(" ");
  if (typeof detail === "object") return detail?.message || JSON.stringify(detail);
  return String(detail);
}

export default function Signup({ onSignedUp, onGoToLogin }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const fieldErrors = useMemo(() => {
    const errs = {};
    if (error) return errs;
    return errs;
  }, [error]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Full name is required.");
      return;
    }
    if (!email.trim()) {
      setError("Email address is required.");
      return;
    }
    if (!isValidEmail(email.trim())) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!password.trim()) {
      setError("Password is required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      // Backend requires either organization_name or invite_code. We default to create-org mode.
      const res = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          organization_name: "Klysearch",
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(normaliseBackendDetail(data?.detail) || `Signup failed (${res.status}).`);
        return;
      }

      onSignedUp?.("Account created successfully. Please sign in.");
    } catch (err) {
      if (err?.name === "TypeError") {
        setError("Cannot reach the server. Please check your connection and ensure the backend is running.");
      } else {
        setError(err?.message || "An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{css}</style>
      <div className="signup-root">
        <div className="signup-grid-bg" />
        <div className="signup-radial" />

        <div className="signup-card">
          <div className="signup-wordmark">KLYSEARCH</div>
          <div className="signup-sub">Institutional Research Terminal</div>

          <div className="signup-panel">
            <div className="signup-panel-header">
              <span className="signup-panel-label">Operator Registration</span>
              <span className="signup-panel-status">
                <span className="signup-status-dot" />
                SECURE CHANNEL
              </span>
            </div>

            <form className="signup-form" onSubmit={handleSubmit} noValidate>
              <div className="signup-field">
                <label className="signup-label" htmlFor="name">Full Name</label>
                <input
                  id="name"
                  type="text"
                  className={`signup-input${error && !name ? " error" : ""}`}
                  placeholder="Ananya Bala"
                  value={name}
                  onChange={(e) => { setName(e.target.value); setError(""); }}
                  disabled={loading}
                  autoComplete="name"
                  autoFocus
                />
              </div>

              <div className="signup-field">
                <label className="signup-label" htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  className={`signup-input${error && !email ? " error" : ""}`}
                  placeholder="analyst@firm.com"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError(""); }}
                  disabled={loading}
                  autoComplete="email"
                />
              </div>

              <div className="signup-field">
                <label className="signup-label" htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  className={`signup-input${error && !password ? " error" : ""}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(""); }}
                  disabled={loading}
                  autoComplete="new-password"
                />
              </div>

              <div className="signup-field">
                <label className="signup-label" htmlFor="confirmPassword">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  className={`signup-input${error && !confirmPassword ? " error" : ""}`}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => { setConfirmPassword(e.target.value); setError(""); }}
                  disabled={loading}
                  autoComplete="new-password"
                />
              </div>

              {error && (
                <div className="signup-error" role="alert">
                  <span className="signup-error-icon">ERR</span>
                  <span className="signup-error-text">{error}</span>
                </div>
              )}

              <button type="submit" className="signup-btn" disabled={loading}>
                {loading && <span className="signup-btn-spinner" />}
                {loading ? "CREATING ACCOUNT..." : "CREATE ACCOUNT"}
              </button>

              <div className="signup-links">
                <span className="signup-link" onClick={onGoToLogin}>
                  Already have an account? Sign in
                </span>
              </div>
            </form>

            <div className="signup-footer">
              <span className="signup-footer-text">KLYSEARCH // v3.1 // GROQ AI</span>
              <span className="signup-footer-hint">[ENTER]</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

