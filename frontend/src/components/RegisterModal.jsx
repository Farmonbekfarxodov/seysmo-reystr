import React, { useEffect, useRef, useState } from "react";

import {
  ACADEMIC_DEGREES,
  ACADEMIC_TITLES,
  authApi,
  departmentsApi,
  flattenApiErrors,
  POSITIONS,
} from "../api/endpoints";
import uz from "../i18n/uz.js";
import Modal from "./Modal.jsx";
import PasswordInput from "./PasswordInput.jsx";

const MAX_PHOTO_MB = 5;
const ALLOWED_PHOTO_EXT = ["jpg", "jpeg", "png"];
const CODE_LENGTH = 6;
const RESEND_COOLDOWN = 60;

const initialForm = {
  last_name: "",
  first_name: "",
  patronymic: "",
  email: "",
  username: "",
  password: "",
  password_confirm: "",
  academic_degree: "none",
  academic_title: "none",
  position: "",
  department: "",
  research_interests: "",
};

function initials(first, last) {
  return `${(first || "?").charAt(0)}${(last || "").charAt(0)}`.toUpperCase();
}

export default function RegisterModal({ onClose, onSwitchToLogin }) {
  const [step, setStep] = useState(1);
  const [departments, setDepartments] = useState([]);

  const [form, setForm] = useState(initialForm);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const photoInputRef = useRef(null);

  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [digits, setDigits] = useState(Array(CODE_LENGTH).fill(""));
  const [verifyError, setVerifyError] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [resendState, setResendState] = useState("idle");
  const codeInputsRef = useRef([]);

  useEffect(() => {
    departmentsApi.list().then((res) => setDepartments(res.data)).catch(() => setDepartments([]));
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => Math.max(c - 1, 0)), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handlePhotoSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_PHOTO_EXT.includes(ext)) {
      setFormError("Profil rasmi JPG yoki PNG bo'lishi kerak.");
      return;
    }
    if (file.size > MAX_PHOTO_MB * 1024 * 1024) {
      setFormError(`Profil rasmi ${MAX_PHOTO_MB} MB chegarasidan katta.`);
      return;
    }
    setFormError(null);
    setPhotoFile(file);
    const reader = new FileReader();
    reader.onload = () => setPhotoPreview(reader.result);
    reader.readAsDataURL(file);
  }

  function removePhoto() {
    setPhotoFile(null);
    setPhotoPreview(null);
    if (photoInputRef.current) photoInputRef.current.value = "";
  }

  function validateClientSide() {
    const errors = {};
    if (!form.last_name.trim()) errors.last_name = "Familiya kiritilishi shart.";
    if (!form.first_name.trim()) errors.first_name = "Ism kiritilishi shart.";
    if (!form.email.trim()) errors.email = "Email kiritilishi shart.";
    if (!form.username.trim()) errors.username = "Foydalanuvchi nomi kiritilishi shart.";
    if (form.password.length < 8) errors.password = "Parol kamida 8 belgidan iborat bo'lishi kerak.";
    if (form.password !== form.password_confirm) errors.password_confirm = "Parollar mos kelmadi.";
    if (!form.department) errors.department = "Bo'limni tanlang.";
    return errors;
  }

  async function handleSubmitForm(e) {
    e.preventDefault();
    setFormError(null);

    const errors = validateClientSide();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await authApi.register({ ...form, photo: photoFile });
      setStep(2);
    } catch (err) {
      const { fieldErrors: serverErrors, generic } = flattenApiErrors(err.response?.data);
      setFieldErrors(serverErrors);
      setFormError(generic);
    } finally {
      setSubmitting(false);
    }
  }

  function handleDigitChange(index, value) {
    const clean = value.replace(/[^0-9]/g, "").slice(-1);
    const next = [...digits];
    next[index] = clean;
    setDigits(next);
    if (clean && index < CODE_LENGTH - 1) codeInputsRef.current[index + 1]?.focus();
  }

  function handleDigitKeyDown(index, e) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      codeInputsRef.current[index - 1]?.focus();
    }
  }

  function handleCodePaste(e) {
    const pasted = e.clipboardData.getData("text").replace(/[^0-9]/g, "").slice(0, CODE_LENGTH);
    if (!pasted) return;
    e.preventDefault();
    setDigits(pasted.split("").concat(Array(CODE_LENGTH).fill("")).slice(0, CODE_LENGTH));
    codeInputsRef.current[Math.min(pasted.length, CODE_LENGTH - 1)]?.focus();
  }

  async function handleVerify(e) {
    e.preventDefault();
    const code = digits.join("");
    if (code.length !== CODE_LENGTH) {
      setVerifyError("6 ta raqamni to'liq kiriting.");
      return;
    }
    setVerifyError(null);
    setVerifying(true);
    try {
      await authApi.verifyEmail(form.email, code);
      setStep(3);
    } catch (err) {
      const { generic } = flattenApiErrors(err.response?.data);
      setVerifyError(generic || "Tasdiqlash muvaffaqiyatsiz.");
    } finally {
      setVerifying(false);
    }
  }

  async function handleResend() {
    setResendState("sending");
    setVerifyError(null);
    try {
      await authApi.resendCode(form.email);
      setResendState("sent");
      setCooldown(RESEND_COOLDOWN);
    } catch (err) {
      setResendState("error");
      const { fieldErrors: e } = flattenApiErrors(err.response?.data);
      setVerifyError(e.email || "Kodni hozircha qayta yuborib bo'lmaydi.");
    }
  }

  const inputClass =
    "rounded-lg border border-line bg-paper px-3.5 py-2.5 text-ink transition focus:border-sand focus:bg-surface focus:outline-none";
  const labelClass = "text-sm font-medium text-ink-soft";

  return (
    <Modal onClose={onClose} wide labelledBy="register-modal-title">
      <div className="mb-5 flex gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className={`h-1 flex-1 rounded-full ${step >= s ? "bg-sand" : "bg-line"}`} />
        ))}
      </div>

      {step === 1 && (
        <>
          <h2 id="register-modal-title" className="mb-5 text-2xl font-semibold text-ink">
            {uz.register.title}
          </h2>
          {formError && (
            <div className="mb-4 rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
              {formError}
            </div>
          )}

          <form className="flex flex-col gap-4" onSubmit={handleSubmitForm} noValidate>
            <div className="flex flex-col items-center gap-2">
              <div className="relative h-24 w-24">
                <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2 border-line bg-sand-tint text-2xl font-semibold text-sand-dark">
                  {photoPreview ? (
                    <img src={photoPreview} alt="" className="h-full w-full object-cover" />
                  ) : (
                    initials(form.first_name, form.last_name)
                  )}
                </div>
              </div>
              <div className="flex gap-3 text-sm">
                <label className="cursor-pointer font-medium text-sand-dark underline underline-offset-2">
                  {photoPreview ? uz.common.replace : uz.register.photo}
                  <input
                    ref={photoInputRef}
                    type="file"
                    accept=".jpg,.jpeg,.png"
                    onChange={handlePhotoSelect}
                    className="hidden"
                  />
                </label>
                {photoPreview && (
                  <button type="button" onClick={removePhoto} className="font-medium text-danger underline underline-offset-2">
                    {uz.common.remove}
                  </button>
                )}
              </div>
              <p className="text-xs text-ink-faint">
                {uz.register.photoHint} · ({uz.common.optional})
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-last-name" className={labelClass}>{uz.register.lastName}</label>
                <input id="reg-last-name" className={inputClass} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} />
                {fieldErrors.last_name && <span className="text-xs text-danger">{fieldErrors.last_name}</span>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-first-name" className={labelClass}>{uz.register.firstName}</label>
                <input id="reg-first-name" className={inputClass} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} />
                {fieldErrors.first_name && <span className="text-xs text-danger">{fieldErrors.first_name}</span>}
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="reg-patronymic" className={labelClass}>
                {uz.register.patronymic} <span className="text-ink-faint">({uz.common.optional})</span>
              </label>
              <input id="reg-patronymic" className={inputClass} value={form.patronymic} onChange={(e) => update("patronymic", e.target.value)} />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-email" className={labelClass}>{uz.register.email}</label>
                <input id="reg-email" type="email" className={inputClass} value={form.email} onChange={(e) => update("email", e.target.value)} autoComplete="email" />
                {fieldErrors.email && <span className="text-xs text-danger">{fieldErrors.email}</span>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-username" className={labelClass}>{uz.register.username}</label>
                <input id="reg-username" className={inputClass} value={form.username} onChange={(e) => update("username", e.target.value)} autoComplete="username" />
                {fieldErrors.username && <span className="text-xs text-danger">{fieldErrors.username}</span>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-password" className={labelClass}>{uz.register.password}</label>
                <PasswordInput id="reg-password" className={inputClass} value={form.password} onChange={(e) => update("password", e.target.value)} autoComplete="new-password" />
                {fieldErrors.password && <span className="text-xs text-danger">{fieldErrors.password}</span>}
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-password-confirm" className={labelClass}>{uz.register.passwordConfirm}</label>
                <PasswordInput id="reg-password-confirm" className={inputClass} value={form.password_confirm} onChange={(e) => update("password_confirm", e.target.value)} autoComplete="new-password" />
                {fieldErrors.password_confirm && <span className="text-xs text-danger">{fieldErrors.password_confirm}</span>}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-degree" className={labelClass}>{uz.register.academicDegree}</label>
                <select id="reg-degree" className={inputClass} value={form.academic_degree} onChange={(e) => update("academic_degree", e.target.value)}>
                  {ACADEMIC_DEGREES.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-title" className={labelClass}>{uz.register.academicTitle}</label>
                <select id="reg-title" className={inputClass} value={form.academic_title} onChange={(e) => update("academic_title", e.target.value)}>
                  {ACADEMIC_TITLES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-position" className={labelClass}>{uz.register.position}</label>
                <select id="reg-position" className={inputClass} value={form.position} onChange={(e) => update("position", e.target.value)}>
                  <option value="">{uz.register.selectPlaceholder}</option>
                  {POSITIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reg-department" className={labelClass}>{uz.register.department}</label>
                <select id="reg-department" className={inputClass} value={form.department} onChange={(e) => update("department", e.target.value)}>
                  <option value="">{uz.register.selectPlaceholder}</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                {fieldErrors.department && <span className="text-xs text-danger">{fieldErrors.department}</span>}
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="reg-research" className={labelClass}>
                {uz.register.researchInterests} <span className="text-ink-faint">({uz.common.optional})</span>
              </label>
              <textarea id="reg-research" className={`${inputClass} min-h-20 resize-y`} value={form.research_interests} onChange={(e) => update("research_interests", e.target.value)} maxLength={1000} />
            </div>

            <p className="text-xs text-ink-faint">
              Diplom va sertifikatlarni ro'yxatdan o'tgach, shaxsiy kabinetingizdan yuklashingiz mumkin.
            </p>

            <button
              type="submit"
              disabled={submitting}
              className="mt-1 w-full rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
            >
              {submitting ? uz.register.submitting : uz.register.submit}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-ink-soft">
            {uz.common.login}?{" "}
            <button type="button" className="font-medium text-sand-dark underline underline-offset-2" onClick={() => onSwitchToLogin()}>
              {uz.common.login}
            </button>
          </p>
        </>
      )}

      {step === 2 && (
        <form className="flex flex-col items-center gap-4 text-center" onSubmit={handleVerify}>
          <h2 id="register-modal-title" className="text-2xl font-semibold text-ink">
            {uz.register.verifyTitle}
          </h2>
          <p className="text-sm text-ink-soft">{uz.register.verifyHint(form.email)}</p>

          {verifyError && (
            <div className="w-full rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
              {verifyError}
            </div>
          )}

          <div className="flex gap-2" onPaste={handleCodePaste}>
            {digits.map((digit, i) => (
              <input
                key={i}
                ref={(el) => (codeInputsRef.current[i] = el)}
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleDigitChange(i, e.target.value)}
                onKeyDown={(e) => handleDigitKeyDown(i, e)}
                aria-label={`Raqam ${i + 1}`}
                className="h-14 w-11 rounded-lg border border-line bg-paper text-center text-xl font-bold text-ink focus:border-sand focus:bg-surface focus:outline-none"
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={verifying}
            className="w-full rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
          >
            {verifying ? uz.register.verifySubmitting : uz.register.verifySubmit}
          </button>

          <button
            type="button"
            onClick={handleResend}
            disabled={cooldown > 0 || resendState === "sending"}
            className="text-sm font-medium text-sand-dark underline underline-offset-2 disabled:text-ink-faint disabled:no-underline"
          >
            {cooldown > 0 ? `Qayta yuborish: ${cooldown}s` : resendState === "sending" ? "Yuborilmoqda…" : "Kodni qayta yuborish"}
          </button>
        </form>
      )}

      {step === 3 && (
        <div className="flex flex-col items-center gap-4 text-center">
          <h2 id="register-modal-title" className="text-2xl font-semibold text-ink">
            {uz.register.successTitle}
          </h2>
          <p className="text-sm text-ink-soft">{uz.register.successBody}</p>
          <button
            type="button"
            onClick={() => onSwitchToLogin(form.username)}
            className="w-full rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark"
          >
            {uz.register.goToLogin}
          </button>
        </div>
      )}
    </Modal>
  );
}
