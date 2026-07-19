import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import CodeVerification from "../components/CodeVerification.jsx";

export default function VerifyEmailPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState(location.state?.email || "");
  const [confirmedEmail, setConfirmedEmail] = useState(location.state?.email || "");

  if (!confirmedEmail) {
    return (
      <div className="drawer" style={{ maxWidth: 480 }}>
        <div className="drawer-panel">
          <form
            className="form"
            onSubmit={(e) => {
              e.preventDefault();
              setConfirmedEmail(email);
            }}
          >
            <h2>Verify your email</h2>
            <p>Enter the email address you registered with.</p>
            <div className="field">
              <label htmlFor="verify-email-input">Email</label>
              <input
                id="verify-email-input"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block">
              Continue
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="drawer" style={{ maxWidth: 480 }}>
      <div className="drawer-panel">
        <CodeVerification
          email={confirmedEmail}
          onVerified={() => {
            setTimeout(() => navigate("/", { state: { activeTab: "login" } }), 1200);
          }}
        />
        <hr className="divider" />
        <Link to="/">← Back to home</Link>
      </div>
    </div>
  );
}
