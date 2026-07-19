import React, { useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";

import LoginModal from "./components/LoginModal.jsx";
import RegisterModal from "./components/RegisterModal.jsx";
import Seismogram from "./components/Seismogram.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import uz from "./i18n/uz.js";
import DashboardPage from "./pages/DashboardPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import SpecialistDetailPage from "./pages/SpecialistDetailPage.jsx";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";

export default function App() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeModal, setActiveModal] = useState(null); // null | "login" | "register"
  const [prefillLogin, setPrefillLogin] = useState("");

  function openLogin(prefill = "") {
    setPrefillLogin(prefill);
    setActiveModal("login");
  }

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <Link to="/" className="flex items-center gap-2.5 text-ink">
          <img src="/logo.jpg" alt={uz.common.instituteName} className="h-8 w-8 rounded-full object-cover" />
          <span className="font-display text-lg font-semibold">{uz.common.instituteName}</span>
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-ink transition hover:border-sand"
              >
                {uz.dashboard.title}
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-ink transition hover:border-sand"
              >
                {uz.common.logout}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => openLogin()}
                className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-ink transition hover:border-sand"
              >
                {uz.common.login}
              </button>
              <button
                onClick={() => setActiveModal("register")}
                className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-sand-dark"
              >
                {uz.common.register}
              </button>
            </>
          )}
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/specialists/:id" element={<SpecialistDetailPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      <footer className="mt-10 bg-ink px-6 py-8 text-center sm:px-10">
        <Seismogram className="mx-auto mb-4 h-6 w-48 text-white/20" strokeWidth={1.5} />
        <p className="text-sm text-white/70">
          {uz.common.instituteName} — {uz.common.registryName}
        </p>
      </footer>

      {activeModal === "login" && (
        <LoginModal
          onClose={() => setActiveModal(null)}
          onSwitchToRegister={() => setActiveModal("register")}
          prefillLogin={prefillLogin}
        />
      )}
      {activeModal === "register" && (
        <RegisterModal
          onClose={() => setActiveModal(null)}
          onSwitchToLogin={(username) => openLogin(username || "")}
        />
      )}
    </div>
  );
}
