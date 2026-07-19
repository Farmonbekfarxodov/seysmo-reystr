import React from "react";

import uz from "../i18n/uz.js";

export default function SearchBar({ name, department, departments, onNameChange, onDepartmentChange }) {
  return (
    <div className="flex w-full max-w-2xl flex-col gap-2 rounded-2xl border border-line bg-surface p-2 shadow-lg shadow-ink/5 sm:flex-row sm:items-center">
      <input
        type="text"
        placeholder={uz.search.placeholder}
        value={name}
        onChange={(e) => onNameChange(e.target.value)}
        aria-label={uz.search.placeholder}
        className="flex-1 rounded-xl bg-transparent px-4 py-3 text-base text-ink placeholder:text-ink-faint focus:outline-none"
      />
      <select
        value={department}
        onChange={(e) => onDepartmentChange(e.target.value)}
        aria-label={uz.search.department}
        className="rounded-xl bg-paper px-4 py-3 text-sm text-ink-soft focus:outline-none sm:max-w-56"
      >
        <option value="">{uz.search.allDepartments}</option>
        {departments.map((d) => (
          <option key={d.id} value={d.slug}>
            {d.name}
          </option>
        ))}
      </select>
    </div>
  );
}
