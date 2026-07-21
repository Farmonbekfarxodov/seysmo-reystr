import React from "react";

const COLUMN_DEFS = {
  foreign_article: [
    { key: "title", label: "Maqola nomi" },
    { key: "publisher", label: "Nashriyot" },
    { key: "doi", label: "DOI", type: "doi" },
    { key: "index_type_display", label: "Turi" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)" },
    { key: "impact_factor", label: "Impakt-faktor" },
    { key: "year", label: "Yili", sortable: true, sortKey: "year" },
    { key: "authorship_display", label: "Muallifligi" },
  ],
  local_article: [
    { key: "title", label: "Maqola nomi" },
    { key: "journal_name", label: "Jurnal nomi" },
    { key: "doi", label: "DOI", type: "doi" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)" },
    { key: "year", label: "Yili", sortable: true, sortKey: "year" },
    { key: "link", label: "Havola", type: "link" },
    { key: "authorship_display", label: "Muallifligi" },
  ],
  thesis: [
    { key: "title", label: "Maqola nomi" },
    { key: "journal_name", label: "Jurnal nomi" },
    { key: "thesis_category_display", label: "Kategoriya" },
    { key: "doi", label: "DOI", type: "doi" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)" },
    { key: "year", label: "Yili", sortable: true, sortKey: "year" },
    { key: "link", label: "Havola", type: "link" },
    { key: "authorship_display", label: "Muallifligi" },
  ],
  patent: [
    { key: "patent_category_display", label: "Hujjat kategoriyasi" },
    { key: "patent_type_display", label: "Hujjat turi" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)" },
    { key: "title", label: "Hujjat nomi" },
    { key: "certificate_number", label: "Guvohnoma raqami" },
    { key: "issued_date", label: "Berilgan yili", sortable: true, sortKey: "issued_date", type: "date" },
    { key: "authorship_display", label: "Muallifligi" },
  ],
  monograph: [
    { key: "title", label: "Nomi" },
    { key: "publisher", label: "Nashriyot" },
    { key: "isbn", label: "ISBN" },
    { key: "project_name", label: "Loyiha doirasida (Loyiha nomi)" },
    { key: "year", label: "Yili", sortable: true, sortKey: "year" },
    { key: "link", label: "Havola", type: "link" },
    { key: "authorship_display", label: "Muallifligi" },
  ],
};

export function getColumns(category) {
  return COLUMN_DEFS[category] || [];
}

function formatDate(value) {
  if (!value) return "—";
  const [y, m, d] = value.split("-");
  return `${d}.${m}.${y}`;
}

function Cell({ column, row }) {
  const value = row[column.key];

  if (column.type === "doi") {
    if (!value) return <span className="text-ink-faint">—</span>;
    return (
      <a
        href={`https://doi.org/${value}`}
        target="_blank"
        rel="noreferrer"
        className="text-sand-dark underline underline-offset-2"
      >
        {value}
      </a>
    );
  }

  if (column.type === "link") {
    if (!value) return <span className="text-ink-faint">—</span>;
    return (
      <a href={value} target="_blank" rel="noreferrer" className="inline-flex text-sand-dark" aria-label="Havola">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 3h7v7" />
          <path d="M10 14 21 3" />
          <path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5" />
        </svg>
      </a>
    );
  }

  if (column.type === "date") {
    return formatDate(value);
  }

  if (value === null || value === undefined || value === "") {
    return <span className="text-ink-faint">—</span>;
  }
  return String(value);
}

const DownloadIcon = () => (
  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <path d="M7 10l5 5 5-5" />
    <path d="M12 15V3" />
  </svg>
);

const EditIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
  </svg>
);

const DeleteIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 6h18" />
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
  </svg>
);

export default function WorksTable({ category, rows, sortField, sortDir, onSortChange, showActions, onEdit, onDelete }) {
  const columns = getColumns(category);

  function handleSort(column) {
    if (!column.sortable) return;
    if (sortField === column.sortKey) {
      onSortChange(column.sortKey, sortDir === "asc" ? "desc" : "asc");
    } else {
      onSortChange(column.sortKey, "desc");
    }
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[860px] border-collapse text-sm">
        <thead>
          <tr className="bg-paper text-left text-xs font-semibold uppercase tracking-wide text-ink-faint">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`whitespace-nowrap px-4 py-3 ${col.sortable ? "cursor-pointer select-none hover:text-ink" : ""}`}
                onClick={() => handleSort(col)}
              >
                {col.label}
                {col.sortable && sortField === col.sortKey && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
            ))}
            <th className="whitespace-nowrap px-4 py-3 text-right">
              {showActions ? "Amallar" : "Fayl"}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => (
            <tr key={row.id} className="text-ink">
              {columns.map((col) => (
                <td key={col.key} className="whitespace-nowrap px-4 py-3 max-w-xs truncate">
                  <Cell column={col} row={row} />
                </td>
              ))}
              <td className="whitespace-nowrap px-4 py-3">
                <div className="flex items-center justify-end gap-3 text-ink-soft">
                  <a
                    href={row.file}
                    target="_blank"
                    rel="noreferrer"
                    aria-label="PDF yuklab olish"
                    className="transition hover:text-sand-dark"
                  >
                    <DownloadIcon />
                  </a>
                  {showActions && (
                    <>
                      <button
                        type="button"
                        onClick={() => onEdit(row)}
                        aria-label="Tahrirlash"
                        className="transition hover:text-sand-dark"
                      >
                        <EditIcon />
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(row)}
                        aria-label="O'chirish"
                        className="transition hover:text-danger"
                      >
                        <DeleteIcon />
                      </button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
