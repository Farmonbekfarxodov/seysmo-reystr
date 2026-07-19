import React from "react";
import { useNavigate } from "react-router-dom";

function initials(fullName) {
  const parts = (fullName || "?").trim().split(" ");
  return parts.slice(0, 2).map((p) => p.charAt(0)).join("").toUpperCase();
}

export default function SpecialistCard({ specialist }) {
  const navigate = useNavigate();

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/specialists/${specialist.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter") navigate(`/specialists/${specialist.id}`);
      }}
      className="flex cursor-pointer flex-col items-center gap-3 rounded-2xl border border-line bg-surface p-6 text-center shadow-sm shadow-ink/5 transition hover:-translate-y-0.5 hover:border-sand/60 hover:shadow-lg hover:shadow-sand/10"
    >
      {specialist.photo_thumbnail ? (
        <img
          src={specialist.photo_thumbnail}
          alt=""
          className="h-20 w-20 rounded-full object-cover ring-2 ring-line"
        />
      ) : (
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-sand-tint text-xl font-semibold text-sand-dark ring-2 ring-line">
          {initials(specialist.full_name)}
        </div>
      )}
      <div>
        <h3 className="text-base font-semibold text-ink">{specialist.full_name}</h3>
        <p className="mt-0.5 text-sm text-ink-soft">
          {[specialist.academic_degree, specialist.position].filter((v) => v && v !== "Yo'q").join(" · ")}
        </p>
        <span className="mt-2 inline-block rounded-full bg-sand-tint px-2.5 py-1 text-xs font-medium text-sand-dark">
          {specialist.department}
        </span>
      </div>
    </article>
  );
}
