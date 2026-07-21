import React, { useRef, useState } from "react";

import {
  AUTHORSHIP_OPTIONS,
  errorCode,
  flattenApiErrors,
  INDEX_TYPE_OPTIONS,
  PATENT_CATEGORY_OPTIONS,
  PATENT_TYPE_OPTIONS,
  THESIS_CATEGORY_OPTIONS,
  worksApi,
} from "../api/endpoints";
import Modal from "./Modal.jsx";

const FIELD_CONFIGS = {
  foreign_article: [
    { key: "title", label: "Maqola nomi", type: "text", required: true, span: 2 },
    { key: "doi", label: "DOI", type: "text", required: true },
    { key: "year", label: "Yili", type: "year", required: true },
    { key: "authorship", label: "Muallifligi", type: "select", required: true, options: AUTHORSHIP_OPTIONS },
    { key: "publisher", label: "Nashriyot", type: "text" },
    { key: "index_type", label: "Turi", type: "select", options: INDEX_TYPE_OPTIONS },
    { key: "impact_factor", label: "Impakt-faktor", type: "number" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)", type: "text", span: 2 },
  ],
  local_article: [
    { key: "title", label: "Maqola nomi", type: "text", required: true, span: 2 },
    { key: "journal_name", label: "Jurnal nomi", type: "text", required: true },
    { key: "doi", label: "DOI", type: "text", required: true },
    { key: "year", label: "Yili", type: "year", required: true },
    { key: "link", label: "Havola", type: "url", required: true },
    { key: "authorship", label: "Muallifligi", type: "select", required: true, options: AUTHORSHIP_OPTIONS },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)", type: "text", span: 2 },
  ],
  thesis: [
    { key: "title", label: "Maqola nomi", type: "text", required: true, span: 2 },
    { key: "journal_name", label: "Jurnal/Konferensiya nomi", type: "text", required: true },
    { key: "thesis_category", label: "Kategoriya", type: "select", required: true, options: THESIS_CATEGORY_OPTIONS },
    { key: "year", label: "Yili", type: "year", required: true },
    { key: "authorship", label: "Muallifligi", type: "select", required: true, options: AUTHORSHIP_OPTIONS },
    { key: "doi", label: "DOI", type: "text" },
    { key: "link", label: "Havola", type: "url" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)", type: "text", span: 2 },
  ],
  patent: [
    { key: "title", label: "Hujjat nomi", type: "text", required: true, span: 2 },
    { key: "patent_category", label: "Hujjat kategoriyasi", type: "select", required: true, options: PATENT_CATEGORY_OPTIONS },
    { key: "patent_type", label: "Hujjat turi", type: "select", required: true, options: PATENT_TYPE_OPTIONS },
    { key: "certificate_number", label: "Guvohnoma raqami", type: "text", required: true },
    { key: "issued_date", label: "Berilgan sanasi", type: "date", required: true },
    { key: "authorship", label: "Muallifligi", type: "select", required: true, options: AUTHORSHIP_OPTIONS },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)", type: "text", span: 2 },
  ],
  monograph: [
    { key: "title", label: "Nomi", type: "text", required: true, span: 2 },
    { key: "publisher", label: "Nashriyot", type: "text", required: true },
    { key: "year", label: "Yili", type: "year", required: true },
    { key: "authorship", label: "Muallifligi", type: "select", required: true, options: AUTHORSHIP_OPTIONS },
    { key: "isbn", label: "ISBN", type: "text" },
    { key: "pages", label: "Sahifalar soni", type: "number" },
    { key: "link", label: "Havola", type: "url" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)", type: "text", span: 2 },
  ],
};

const CATEGORY_TITLES = {
  foreign_article: "Xorijiy maqola",
  local_article: "Mahalliy maqola",
  thesis: "Tezis",
  patent: "Patent",
  monograph: "Monografiya",
};

function initialFormFor(category, work) {
  const fields = FIELD_CONFIGS[category];
  const form = {};
  fields.forEach((f) => {
    form[f.key] = work?.[f.key] ?? "";
  });
  return form;
}

export default function WorkFormModal({ category, work, projectNameSuggestions = [], onClose, onSaved }) {
  const isEditing = !!work;
  const fields = FIELD_CONFIGS[category];

  const [form, setForm] = useState(() => initialFormFor(category, work));
  const [pdfFile, setPdfFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirmingDuplicate, setConfirmingDuplicate] = useState(false);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleFileSelect(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setFieldErrors((prev) => ({ ...prev, file: "Faqat PDF fayl yuklash mumkin" }));
      return;
    }
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.file;
      return next;
    });
    setPdfFile(file);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    handleFileSelect(e.dataTransfer.files?.[0]);
  }

  function buildPayload() {
    const payload = { category, ...form };
    if (pdfFile) payload.file = pdfFile;
    return payload;
  }

  function validateClientSide() {
    const errors = {};
    fields.forEach((f) => {
      if (f.required && !form[f.key]) errors[f.key] = `${f.label} majburiy.`;
    });
    if (!isEditing && !pdfFile) errors.file = "PDF fayl yuklash majburiy.";
    return errors;
  }

  async function submitWork(payload) {
    if (isEditing) {
      return worksApi.update(work.id, payload);
    }
    return worksApi.create(payload);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError(null);

    const errors = validateClientSide();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await submitWork(buildPayload());
      onSaved();
    } catch (err) {
      const data = err.response?.data;
      if (errorCode(data) === "duplicate_doi") {
        setConfirmingDuplicate(true);
      } else {
        const { fieldErrors: fe, generic } = flattenApiErrors(data);
        setFieldErrors(fe);
        setFormError(generic);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirmDuplicate() {
    setSubmitting(true);
    try {
      await submitWork({ ...buildPayload(), confirm_duplicate: true });
      onSaved();
    } catch (err) {
      const { fieldErrors: fe, generic } = flattenApiErrors(err.response?.data);
      setFieldErrors(fe);
      setFormError(generic);
      setConfirmingDuplicate(false);
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "rounded-lg border border-line bg-paper px-3.5 py-2.5 text-ink transition focus:border-sand focus:bg-surface focus:outline-none";
  const labelClass = "text-sm font-medium text-ink-soft";

  if (confirmingDuplicate) {
    return (
      <Modal onClose={() => setConfirmingDuplicate(false)} labelledBy="duplicate-doi-title">
        <h2 id="duplicate-doi-title" className="mb-3 text-xl font-semibold text-ink">
          Bu DOI allaqachon mavjud
        </h2>
        <p className="mb-6 text-sm text-ink-soft">
          Sizda shu DOI bilan boshqa yozuv bor. Baribir saqlaysizmi?
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setConfirmingDuplicate(false)}
            className="flex-1 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink transition hover:border-sand"
          >
            Yo'q, orqaga
          </button>
          <button
            type="button"
            onClick={handleConfirmDuplicate}
            disabled={submitting}
            className="flex-1 rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
          >
            {submitting ? "Saqlanmoqda…" : "Ha, saqlash"}
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal onClose={onClose} wide labelledBy="work-modal-title">
      <h2 id="work-modal-title" className="mb-5 text-2xl font-semibold text-ink">
        {isEditing ? "Tahrirlash" : "Qo'shish"} — {CATEGORY_TITLES[category]}
      </h2>

      {formError && (
        <div className="mb-4 rounded-lg border border-danger/30 bg-danger-tint px-3 py-2.5 text-sm text-danger">
          {formError}
        </div>
      )}

      <form className="flex flex-col gap-4" onSubmit={handleSubmit} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {fields.map((f) => (
            <div key={f.key} className={`flex flex-col gap-1.5 ${f.span === 2 ? "sm:col-span-2" : ""}`}>
              <label htmlFor={`work-${f.key}`} className={labelClass}>
                {f.label} {f.required && <span className="text-danger">*</span>}
              </label>

              {f.type === "select" ? (
                <select
                  id={`work-${f.key}`}
                  className={inputClass}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                >
                  <option value="">Tanlang…</option>
                  {f.options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              ) : f.type === "year" ? (
                <input
                  id={`work-${f.key}`}
                  type="number"
                  min="1900"
                  max="2100"
                  step="1"
                  className={inputClass}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              ) : f.type === "date" ? (
                <input
                  id={`work-${f.key}`}
                  type="date"
                  className={inputClass}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              ) : f.type === "number" ? (
                <input
                  id={`work-${f.key}`}
                  type="number"
                  step="any"
                  className={inputClass}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              ) : f.key === "project_name" ? (
                <>
                  <input
                    id={`work-${f.key}`}
                    type="text"
                    list="project-name-suggestions"
                    className={inputClass}
                    value={form[f.key]}
                    onChange={(e) => update(f.key, e.target.value)}
                  />
                  <datalist id="project-name-suggestions">
                    {projectNameSuggestions.map((name) => (
                      <option key={name} value={name} />
                    ))}
                  </datalist>
                </>
              ) : (
                <input
                  id={`work-${f.key}`}
                  type={f.type === "url" ? "url" : "text"}
                  className={inputClass}
                  value={form[f.key]}
                  onChange={(e) => update(f.key, e.target.value)}
                />
              )}

              {fieldErrors[f.key] && <span className="text-xs text-danger">{fieldErrors[f.key]}</span>}
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className={labelClass}>
            Pdf yuklash <span className="text-danger">*</span>
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex aspect-[3/1] max-h-32 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed px-4 text-center transition ${
              dragActive ? "border-sand bg-sand-tint" : "border-line bg-paper hover:border-sand"
            }`}
          >
            {pdfFile ? (
              <>
                <p className="text-sm font-medium text-ink">{pdfFile.name}</p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPdfFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="text-xs font-medium text-danger underline underline-offset-2"
                >
                  Olib tashlash
                </button>
              </>
            ) : isEditing && work.original_filename ? (
              <>
                <p className="text-sm text-ink-soft">Joriy fayl: {work.original_filename}</p>
                <p className="text-xs text-ink-faint">Almashtirish uchun bosing yoki faylni shu yerga tashlang</p>
              </>
            ) : (
              <>
                <p className="text-sm text-ink-soft">PDF faylni shu yerga tashlang yoki bosing</p>
                <p className="text-xs text-ink-faint">Faqat .pdf</p>
              </>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files?.[0])}
          />
          {fieldErrors.file && <span className="text-xs text-danger">{fieldErrors.file}</span>}
        </div>

        <div className="mt-2 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-line px-5 py-2.5 text-sm font-medium text-ink transition hover:border-sand"
          >
            Bekor qilish
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
          >
            {submitting ? "Saqlanmoqda…" : "Saqlash"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
