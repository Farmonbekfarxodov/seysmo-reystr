import React from "react";

export default function CategoryTabs({ categories, active, onChange, counts = {} }) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-line pb-3">
      {categories.map((cat) => {
        const isActive = cat.value === active;
        const count = counts[cat.value] ?? 0;
        return (
          <button
            key={cat.value}
            type="button"
            onClick={() => onChange(cat.value)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              isActive
                ? "bg-ink text-white"
                : "bg-paper text-ink-soft hover:bg-sand-tint hover:text-sand-dark"
            }`}
          >
            {cat.tabLabel} ({count})
          </button>
        );
      })}
    </div>
  );
}
