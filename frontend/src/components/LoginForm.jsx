import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { authApi } from "../api/endpoints";
import { useAuth } from "../context/AuthContext.jsx";

export default function LoginForm({ onSwitchTab }) {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resendStatus, setResendStatus] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setNeedsVerification(false);
    setResendStatus(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      navigate(user.role === "specialist" ? "/specialist" : "/", { replace: true });
      if (user.role !== "specialist" && onSwitchTab) {
        onSwitchTab("search");
      }
    } catch (err) {
      const data = err.response?.data;
      if (data?.code === "unverified_email") {
        setNeedsVerification(true);
        setError(data.detail);
      } else {
        setError(data?.detail || "Incorrect email or password.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResendStatus("sending");
    try {
      await authApi.resendCode(email);
      setResendStatus("sent");
    } catch {
      setResendStatus("error");
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>Log in</h2>

      {error && (
        <div className="alert alert-error">
          {error}
          {needsVerification && (
            <div style={{ marginTop: 8 }}>
              <button
                type="button"
                className="link-button"
                onClick={handleResend}
                disabled={resendStatus === "sending"}
              >
                {resendStatus === "sending" ? "Sending…" : "Resend verification code"}
              </button>
              {resendStatus === "sent" && (
                <span style={{ marginLeft: 8 }}>Code sent. Check your email.</span>
              )}
            </div>
          )}
        </div>
      )}

      <div className="field">
        <label htmlFor="login-email">Email</label>
        <input
          id="login-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
      </div>

      <div className="field">
        <label htmlFor="login-password">Password</label>
        <input
          id="login-password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
      </div>

      <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
        {submitting ? "Signing in…" : "Log in"}
      </button>
    </form>
  );
}
