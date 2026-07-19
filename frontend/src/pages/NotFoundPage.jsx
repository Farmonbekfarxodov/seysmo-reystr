import React from "react";
import { Link } from "react-router-dom";

import Seismogram from "../components/Seismogram.jsx";
import uz from "../i18n/uz.js";

export default function NotFoundPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-5 py-24 text-center">
      <p className="font-display text-7xl font-semibold text-sand">{uz.notFound.title}</p>
      <Seismogram className="mt-4 h-8 w-64 text-ink-faint" />
      <p className="mt-4 text-ink-soft">{uz.notFound.body}</p>
      <Link
        to="/"
        className="mt-6 rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-sand-dark"
      >
        {uz.notFound.backHome}
      </Link>
    </div>
  );
}
