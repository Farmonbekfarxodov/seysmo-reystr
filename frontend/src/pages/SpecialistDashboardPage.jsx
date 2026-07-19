import React, { useEffect, useRef, useState } from "react";

import { ACADEMIC_TITLES, specialistsApi } from "../api/endpoints";

const STATUS_CLASS = {
  pending: "status-pending",
  approved: "status-approved",
  rejected: "status-rejected",
};

export default function SpecialistDashboardPage() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [error, setError] = useState(null);

  const [uploadError, setUploadError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  function loadProfile() {
    setLoading(true);
    specialistsApi
      .me()
      .then((res) => {
        setProfile(res.data);
        setForm({
          last_name: res.data.last_name,
          first_name: res.data.first_name,
          patronymic: res.data.patronymic || "",
          academic_title: res.data.academic_title,
          direction: res.data.direction,
          bio: res.data.bio || "",
          contact_info: res.data.contact_info || "",
        });
      })
      .catch(() => setError("Could not load your profile."))
      .finally(() => setLoading(false));
  }

  useEffect(loadProfile, []);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setSaveMessage(null);
    setError(null);
    try {
      const res = await specialistsApi.updateMe(form);
      setProfile(res.data);
      setSaveMessage("Profile updated.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save your changes.");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await specialistsApi.uploadDocument(file);
      loadProfile();
    } catch (err) {
      setUploadError(err.response?.data?.file?.[0] || err.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(docId) {
    try {
      await specialistsApi.deleteDocument(docId);
      loadProfile();
    } catch {
      setUploadError("Could not delete that file.");
    }
  }

  if (loading || !form) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Loading your dashboard…
      </div>
    );
  }

  return (
    <div>
      <h1>My profile</h1>
      <p>Edit your public information and manage your credential documents.</p>

      <div className="dashboard-grid">
        <div className="panel">
          <h2>Profile</h2>
          {error && <div className="alert alert-error">{error}</div>}
          {saveMessage && <div className="alert alert-success">{saveMessage}</div>}

          <form className="form" onSubmit={handleSave}>
            <div className="form-row">
              <div className="field">
                <label htmlFor="dash-last-name">Surname</label>
                <input
                  id="dash-last-name"
                  value={form.last_name}
                  onChange={(e) => update("last_name", e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="dash-first-name">Name</label>
                <input
                  id="dash-first-name"
                  value={form.first_name}
                  onChange={(e) => update("first_name", e.target.value)}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="dash-patronymic">Patronymic</label>
              <input
                id="dash-patronymic"
                value={form.patronymic}
                onChange={(e) => update("patronymic", e.target.value)}
              />
            </div>

            <div className="form-row">
              <div className="field">
                <label htmlFor="dash-title">Academic title</label>
                <select
                  id="dash-title"
                  value={form.academic_title}
                  onChange={(e) => update("academic_title", e.target.value)}
                >
                  {ACADEMIC_TITLES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="dash-direction">Direction</label>
                <input
                  id="dash-direction"
                  value={form.direction}
                  onChange={(e) => update("direction", e.target.value)}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="dash-bio">Short bio</label>
              <textarea
                id="dash-bio"
                value={form.bio}
                onChange={(e) => update("bio", e.target.value)}
                maxLength={600}
              />
            </div>

            <div className="field">
              <label htmlFor="dash-contact">Contact info</label>
              <input
                id="dash-contact"
                placeholder="Phone, office, alternate email…"
                value={form.contact_info}
                onChange={(e) => update("contact_info", e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
          </form>
        </div>

        <div className="panel">
          <h2>Credential documents</h2>
          {uploadError && <div className="alert alert-error">{uploadError}</div>}

          {profile.documents.length === 0 ? (
            <p>No documents uploaded yet.</p>
          ) : (
            <div>
              {profile.documents.map((doc) => (
                <div className="doc-row" key={doc.id}>
                  <span className="doc-name">{doc.original_filename}</span>
                  <span className={`status-badge ${STATUS_CLASS[doc.status]}`}>{doc.status}</span>
                  <button className="btn btn-danger" onClick={() => handleDelete(doc.id)}>
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}

          <hr className="divider" />

          <label className="file-drop">
            {uploading ? "Uploading…" : "Upload a new document (PDF, JPG, PNG · up to 5 MB)"}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleUpload}
              disabled={uploading || profile.documents.length >= 5}
              style={{ display: "none" }}
            />
          </label>
          {profile.documents.length >= 5 && (
            <p className="hint" style={{ marginTop: 8 }}>
              You have reached the maximum of 5 documents. Delete one to upload another.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
