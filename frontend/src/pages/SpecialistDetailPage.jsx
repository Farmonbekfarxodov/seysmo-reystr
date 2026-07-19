import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { specialistsApi } from "../api/endpoints";
import uz from "../i18n/uz.js";

function initials(fullName) {
  const parts = (fullName || "?").trim().split(" ");
  return parts.slice(0, 2).map((p) => p.charAt(0)).join("").toUpperCase();
}

export default function SpecialistDetailPage() {
  const { id } = useParams();
  const [specialist, setSpecialist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFound(false);

    specialistsApi
      .detail(id)
      .then((res) => {
        if (!cancelled) setSpecialist(res.data);
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return <div className="flex-1 py-24 text-center text-sm text-ink-faint">{uz.common.loading}</div>;
  }

  if (notFound) {
    return (
      <div className="mx-auto max-w-2xl px-5 py-16">
        <div className="rounded-xl border border-danger/30 bg-danger-tint px-4 py-3 text-sm text-danger">
          {uz.detail.notFound}
        </div>
        <Link to="/" className="mt-4 inline-block text-sm font-medium text-sand-dark underline underline-offset-2">
          {uz.detail.backToSearch}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-5 py-16">
      <Link to="/" className="text-sm font-medium text-sand-dark underline underline-offset-2">
        {uz.detail.backToSearch}
      </Link>

      <div className="mt-6 rounded-2xl border border-line bg-surface p-8 shadow-sm shadow-ink/5">
        <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
          {specialist.photo ? (
            <img src={specialist.photo} alt="" className="h-28 w-28 rounded-full object-cover ring-4 ring-sand-tint" />
          ) : (
            <div className="flex h-28 w-28 items-center justify-center rounded-full bg-sand-tint text-3xl font-semibold text-sand-dark ring-4 ring-sand-tint">
              {initials(specialist.full_name)}
            </div>
          )}
          <div>
            <h1 className="text-2xl font-semibold text-ink">{specialist.full_name}</h1>
            <p className="mt-1 text-sm text-ink-soft">
              {[specialist.academic_degree, specialist.academic_title, specialist.position]
                .filter((v) => v && v !== "Yo'q")
                .join(" · ")}
            </p>
            <span className="mt-2 inline-block rounded-full bg-sand-tint px-3 py-1 text-xs font-medium text-sand-dark">
              {specialist.department}
            </span>
          </div>
        </div>

        {specialist.research_interests && (
          <div className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-faint">
              {uz.detail.researchInterests}
            </h2>
            <p className="mt-2 text-ink-soft">{specialist.research_interests}</p>
          </div>
        )}

        {specialist.bio && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-faint">{uz.detail.about}</h2>
            <p className="mt-2 text-ink-soft">{specialist.bio}</p>
          </div>
        )}

        <div className="mt-8">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-faint">{uz.detail.documents}</h2>
          {specialist.documents && specialist.documents.length > 0 ? (
            <ul className="mt-2 flex flex-col gap-2">
              {specialist.documents.map((doc) => (
                <li key={doc.id}>
                  <a
                    href={doc.file}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-line bg-paper px-3.5 py-2 text-sm text-sand-dark underline underline-offset-2 transition hover:border-sand"
                  >
                    {doc.original_filename}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-ink-faint">{uz.detail.noDocuments}</p>
          )}
        </div>
      </div>
    </div>
  );
}
