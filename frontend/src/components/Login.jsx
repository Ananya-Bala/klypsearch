import { useState } from "react";

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap');

  .login-root {
    min-height: 100vh;
    background: #050505;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Space Grotesk', sans-serif;
    position: relative;
    overflow: hidden;
  }

  .login-grid-bg {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(223,255,47,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(223,255,47,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  .login-radial {
    position: absolute;
    top: -20%;
    left: 50%;
    transform: translateX(-50%);
    width: 80vw;
    height: 80vw;
    background: radial-gradient(ellipse, rgba(223,255,47,0.05) 0%, transparent 60%);
    pointer-events: none;
  }

  .login-card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 460px;
    padding: 0 24px;
  }

  .login-wordmark {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 56px;
    color: #ffffff;
    letter-spacing: 4px;
    line-height: 1;
    margin-bottom: 4px;
    position: relative;
    display: inline-block;
  }

  .login-wordmark::before {
    content: 'KLYSEARCH';
    position: absolute;
    inset: 0;
    color: #DFFF2F;
    clip-path: polygon(0 0, 100% 0, 100% 40%, 0 40%);
  }

  .login-sub {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.22em;
    color: #666666;
    text-transform: uppercase;
    margin-bottom: 48px;
  }

  .login-panel {
    background: #111111;
    border: 1px solid rgba(255,255,255,0.08);
    position: relative;
  }

  .login-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: #DFFF2F;
  }

  .login-panel-header {
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .login-panel-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.22em;
    color: #DFFF2F;
    text-transform: uppercase;
  }

  .login-panel-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #666666;
    letter-spacing: 0.1em;
  }

  .login-status-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #65FF8A;
    box-shadow: 0 0 6px #65FF8A;
    animation: login-pulse 2s ease-in-out infinite;
  }

  @keyframes login-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .login-form {
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .login-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .login-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.2em;
    color: #666666;
    text-transform: uppercase;
  }

  .login-input {
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

  .login-input:focus {
    border-color: rgba(223,255,47,0.5);
  }

  .login-input::placeholder {
    color: #333333;
  }

  .login-input.error {
    border-color: rgba(255,90,90,0.5);
  }

  .login-error {
    background: rgba(255,90,90,0.07);
    border: 1px solid rgba(255,90,90,0.3);
    border-left: 3px solid #FF5A5A;
    padding: 12px 16px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .login-error-icon {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #FF5A5A;
    flex-shrink: 0;
    padding-top: 1px;
  }

  .login-error-text {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #FF5A5A;
    line-height: 1.5;
    letter-spacing: 0.04em;
  }

  .login-success {
    background: rgba(101,255,138,0.07);
    border: 1px solid rgba(101,255,138,0.3);
    border-left: 3px solid #65FF8A;
    padding: 12px 16px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }

  .login-success-icon {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #65FF8A;
    flex-shrink: 0;
    padding-top: 1px;
  }

  .login-success-text {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #65FF8A;
    line-height: 1.5;
    letter-spacing: 0.04em;
  }

  .login-links {
    margin-top: 10px;
    display: flex;
    justify-content: center;
  }

  .login-link {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: rgba(223,255,47,0.75);
    letter-spacing: 0.08em;
    text-decoration: none;
    cursor: pointer;
    user-select: none;
  }

  .login-link:hover { text-decoration: underline; }

  .login-btn {
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
    position: relative;
    transition: opacity 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }

  .login-btn:hover:not(:disabled) { opacity: 0.88; }
  .login-btn:disabled { opacity: 0.45; cursor: not-allowed; }

  .login-btn-spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(0,0,0,0.3);
    border-top-color: #000000;
    border-radius: 50%;
    animation: login-spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  @keyframes login-spin {
    to { transform: rotate(360deg); }
  }

  .login-footer {
    padding: 14px 24px;
    border-top: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .login-footer-text {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #333333;
    letter-spacing: 0.1em;
  }

  .login-footer-hint {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #DFFF2F;
    letter-spacing: 0.1em;
    opacity: 0.5;
  }
`;

export default function Login({ onLogin, successMessage = "", onGoToSignup, onClearSuccess }) {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim())    { setError("Email address is required.");    return; }
    if (!password.trim()) { setError("Password is required."); return; }

    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/auth/login", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email: email.trim(), password }),
      });

      const data = await res.json();

      if (!res.ok) {
        // FastAPI returns { detail: "..." } on auth failure
        const msg = data?.detail || `Authentication failed (${res.status}).`;
        setError(msg);
        return;
      }

      if (!data.access_token) {
        setError("Server returned an unexpected response. Please try again.");
        return;
      }

      localStorage.setItem("token", data.access_token);
      onLogin();

    } catch (err) {
      if (err.name === "TypeError") {
        setError("Cannot reach the server. Is the backend running on port 8000?");
      } else {
        setError(err.message || "An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{css}</style>
      <div className="login-root">
        <div className="login-grid-bg" />
        <div className="login-radial" />

        <div className="login-card">
          <div className="login-wordmark">KLYSEARCH</div>
          <div className="login-sub">Institutional Research Terminal</div>

          <div className="login-panel">
            <div className="login-panel-header">
              <span className="login-panel-label">Operator Authentication</span>
              <span className="login-panel-status">
                <span className="login-status-dot" />
                SECURE CHANNEL
              </span>
            </div>

            <form className="login-form" onSubmit={handleSubmit} noValidate>
              <div className="login-field">
                <label className="login-label" htmlFor="email">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  className={`login-input${error && !email ? " error" : ""}`}
                  placeholder="analyst@firm.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setError("");
                    onClearSuccess?.();
                  }}
                  disabled={loading}
                  autoComplete="email"
                  autoFocus
                />
              </div>

              <div className="login-field">
                <label className="login-label" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  className={`login-input${error && !password ? " error" : ""}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError("");
                    onClearSuccess?.();
                  }}
                  disabled={loading}
                  autoComplete="current-password"
                />
              </div>

              {!!successMessage && !error && (
                <div className="login-success" role="status">
                  <span className="login-success-icon">OK</span>
                  <span className="login-success-text">{successMessage}</span>
                </div>
              )}

              {error && (
                <div className="login-error" role="alert">
                  <span className="login-error-icon">ERR</span>
                  <span className="login-error-text">{error}</span>
                </div>
              )}

              <button type="submit" className="login-btn" disabled={loading}>
                {loading && <span className="login-btn-spinner" />}
                {loading ? "AUTHENTICATING..." : "ACCESS TERMINAL"}
              </button>

              <div className="login-links">
                <span className="login-link" onClick={onGoToSignup}>
                  Don't have an account? Create one
                </span>
              </div>
            </form>

            <div className="login-footer">
              <span className="login-footer-text">
                KLYSEARCH // v3.1 // GROQ AI
              </span>
              <span className="login-footer-hint">[ENTER]</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
