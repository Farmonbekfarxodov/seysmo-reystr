import React, { useEffect, useState } from "react";

import { downloadBlob, reportsApi } from "../api/endpoints";
import Modal from "./Modal.jsx";

const CATEGORY_META_FIELDS = {
  foreign_article: ["publisher", "doi", "year", "journal_scope_display"],
  local_article: ["journal_name", "doi", "year"],
  thesis: ["journal_name", "conference_scope_display", "year"],
  conference_participation: ["conference_name", "location", "event_date"],
  patent: ["patent_category_display", "certificate_number", "issued_date"],
  other_publication: ["publication_type_display", "publisher", "year"],
};

const FIELD_LABELS = {
  publisher: "Nashriyot",
  doi: "DOI",
  year: "Yili",
  journal_scope_display: "Turi",
  journal_name: "Jurnal nomi",
  conference_scope_display: "Anjuman turi",
  conference_name: "Anjuman nomi",
  location: "Joyi",
  event_date: "Sana",
  patent_category_display: "Kategoriya",
  certificate_number: "Guvohnoma raqami",
  issued_date: "Berilgan sanasi",
  publication_type_display: "Nashr turi",
};

function DownloadIcon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M7 10l5 5 5-5" />
      <path d="M12 15V3" />
    </svg>
  );
}

export default function LineDrilldownModal({ scope, code, label, year, department, onClose }) {
  const isInstitute = scope === "institute";
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [zipping, setZipping] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    setRows(null);
    setError(null);
    const fetcher = isInstitute
      ? () => reportsApi.instituteLine({ code, year, department })
      : () => reportsApi.line({ code, year });
    fetcher()
      .then((res) => setRows(res.data.results))
      .catch(() => setError("Ma'lumotlarni yuklab bo'lmadi."));
  }, [scope, code, year, department, isInstitute]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  async function handleZip() {
    setZipping(true);
    try {
      const res = isInstitute
        ? await reportsApi.instituteLineZip({ code, year, department })
        : await reportsApi.lineZip({ code, year });
      downloadBlob(res.data, `${code}_${year || "barcha"}.zip`);
      setToast({ type: "success", message: "ZIP fayl yuklab olindi." });
    } catch {
      setToast({ type: "error", message: "ZIP faylni yuklab bo'lmadi." });
    } finally {
      setZipping(false);
    }
  }

  const metaFields = rows && rows[0] ? CATEGORY_META_FIELDS[rows[0].category] || [] : [];

  return (
    <Modal onClose={onClose} wide labelledBy="line-drilldown-title">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 id="line-drilldown-title" className="text-lg font-semibold text-ink">
            {label}
          </h2>
          <p className="text-sm text-ink-faint">
            {year ? `${year} · ` : ""}
            {rows ? `${rows.length} ta yozuv` : "Yuklanmoqda…"}
            {isInstitute ? " · institut" : " · shaxsiy"}
          </p>
        </div>
      </div>

      {toast && (
        <div
          className={`mb-4 rounded-lg px-3 py-2.5 text-sm ${
            toast.type === "success"
              ? "border border-success/30 bg-success-tint text-success"
              : "border border-danger/30 bg-danger-tint text-danger"
          }`}
        >
          {toast.message}
        </div>
      )}

      {error ? (
        <p className="py-10 text-center text-sm text-danger">{error}</p>
      ) : rows === null ? (
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-paper" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <p className="py-10 text-center text-sm text-ink-faint">Yozuvlar topilmadi.</p>
      ) : (
        <div className="max-h-[55vh] overflow-x-auto overflow-y-auto rounded-xl border border-line">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead className="sticky top-0 bg-paper">
              <tr className="text-left text-xs font-semibold uppercase tracking-wide text-ink-faint">
                <th className="px-3 py-2.5">№</th>
                {isInstitute && <th className="px-3 py-2.5">Muallif</th>}
                <th className="px-3 py-2.5">Nomi</th>
                {metaFields.map((f) => (
                  <th key={f} className="px-3 py-2.5 whitespace-nowrap">
                    {FIELD_LABELS[f] || f}
                  </th>
                ))}
                <th className="px-3 py-2.5">Muallifligi</th>
                <th className="px-3 py-2.5 text-right">Hujjat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((row, i) => (
                <tr key={row.id}>
                  <td className="px-3 py-2.5 text-ink-faint">{i + 1}</td>
                  {isInstitute && (
                    <td className="px-3 py-2.5">
                      {row.authors.map((a) => (
                        <div key={a.specialist_id}>
                          <a
                            href={`/specialists/${a.specialist_id}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sand-dark underline underline-offset-2"
                          >
                            {a.full_name}
                          </a>
                          {a.is_main_author && <span className="text-ink-faint"> (asosiy)</span>}
                        </div>
                      ))}
                    </td>
                  )}
                  <td className="px-3 py-2.5">
                    {row.link || row.doi ? (
                      <a
                        href={row.link || `https://doi.org/${row.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-ink underline underline-offset-2"
                      >
                        {row.title}
                      </a>
                    ) : (
                      row.title
                    )}
                  </td>
                  {metaFields.map((f) => (
                    <td key={f} className="px-3 py-2.5 text-ink-soft">
                      {row[f] || "—"}
                    </td>
                  ))}
                  <td className="px-3 py-2.5 text-ink-soft">{row.authorship_display}</td>
                  <td className="px-3 py-2.5 text-right">
                    {row.download_url ? (
                      <a
                        href={row.download_url}
                        target="_blank"
                        rel="noreferrer"
                        aria-label="Hujjatni yuklab olish"
                        className="inline-flex text-ink-soft transition hover:text-sand-dark"
                      >
                        <DownloadIcon />
                      </a>
                    ) : (
                      <span className="text-xs text-ink-faint">Sertifikat yo'q</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink transition hover:border-sand"
        >
          Yopish
        </button>
        <button
          type="button"
          onClick={handleZip}
          disabled={zipping || !rows || rows.length === 0}
          className="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
        >
          {zipping ? "Tayyorlanmoqda…" : "Barchasini ZIP qilib yuklash"}
        </button>
      </div>
    </Modal>
  );
}
