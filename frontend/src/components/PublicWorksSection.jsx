import React, { useEffect, useMemo, useState } from "react";

import { worksApi, WORK_CATEGORIES } from "../api/endpoints";
import WorkCategoryTabs from "./WorkCategoryTabs.jsx";
import WorksTable from "./WorksTable.jsx";

export default function PublicWorksSection({ specialistId, worksByCategory }) {
  const availableCategories = useMemo(
    () => WORK_CATEGORIES.filter((c) => (worksByCategory?.[c.value] || 0) > 0),
    [worksByCategory]
  );

  const [activeCategory, setActiveCategory] = useState(availableCategories[0]?.value || null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [numPages, setNumPages] = useState(1);

  useEffect(() => {
    if (!activeCategory) return;
    let cancelled = false;
    setLoading(true);

    worksApi
      .listPublic(specialistId, { category: activeCategory, page })
      .then((res) => {
        if (cancelled) return;
        setRows(res.data.results);
        setNumPages(res.data.num_pages || 1);
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
  }, [specialistId, activeCategory, page]);

  if (availableCategories.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-faint">Ilmiy ishlar</h2>

      <WorkCategoryTabs
        categories={availableCategories}
        active={activeCategory}
        onChange={(cat) => {
          setActiveCategory(cat);
          setPage(1);
        }}
        counts={worksByCategory}
      />

      <div className="mt-4">
        {loading ? (
          <div className="py-10 text-center text-sm text-ink-faint">Yuklanmoqda…</div>
        ) : (
          <>
            <WorksTable category={activeCategory} rows={rows} showActions={false} />

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
    </div>
  );
}
