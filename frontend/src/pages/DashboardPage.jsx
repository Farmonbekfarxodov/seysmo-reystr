import React, { useEffect, useRef, useState } from "react";

import {
  ACADEMIC_DEGREES,
  ACADEMIC_TITLES,
  departmentsApi,
  flattenApiErrors,
  POSITIONS,
  specialistsApi,
} from "../api/endpoints";
import uz from "../i18n/uz.js";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function initials(first, last) {
  return `${(first || "?").charAt(0)}${(last || "").charAt(0)}`.toUpperCase();
}

export default function DashboardPage() {
  const [departments, setDepartments] = useState([]);
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [error, setError] = useState(null);

  const [photoAction, setPhotoAction] = useState("none");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const photoInputRef = useRef(null);

  const [uploadError, setUploadError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  function loadProfile() {
    setLoading(true);
    specialistsApi
      .me()
      .then((res) => {
        setProfile(res.data);
        setForm({
          last_name: res.data.last_name,
          first_name: res.data.first_name,
          patronymic: res.data.patronymic || "",
          academic_degree: res.data.academic_degree,
          academic_title: res.data.academic_title,
          position: res.data.position,
          department: res.data.department,
          research_interests: res.data.research_interests || "",
          bio: res.data.bio || "",
        });
        setPhotoAction("none");
        setPhotoFile(null);
        setPhotoPreview(null);
      })
      .catch(() => setError("Profilni yuklab bo'lmadi."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    departmentsApi.list().then((res) => setDepartments(res.data)).catch(() => setDepartments([]));
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handlePhotoSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoAction("replace");
    setPhotoFile(file);
    const reader = new FileReader();
    reader.onload = () => setPhotoPreview(reader.result);
    reader.readAsDataURL(file);
  }

  function handleRemovePhoto() {
    setPhotoAction("remove");
    setPhotoFile(null);
    setPhotoPreview(null);
    if (photoInputRef.current) photoInputRef.current.value = "";
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setSaveMessage(null);
    setError(null);
    try {
      let res;
      if (photoAction === "replace") {
        res = await specialistsApi.updateMe({ ...form, photo: photoFile }, { isMultipart: true });
      } else if (photoAction === "remove") {
        res = await specialistsApi.updateMe({ ...form, remove_photo: true }, { isMultipart: true });
      } else {
        res = await specialistsApi.updateMe(form);
      }
      setProfile(res.data);
      setPhotoAction("none");
      setPhotoFile(null);
      setPhotoPreview(null);
      setSaveMessage(uz.dashboard.saved);
    } catch (err) {
      const { generic } = flattenApiErrors(err.response?.data);
      setError(generic || "O'zgarishlarni saqlab bo'lmadi.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUploadDocument(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await specialistsApi.uploadDocument(file);
      loadProfile();
    } catch (err) {
      const { fieldErrors, generic } = flattenApiErrors(err.response?.data);
      setUploadError(fieldErrors.file || generic || "Yuklash muvaffaqiyatsiz tugadi.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDeleteDocument(docId) {
    try {
      await specialistsApi.deleteDocument(docId);
      loadProfile();
    } catch {
      setUploadError("Faylni o'chirib bo'lmadi.");
    }
  }

  if (loading || !form) {
    return <div className="flex-1 py-24 text-center text-sm text-ink-faint">{uz.common.loading}</div>;
  }

  const inputClass =
    "rounded-lg border border-line bg-paper px-3.5 py-2.5 text-ink transition focus:border-sand focus:bg-surface focus:outline-none";
  const labelClass = "text-sm font-medium text-ink-soft";

  const currentPhotoSrc = photoPreview || (photoAction !== "remove" ? profile.photo_thumbnail : null);

  return (
    <div className="mx-auto grid w-full max-w-5xl grid-cols-1 gap-6 px-5 py-12 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="rounded-2xl border border-line bg-surface p-7 shadow-sm shadow-ink/5">
        <h2 className="mb-1 text-lg font-semibold text-ink">{uz.dashboard.profileSection}</h2>
        <p className="mb-5 text-sm text-ink-faint">{uz.dashboard.subtitle}</p>

        {error && (
          <div className="mb-4 rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
            {error}
          </div>
        )}
        {saveMessage && (
          <div className="mb-4 rounded-lg border border-success/30 bg-success-tint px-3 py-2.5 text-sm text-success">
            {saveMessage}
          </div>
        )}

        <form className="flex flex-col gap-4" onSubmit={handleSave}>
          <div className="flex items-center gap-4">
            {currentPhotoSrc ? (
              <img src={currentPhotoSrc} alt="" className="h-16 w-16 rounded-full object-cover ring-2 ring-line" />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-sand-tint text-lg font-semibold text-sand-dark ring-2 ring-line">
                {initials(form.first_name, form.last_name)}
              </div>
            )}
            <div className="flex gap-3 text-sm">
              <label className="cursor-pointer font-medium text-sand-dark underline underline-offset-2">
                {currentPhotoSrc ? uz.common.replace : uz.register.photo}
                <input ref={photoInputRef} type="file" accept=".jpg,.jpeg,.png" onChange={handlePhotoSelect} className="hidden" />
              </label>
              {currentPhotoSrc && (
                <button type="button" onClick={handleRemovePhoto} className="font-medium text-danger underline underline-offset-2">
                  {uz.common.remove}
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-last-name" className={labelClass}>{uz.register.lastName}</label>
              <input id="dash-last-name" className={inputClass} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-first-name" className={labelClass}>{uz.register.firstName}</label>
              <input id="dash-first-name" className={inputClass} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="dash-patronymic" className={labelClass}>{uz.register.patronymic}</label>
            <input id="dash-patronymic" className={inputClass} value={form.patronymic} onChange={(e) => update("patronymic", e.target.value)} />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-degree" className={labelClass}>{uz.register.academicDegree}</label>
              <select id="dash-degree" className={inputClass} value={form.academic_degree} onChange={(e) => update("academic_degree", e.target.value)}>
                {ACADEMIC_DEGREES.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-title" className={labelClass}>{uz.register.academicTitle}</label>
              <select id="dash-title" className={inputClass} value={form.academic_title} onChange={(e) => update("academic_title", e.target.value)}>
                {ACADEMIC_TITLES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-position" className={labelClass}>{uz.register.position}</label>
              <select id="dash-position" className={inputClass} value={form.position} onChange={(e) => update("position", e.target.value)}>
                <option value="">{uz.register.selectPlaceholder}</option>
                {POSITIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="dash-department" className={labelClass}>{uz.register.department}</label>
              <select id="dash-department" className={inputClass} value={form.department} onChange={(e) => update("department", e.target.value)}>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="dash-research" className={labelClass}>{uz.register.researchInterests}</label>
            <textarea id="dash-research" className={`${inputClass} min-h-20 resize-y`} value={form.research_interests} onChange={(e) => update("research_interests", e.target.value)} maxLength={1000} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="dash-bio" className={labelClass}>{uz.register.bio}</label>
            <textarea id="dash-bio" className={`${inputClass} min-h-20 resize-y`} value={form.bio} onChange={(e) => update("bio", e.target.value)} maxLength={1000} />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="mt-1 self-start rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
          >
            {saving ? uz.common.saving : uz.common.save}
          </button>
        </form>
      </div>

      <div className="h-fit rounded-2xl border border-line bg-surface p-7 shadow-sm shadow-ink/5">
        <h2 className="mb-4 text-lg font-semibold text-ink">{uz.dashboard.documentsSection}</h2>
        {uploadError && (
          <div className="mb-4 rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
            {uploadError}
          </div>
        )}

        {profile.documents.length === 0 ? (
          <p className="text-sm text-ink-faint">{uz.dashboard.noDocuments}</p>
        ) : (
          <div className="divide-y divide-line">
            {profile.documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <a
                    href={doc.file}
                    target="_blank"
                    rel="noreferrer"
                    className="truncate text-sm font-medium text-sand-dark underline underline-offset-2"
                  >
                    {doc.original_filename}
                  </a>
                  <p className="text-xs text-ink-faint">
                    {formatSize(doc.size)} · {new Date(doc.uploaded_at).toLocaleDateString("uz-UZ")}
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id)}
                  className="shrink-0 rounded-lg border border-danger/40 px-3 py-1.5 text-xs font-medium text-danger transition hover:bg-danger-tint"
                >
                  {uz.common.delete}
                </button>
              </div>
            ))}
          </div>
        )}

        <hr className="my-5 border-line" />

        <label className="block cursor-pointer rounded-lg border border-dashed border-line bg-paper px-4 py-3.5 text-center text-sm text-ink-soft transition hover:border-sand">
          {uploading ? uz.dashboard.uploading : uz.dashboard.uploadNew}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleUploadDocument}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>
    </div>
  );
}
