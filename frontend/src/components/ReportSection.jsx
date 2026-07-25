import React, { useEffect, useState } from "react";

import { downloadBlob, reportsApi } from "../api/endpoints";

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 8 }, (_, i) => CURRENT_YEAR - i);

function DrilldownModal({ code, year, onClose }) {
  const [rows, setRows] = useState(null);

  useEffect(() => {
    reportsApi.drilldown(code, year).then((res) => setRows(res.data.results));
  }, [code, year]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-surface p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink">{code}-band ostidagi yozuvlar</h3>
          <button onClick={onClose} className="text-2xl text-ink-faint hover:text-ink">
            ×
          </button>
        </div>
        {rows === null ? (
          <p className="text-sm text-ink-faint">Yuklanmoqda…</p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-ink-faint">Yozuvlar topilmadi.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {rows.map((r) => (
              <li key={r.id} className="rounded-lg border border-line bg-paper px-3.5 py-2.5 text-sm">
                <p className="font-medium text-ink">{r.title}</p>
                <p className="text-xs text-ink-faint">
                  {r.category_display} · {r.year || ""} {r.doi && `· DOI: ${r.doi}`}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function ReportSection() {
  const [year, setYear] = useState(String(CURRENT_YEAR));
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [drilldown, setDrilldown] = useState(null); // { code }

  useEffect(() => {
    setLoading(true);
    reportsApi
      .me({ year })
      .then((res) => setReport(res.data))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [year]);

  async function handleExport() {
    setExporting(true);
    try {
      const res = await reportsApi.exportMe({ year });
      downloadBlob(res.data, `hisobot_${year}.xlsx`);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-7 shadow-sm shadow-ink/5">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Hisobot</h2>
          <p className="text-sm text-ink-faint">Rasmiy yillik hisobot shakli — avtomatik hisoblanadi.</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded-lg border border-line bg-paper px-3.5 py-2 text-sm text-ink focus:border-sand focus:bg-surface focus:outline-none"
          >
            {YEAR_OPTIONS.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || loading}
            className="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark disabled:opacity-60"
          >
            {exporting ? "Tayyorlanmoqda…" : "Excelga yuklash"}
          </button>
        </div>
      </div>

      {loading || !report ? (
        <div className="py-16 text-center text-sm text-ink-faint">Yuklanmoqda…</div>
      ) : (
        <>
          {report.unclassified.length > 0 && (
            <div className="mb-5 rounded-lg border border-warning/30 bg-warning-tint px-4 py-3 text-sm text-warning">
              <p className="font-medium">
                {report.unclassified.length} ta yozuv hisobotga kiritilmadi (klassifikatsiya maydonlari to'ldirilmagan):
              </p>
              <ul className="mt-2 list-disc pl-5">
                {report.unclassified.map((w) => (
                  <li key={w.id}>
                    {w.title} — <span className="italic">{w.category_display}</span>, "Ilmiy ishlarim" bo'limidan tahrirlang.
                  </li>
                ))}
              </ul>
            </div>
          )}

          {report.without_certificate > 0 && (
            <div className="mb-5 rounded-lg border border-line bg-paper px-4 py-3 text-sm text-ink-soft">
              * {report.without_certificate} ta anjumanda ishtirok yozuvi sertifikatsiz (IV bo'lim).
            </div>
          )}

          <div className="flex flex-col gap-8">
            {report.sections.map((section) => (
              <div key={section.id}>
                <h3 className="mb-3 rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white">
                  {section.id}. {section.title}
                </h3>
                <table className="w-full border-collapse text-sm">
                  <tbody className="divide-y divide-line">
                    {section.lines.map((line) => (
                      <tr key={line.code} className={line.is_subset ? "text-ink-faint" : "text-ink"}>
                        <td className="w-16 py-2 pr-3 font-mono text-xs">{line.code}</td>
                        <td className={`py-2 pr-3 ${line.is_subset ? "pl-6 italic" : ""}`}>{line.label}</td>
                        <td className="w-16 py-2 text-right">
                          {line.count > 0 ? (
                            <button
                              type="button"
                              onClick={() => setDrilldown({ code: line.code })}
                              className="font-semibold text-sand-dark underline underline-offset-2"
                            >
                              {line.count}
                            </button>
                          ) : (
                            <span className="text-ink-faint">0</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {section.id === "II" && (
                      <tr>
                        <td colSpan={3} className="py-2">
                          <div className="grid grid-cols-2 gap-4 rounded-lg bg-paper p-3 text-xs">
                            <div>
                              <p className="mb-1 font-semibold text-ink-soft">Scopus</p>
                              {["Q1", "Q2", "Q3", "Q4"].map((q) => (
                                <span key={q} className="mr-3">
                                  {q}: {report.quartile_matrix.scopus[q]}
                                </span>
                              ))}
                            </div>
                            <div>
                              <p className="mb-1 font-semibold text-ink-soft">Web of Science</p>
                              {["Q1", "Q2", "Q3", "Q4"].map((q) => (
                                <span key={q} className="mr-3">
                                  {q}: {report.quartile_matrix.wos[q]}
                                </span>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                    <tr className="bg-sand-tint font-semibold text-ink">
                      <td colSpan={2} className="py-2 pl-2">
                        Jami:
                      </td>
                      <td className="py-2 pr-2 text-right">{section.total}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </>
      )}

      {drilldown && (
        <DrilldownModal code={drilldown.code} year={year} onClose={() => setDrilldown(null)} />
      )}
    </div>
  );
}
