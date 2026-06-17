import { useEffect, useState, useCallback } from "react";
import InvestmentTerminal from "./components/InvestmentTerminal";
import Login from "./components/Login";
import Signup from "./components/Signup";

// ── Logout button styles ───────────────────────────────────────────────────
// Injected as a <style> tag so we never touch InvestmentTerminal's CSS block.
const LOGOUT_CSS = `
  .kly-logout-wrap {
    position: fixed;
    top: 0;
    right: 0;
    z-index: 500;
    padding: 18px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    pointer-events: none;   /* let clicks fall through to the nav beneath */
  }

  .kly-user-chip {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    color: #666666;
    text-transform: uppercase;
    pointer-events: none;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .kly-logout-btn {
    /* matches the terminal's design language: mono font, sharp corners,
       accent border — but deliberately compact so it doesn't crowd the nav */
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #666666;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.12);
    padding: 6px 14px;
    cursor: pointer;
    pointer-events: all;    /* re-enable clicks just for this button */
    transition: color 0.15s, border-color 0.15s;
    line-height: 1;
  }

  .kly-logout-btn:hover {
    color: #FF5A5A;
    border-color: rgba(255,90,90,0.45);
  }
`;

function LogoutOverlay({ onLogout }) {
  return (
    <>
      <style>{LOGOUT_CSS}</style>
      <div className="kly-logout-wrap">
        <button
          className="kly-logout-btn"
          onClick={onLogout}
          title="Sign out"
        >
          SIGN OUT
        </button>
      </div>
    </>
  );
}

export default function App() {
  // Initialise synchronously from localStorage so there's no flash.
  const [authed, setAuthed] = useState(() => !!localStorage.getItem("token"));
  const [authView, setAuthView] = useState(() =>
    window.location.hash === "#/signup" ? "signup" : "login"
  );
  const [loginNotice, setLoginNotice] = useState("");

  useEffect(() => {
    const onHashChange = () => {
      setAuthView(window.location.hash === "#/signup" ? "signup" : "login");
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const handleLogin = useCallback(() => {
    setAuthed(true);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("token");
    setAuthed(false);
  }, []);

  if (!authed) {
    if (authView === "signup") {
      return (
        <Signup
          onGoToLogin={() => { window.location.hash = "#/login"; }}
          onSignedUp={(msg) => {
            setLoginNotice(msg || "Account created. Please sign in.");
            window.location.hash = "#/login";
          }}
        />
      );
    }

    return (
      <Login
        onLogin={handleLogin}
        successMessage={loginNotice}
        onGoToSignup={() => { setLoginNotice(""); window.location.hash = "#/signup"; }}
        onClearSuccess={() => setLoginNotice("")}
      />
    );
  }

  return (
    <>
      <InvestmentTerminal />
      <LogoutOverlay onLogout={handleLogout} />
    </>
  );
}