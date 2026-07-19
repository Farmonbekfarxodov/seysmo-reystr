import React, { useEffect, useRef, useState } from "react";

import { authApi } from "../api/endpoints";

const CODE_LENGTH = 6;
const RESEND_COOLDOWN = 60;

export default function CodeVerification({ email, onVerified }) {
  const [digits, setDigits] = useState(Array(CODE_LENGTH).fill(""));
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [resendState, setResendState] = useState("idle"); // idle | sending | sent | error
  const inputsRef = useRef([]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => Math.max(c - 1, 0)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  function handleDigitChange(index, value) {
    const clean = value.replace(/[^0-9]/g, "").slice(-1);
    const next = [...digits];
    next[index] = clean;
    setDigits(next);
    if (clean && index < CODE_LENGTH - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  }

  function handleKeyDown(index, e) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  }

  function handlePaste(e) {
    const pasted = e.clipboardData.getData("text").replace(/[^0-9]/g, "").slice(0, CODE_LENGTH);
    if (!pasted) return;
    e.preventDefault();
    setDigits(pasted.split("").concat(Array(CODE_LENGTH).fill("")).slice(0, CODE_LENGTH));
    inputsRef.current[Math.min(pasted.length, CODE_LENGTH - 1)]?.focus();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const code = digits.join("");
    if (code.length !== CODE_LENGTH) {
      setError("Enter all 6 digits.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await authApi.verifyEmail(email, code);
      setSuccess(true);
      onVerified?.();
    } catch (err) {
      const data = err.response?.data;
      setError(data?.non_field_errors?.[0] || data?.detail || "Verification failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResendState("sending");
    setError(null);
    try {
      await authApi.resendCode(email);
      setResendState("sent");
      setCooldown(RESEND_COOLDOWN);
    } catch (err) {
      setResendState("error");
      setError(err.response?.data?.email?.[0] || "Could not resend the code yet.");
    }
  }

  if (success) {
    return (
      <div className="alert alert-success">
        Email verified! You can now log in with your email and password.
      </div>
    );
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>Verify your email</h2>
      <p>
        We sent a 6-digit code to <strong>{email}</strong>. It expires in 15 minutes.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="code-input-group" onPaste={handlePaste}>
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => (inputsRef.current[i] = el)}
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleDigitChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            aria-label={`Digit ${i + 1}`}
          />
        ))}
      </div>

      <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
        {submitting ? "Verifying…" : "Verify"}
      </button>

      <button
        type="button"
        className="link-button"
        onClick={handleResend}
        disabled={cooldown > 0 || resendState === "sending"}
      >
        {cooldown > 0
          ? `Resend code in ${cooldown}s`
          : resendState === "sending"
          ? "Sending…"
          : "Resend code"}
      </button>
      {resendState === "sent" && cooldown === RESEND_COOLDOWN && (
        <span className="hint">A new code is on its way.</span>
      )}
    </form>
  );
}
