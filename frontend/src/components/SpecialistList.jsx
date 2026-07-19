import React from "react";

import uz from "../i18n/uz.js";
import SpecialistCard from "./SpecialistCard.jsx";

function SkeletonCard() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-line bg-surface p-6">
      <div className="skeleton h-20 w-20 rounded-full" />
      <div className="skeleton h-4 w-32 rounded" />
      <div className="skeleton h-3 w-24 rounded" />
      <div className="skeleton h-5 w-20 rounded-full" />
    </div>
  );
}

export default function SpecialistList({ loading, results, page, numPages, onPageChange }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-line py-16 text-center">
        <p className="text-base font-medium text-ink">{uz.search.empty}</p>
        <p className="mt-1 text-sm text-ink-faint">{uz.search.emptyHint}</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((specialist) => (
          <SpecialistCard key={specialist.id} specialist={specialist} />
        ))}
      </div>

      {numPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-4 text-sm text-ink-soft">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-lg border border-line px-3.5 py-2 transition hover:border-sand disabled:opacity-40"
          >
            {uz.search.prev}
          </button>
          <span>{uz.search.page(page, numPages)}</span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= numPages}
            className="rounded-lg border border-line px-3.5 py-2 transition hover:border-sand disabled:opacity-40"
          >
            {uz.search.next}
          </button>
        </div>
      )}
    </>
  );
}
