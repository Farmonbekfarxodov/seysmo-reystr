import React, { useEffect, useState } from "react";

import { departmentsApi, downloadBlob, reportsApi } from "../api/endpoints";
import LineDrilldownModal from "../components/LineDrilldownModal.jsx";

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 8 }, (_, i) => CURRENT_YEAR - i);
const SECTION_TOTAL_KEYS = [
  ["total_II", "II"],
  ["total_III", "III"],
  ["total_IV", "IV"],
  ["total_V", "V"],
  ["total_VI", "VI"],
];

function CountButton({ count, onClick, label }) {
  if (!count) {
    return <span className="text-ink-faint">0</span>;
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="rounded font-semibold text-sand-dark underline underline-offset-2 transition hover:text-sand focus-visible:outline focus-visible:outline-2 focus-visible:outline-sand"
    >
      {count}
    </button>
  );
}

export default function AdminReportPage() {
  const [year, setYear] = useState(String(CURRENT_YEAR));
  const [department, setDepartment] = useState("");
  const [departments, setDepartments] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [drilldown, setDrilldown] = useState(null); // { code, label }

  useEffect(() => {
    departmentsApi.list().then((res) => setDepartments(res.data)).catch(() => setDepartments([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    reportsApi
      .institute({ year, department: department || undefined })
      .then((res) => setReport(res.data))
      .catch(() => setReport(null))
      .finally(() => setLoading(false));
  }, [year, department]);

  async function handleExport() {
    setExporting(true);
    try {
      const res = await reportsApi.exportInstitute({ year, department: department || undefined });
      downloadBlob(res.data, `hisobot_${year}_institut.xlsx`);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-12">
      <div className="rounded-2xl border border-line bg-surface p-7 shadow-sm shadow-ink/5">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-ink">Institut bo'yicha hisobot</h1>
            <p className="text-sm text-ink-faint">Barcha xodimlar bo'yicha jamlangan, takroriy yozuvlar birlashtirilgan.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
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
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="rounded-lg border border-line bg-paper px-3.5 py-2 text-sm text-ink focus:border-sand focus:bg-surface focus:outline-none"
            >
              <option value="">Barcha bo'limlar</option>
              {departments.map((d) => (
                <option key={d.id} value={d.slug}>
                  {d.name}
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
            {report.deduplicated_count > 0 && (
              <div className="mb-5 rounded-lg border border-line bg-paper px-4 py-3 text-sm text-ink-soft">
                {report.deduplicated_count} ta takroriy yozuv birlashtirildi.
                <ul className="mt-2 list-disc pl-5 text-xs">
                  {report.duplicate_groups.map((g, i) => (
                    <li key={i}>
                      {g.title} ({g.report_code}) — {g.authors.join(", ")}
                    </li>
                  ))}
                </ul>
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
                            <CountButton
                              count={line.count}
                              label={`${line.code} — ${line.count} ta yozuv`}
                              onClick={() =>
                                setDrilldown({ code: line.code, label: `${line.code} — ${line.label}` })
                              }
                            />
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
                                    {q}:{" "}
                                    <CountButton
                                      count={report.quartile_matrix.scopus[q]}
                                      label={`Scopus ${q} — ${report.quartile_matrix.scopus[q]} ta yozuv`}
                                      onClick={() =>
                                        setDrilldown({ code: `2.1:scopus:${q}`, label: `2.1 — Scopus ${q}` })
                                      }
                                    />
                                  </span>
                                ))}
                              </div>
                              <div>
                                <p className="mb-1 font-semibold text-ink-soft">Web of Science</p>
                                {["Q1", "Q2", "Q3", "Q4"].map((q) => (
                                  <span key={q} className="mr-3">
                                    {q}:{" "}
                                    <CountButton
                                      count={report.quartile_matrix.wos[q]}
                                      label={`Web of Science ${q} — ${report.quartile_matrix.wos[q]} ta yozuv`}
                                      onClick={() =>
                                        setDrilldown({ code: `2.1:wos:${q}`, label: `2.1 — Web of Science ${q}` })
                                      }
                                    />
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
                        <td className="py-2 pr-2 text-right">
                          <CountButton
                            count={section.total}
                            label={`${section.id}-bo'lim jami — ${section.total} ta yozuv`}
                            onClick={() =>
                              setDrilldown({ code: section.id, label: `${section.id}. ${section.title} — Jami` })
                            }
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              ))}
            </div>

            {report.department_breakdown?.length > 0 && (
              <div className="mt-8">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-faint">
                  Laboratoriyalar bo'yicha
                </h3>
                <div className="overflow-x-auto rounded-xl border border-line">
                  <table className="w-full min-w-[600px] border-collapse text-sm">
                    <thead>
                      <tr className="bg-paper text-left text-xs font-semibold uppercase tracking-wide text-ink-faint">
                        <th className="px-4 py-3">Laboratoriya</th>
                        {SECTION_TOTAL_KEYS.map(([, id]) => (
                          <th key={id} className="px-4 py-3 text-right">
                            {id}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {report.department_breakdown.map((row) => (
                        <tr key={row.department}>
                          <td className="px-4 py-2.5">{row.department}</td>
                          {SECTION_TOTAL_KEYS.map(([key, id]) => (
                            <td key={id} className="px-4 py-2.5 text-right">
                              {row.report[key] || 0}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {report.employee_breakdown?.length > 0 && (
              <div className="mt-8">
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-faint">
                  Xodimlar bo'yicha
                </h3>
                <div className="overflow-x-auto rounded-xl border border-line">
                  <table className="w-full min-w-[700px] border-collapse text-sm">
                    <thead>
                      <tr className="bg-paper text-left text-xs font-semibold uppercase tracking-wide text-ink-faint">
                        <th className="px-4 py-3">F.I.Sh.</th>
                        <th className="px-4 py-3">Laboratoriya</th>
                        {SECTION_TOTAL_KEYS.map(([, id]) => (
                          <th key={id} className="px-4 py-3 text-right">
                            {id}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {report.employee_breakdown.map((row) => (
                        <tr key={row.employee_id}>
                          <td className="px-4 py-2.5">{row.full_name}</td>
                          <td className="px-4 py-2.5 text-ink-soft">{row.department}</td>
                          {SECTION_TOTAL_KEYS.map(([key, id]) => (
                            <td key={id} className="px-4 py-2.5 text-right">
                              {row.report[key] || 0}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {drilldown && (
        <LineDrilldownModal
          scope="institute"
          code={drilldown.code}
          label={drilldown.label}
          year={year}
          department={department || undefined}
          onClose={() => setDrilldown(null)}
        />
      )}
    </div>
  );
}
