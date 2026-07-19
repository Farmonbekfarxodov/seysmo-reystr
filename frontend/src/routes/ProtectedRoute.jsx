import React from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ children }) {
  const { user, initializing } = useAuth();

  if (initializing) {
    return <div className="py-24 text-center text-sm text-ink-faint">Yuklanmoqda…</div>;
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
}
