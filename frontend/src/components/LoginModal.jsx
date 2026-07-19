import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { authApi, errorCode, flattenApiErrors } from "../api/endpoints";
import { useAuth } from "../context/AuthContext.jsx";
import uz from "../i18n/uz.js";
import Modal from "./Modal.jsx";
import PasswordInput from "./PasswordInput.jsx";

export default function LoginModal({ onClose, onSwitchToRegister, prefillLogin = "" }) {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [loginValue, setLoginValue] = useState(prefillLogin);
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resendState, setResendState] = useState("idle");

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setNeedsVerification(false);
    setSubmitting(true);
    try {
      await login(loginValue, password);
      onClose();
      navigate("/dashboard");
    } catch (err) {
      const data = err.response?.data;
      const { generic } = flattenApiErrors(data);
      if (errorCode(data) === "unverified_email") {
        setNeedsVerification(true);
        setError(generic || uz.login.unverified);
      } else {
        setError(generic || uz.login.wrongCredentials);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResendState("sending");
    try {
      await authApi.resendCode(loginValue);
      setResendState("sent");
    } catch {
      setResendState("error");
    }
  }

  return (
    <Modal onClose={onClose} labelledBy="login-modal-title">
      <h2 id="login-modal-title" className="mb-5 text-2xl font-semibold text-ink">
        {uz.login.title}
      </h2>

      {error && (
        <div className="mb-4 rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
          {error}
          {needsVerification && (
            <div className="mt-2">
              <button
                type="button"
                className="text-sm font-medium text-sand-dark underline underline-offset-2"
                onClick={handleResend}
                disabled={resendState === "sending"}
              >
                {resendState === "sending" ? uz.login.resending : uz.login.resend}
              </button>
              {resendState === "sent" && (
                <span className="ml-2 text-xs">{uz.login.resent}</span>
              )}
            </div>
          )}
        </div>
      )}

      <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="login-login" className="text-sm font-medium text-ink-soft">
            {uz.login.loginLabel}
          </label>
          <input
            id="login-login"
            type="text"
            required
            value={loginValue}
            onChange={(e) => setLoginValue(e.target.value)}
            autoComplete="username"
            className="rounded-lg border border-line bg-paper px-3.5 py-2.5 text-ink transition focus:border-sand focus:bg-surface focus:outline-none"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="login-password" className="text-sm font-medium text-ink-soft">
            {uz.login.passwordLabel}
          </label>
          <PasswordInput
            id="login-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            className="rounded-lg border border-line bg-paper px-3.5 py-2.5 text-ink transition focus:border-sand focus:bg-surface focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="mt-1 w-full rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
        >
          {submitting ? uz.login.submitting : uz.login.submit}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-ink-soft">
        {uz.common.register}?{" "}
        <button
          type="button"
          className="font-medium text-sand-dark underline underline-offset-2"
          onClick={onSwitchToRegister}
        >
          {uz.common.register}
        </button>
      </p>
    </Modal>
  );
}
