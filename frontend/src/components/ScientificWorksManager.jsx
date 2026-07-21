import React, { useEffect, useState } from "react";

import { worksApi, WORK_CATEGORIES } from "../api/endpoints";
import { useDebounce } from "../hooks/useDebounce.js";
import WorkCategoryTabs from "./WorkCategoryTabs.jsx";
import WorkFormModal from "./WorkFormModal.jsx";
import WorksTable from "./WorksTable.jsx";

const DEFAULT_SORT = {
  foreign_article: "year",
  local_article: "year",
  thesis: "year",
  patent: "issued_date",
  monograph: "year",
};

export default function ScientificWorksManager() {
  const [activeCategory, setActiveCategory] = useState("foreign_article");
  const [counts, setCounts] = useState({});
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [numPages, setNumPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [sortField, setSortField] = useState(DEFAULT_SORT.foreign_article);
  const [sortDir, setSortDir] = useState("desc");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 400);
  const [projectNames, setProjectNames] = useState([]);

  const [modalState, setModalState] = useState(null); // null | { mode: "add" } | { mode: "edit", work }
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  function fetchCounts() {
    Promise.all(
      WORK_CATEGORIES.map((c) => worksApi.listMine({ category: c.value, page: 1 }))
    )
      .then((results) => {
        const next = {};
        WORK_CATEGORIES.forEach((c, i) => {
          next[c.value] = results[i].data.count;
        });
        setCounts(next);
      })
      .catch(() => {});
  }

  useEffect(fetchCounts, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const ordering = sortField ? `${sortDir === "asc" ? "" : "-"}${sortField}` : undefined;

    worksApi
      .listMine({ category: activeCategory, page, ordering, search: debouncedSearch || undefined })
      .then((res) => {
        if (cancelled) return;
        setRows(res.data.results);
        setNumPages(res.data.num_pages || 1);
        setTotalCount(res.data.count);
        setProjectNames((prev) => {
          const set = new Set(prev);
          res.data.results.forEach((r) => {
            if (r.project_name) set.add(r.project_name);
          });
          return Array.from(set);
        });
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeCategory, page, sortField, sortDir, debouncedSearch]);

  function handleCategoryChange(category) {
    setActiveCategory(category);
    setPage(1);
    setSortField(DEFAULT_SORT[category]);
    setSortDir("desc");
  }

  function handleSortChange(field, dir) {
    setSortField(field);
    setSortDir(dir);
  }

  function refreshAfterChange() {
    setModalState(null);
    fetchCounts();
    worksApi
      .listMine({
        category: activeCategory,
        page,
        ordering: `${sortDir === "asc" ? "" : "-"}${sortField}`,
        search: debouncedSearch || undefined,
      })
      .then((res) => {
        setRows(res.data.results);
        setNumPages(res.data.num_pages || 1);
        setTotalCount(res.data.count);
      });
  }

  async function handleConfirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await worksApi.delete(deleteTarget.id);
      setDeleteTarget(null);
      refreshAfterChange();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-7 shadow-sm shadow-ink/5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">Ilmiy ishlarim</h2>
          <p className="text-sm text-ink-faint">
            {WORK_CATEGORIES.reduce((sum, c) => sum + (counts[c.value] || 0), 0)} ta jami ilmiy ish
          </p>
        </div>
      </div>

      <WorkCategoryTabs
        categories={WORK_CATEGORIES}
        active={activeCategory}
        onChange={handleCategoryChange}
        counts={counts}
      />

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          placeholder="Ishlarim ichidan qidirish…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-line bg-paper px-3.5 py-2 text-sm text-ink focus:border-sand focus:bg-surface focus:outline-none sm:max-w-xs"
        />
        <button
          type="button"
          onClick={() => setModalState({ mode: "add" })}
          className="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark"
        >
          + Qo'shish
        </button>
      </div>

      <div className="mt-4">
        {loading ? (
          <div className="py-16 text-center text-sm text-ink-faint">Yuklanmoqda…</div>
        ) : rows.length === 0 ? (
          <div className="rounded-xl border border-dashed border-line py-16 text-center">
            <p className="text-base font-medium text-ink">Yozuvlar topilmadi</p>
            <p className="mt-1 text-sm text-ink-faint">Yangi yozuv qo'shish uchun "Qo'shish" tugmasini bosing.</p>
          </div>
        ) : (
          <>
            <WorksTable
              category={activeCategory}
              rows={rows}
              sortField={sortField}
              sortDir={sortDir}
              onSortChange={handleSortChange}
              showActions
              onEdit={(work) => setModalState({ mode: "edit", work })}
              onDelete={(work) => setDeleteTarget(work)}
            />
            <p className="mt-3 text-sm text-ink-faint">{totalCount} natijalar</p>

            {numPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-4 text-sm text-ink-soft">
                <button
                  onClick={() => setPage((p) => p - 1)}
                  disabled={page <= 1}
                  className="rounded-lg border border-line px-3.5 py-2 transition hover:border-sand disabled:opacity-40"
                >
                  ← Oldingi
                </button>
                <span>
                  {page} / {numPages} sahifa
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= numPages}
                  className="rounded-lg border border-line px-3.5 py-2 transition hover:border-sand disabled:opacity-40"
                >
                  Keyingi →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {modalState && (
        <WorkFormModal
          category={modalState.mode === "edit" ? modalState.work.category : activeCategory}
          work={modalState.mode === "edit" ? modalState.work : null}
          projectNameSuggestions={projectNames}
          onClose={() => setModalState(null)}
          onSaved={refreshAfterChange}
        />
      )}

      {deleteTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 p-4"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setDeleteTarget(null);
          }}
        >
          <div className="w-full max-w-sm rounded-2xl bg-surface p-6 shadow-2xl">
            <h3 className="mb-2 text-lg font-semibold text-ink">O'chirishni tasdiqlang</h3>
            <p className="mb-5 text-sm text-ink-soft">
              "{deleteTarget.title}" yozuvini o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="flex-1 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink transition hover:border-sand"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="flex-1 rounded-lg bg-danger px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
              >
                {deleting ? "O'chirilmoqda…" : "O'chirish"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
