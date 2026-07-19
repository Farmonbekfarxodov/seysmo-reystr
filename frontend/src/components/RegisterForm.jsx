import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ACADEMIC_TITLES, authApi } from "../api/endpoints";

const MAX_FILES = 5;
const MAX_FILE_MB = 5;
const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"];

const initialForm = {
  last_name: "",
  first_name: "",
  patronymic: "",
  email: "",
  password: "",
  password_confirm: "",
  role: "regular",
  academic_title: "",
  direction: "",
};

export default function RegisterForm() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState([]);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function validateClientSide() {
    const errors = {};
    if (!form.last_name.trim()) errors.last_name = "Surname is required.";
    if (!form.first_name.trim()) errors.first_name = "Name is required.";
    if (!form.email.trim()) errors.email = "Email is required.";
    if (form.password.length < 8) errors.password = "Password must be at least 8 characters.";
    if (form.password !== form.password_confirm) {
      errors.password_confirm = "Passwords do not match.";
    }
    if (form.role === "specialist") {
      if (!form.academic_title) errors.academic_title = "Choose an academic title.";
      if (!form.direction.trim()) errors.direction = "Direction is required.";
    }
    return errors;
  }

  function handleFileSelect(e) {
    const selected = Array.from(e.target.files || []);
    const combined = [...files, ...selected];

    if (combined.length > MAX_FILES) {
      setFormError(`You can upload at most ${MAX_FILES} files.`);
      return;
    }
    for (const file of combined) {
      const ext = file.name.split(".").pop().toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setFormError(`"${file.name}" must be a PDF, JPG, or PNG file.`);
        return;
      }
      if (file.size > MAX_FILE_MB * 1024 * 1024) {
        setFormError(`"${file.name}" exceeds the ${MAX_FILE_MB} MB limit.`);
        return;
      }
    }
    setFormError(null);
    setFiles(combined);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError(null);

    const errors = validateClientSide();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await authApi.register({ ...form, documents: files });
      navigate("/verify-email", { state: { email: form.email } });
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === "object") {
        const serverErrors = {};
        let generic = null;
        Object.entries(data).forEach(([key, val]) => {
          const message = Array.isArray(val) ? val.join(" ") : String(val);
          if (key in initialForm) {
            serverErrors[key] = message;
          } else {
            generic = message;
          }
        });
        setFieldErrors(serverErrors);
        setFormError(generic || (Object.keys(serverErrors).length ? null : "Registration failed."));
      } else {
        setFormError("Registration failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      <h2>Create an account</h2>

      {formError && <div className="alert alert-error">{formError}</div>}

      <div className="role-toggle" role="radiogroup" aria-label="Account type">
        <button
          type="button"
          className={`role-option ${form.role === "regular" ? "active" : ""}`}
          onClick={() => update("role", "regular")}
        >
          Regular user
        </button>
        <button
          type="button"
          className={`role-option ${form.role === "specialist" ? "active" : ""}`}
          onClick={() => update("role", "specialist")}
        >
          Specialist
        </button>
      </div>

      <div className="form-row">
        <div className="field">
          <label htmlFor="reg-last-name">Surname</label>
          <input
            id="reg-last-name"
            value={form.last_name}
            onChange={(e) => update("last_name", e.target.value)}
          />
          {fieldErrors.last_name && <span className="field-error">{fieldErrors.last_name}</span>}
        </div>
        <div className="field">
          <label htmlFor="reg-first-name">Name</label>
          <input
            id="reg-first-name"
            value={form.first_name}
            onChange={(e) => update("first_name", e.target.value)}
          />
          {fieldErrors.first_name && <span className="field-error">{fieldErrors.first_name}</span>}
        </div>
      </div>

      <div className="field">
        <label htmlFor="reg-patronymic">Patronymic (optional)</label>
        <input
          id="reg-patronymic"
          value={form.patronymic}
          onChange={(e) => update("patronymic", e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="reg-email">Email</label>
        <input
          id="reg-email"
          type="email"
          value={form.email}
          onChange={(e) => update("email", e.target.value)}
          autoComplete="email"
        />
        {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
      </div>

      <div className="form-row">
        <div className="field">
          <label htmlFor="reg-password">Password</label>
          <input
            id="reg-password"
            type="password"
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            autoComplete="new-password"
          />
          {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
        </div>
        <div className="field">
          <label htmlFor="reg-password-confirm">Confirm password</label>
          <input
            id="reg-password-confirm"
            type="password"
            value={form.password_confirm}
            onChange={(e) => update("password_confirm", e.target.value)}
            autoComplete="new-password"
          />
          {fieldErrors.password_confirm && (
            <span className="field-error">{fieldErrors.password_confirm}</span>
          )}
        </div>
      </div>

      {form.role === "specialist" && (
        <>
          <div className="form-row">
            <div className="field">
              <label htmlFor="reg-title">Academic title</label>
              <select
                id="reg-title"
                value={form.academic_title}
                onChange={(e) => update("academic_title", e.target.value)}
              >
                <option value="">Select…</option>
                {ACADEMIC_TITLES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
              {fieldErrors.academic_title && (
                <span className="field-error">{fieldErrors.academic_title}</span>
              )}
            </div>
            <div className="field">
              <label htmlFor="reg-direction">Direction / specialization</label>
              <input
                id="reg-direction"
                placeholder="e.g. Cardiology"
                value={form.direction}
                onChange={(e) => update("direction", e.target.value)}
              />
              {fieldErrors.direction && <span className="field-error">{fieldErrors.direction}</span>}
            </div>
          </div>

          <div className="field">
            <label>Credential documents (optional at signup)</label>
            <label className="file-drop">
              PDF, JPG, or PNG · up to {MAX_FILE_MB} MB each · up to {MAX_FILES} files
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                multiple
                onChange={handleFileSelect}
                style={{ display: "none" }}
              />
            </label>
            {files.length > 0 && (
              <ul className="file-list">
                {files.map((f, i) => (
                  <li key={`${f.name}-${i}`}>
                    <span>{f.name}</span>
                    <button type="button" onClick={() => removeFile(i)}>
                      remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}

      <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
        {submitting ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
