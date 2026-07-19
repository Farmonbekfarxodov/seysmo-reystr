import React from "react";

import uz from "../i18n/uz.js";

const CONFIG = {
  pending: {
    label: uz.status.pending,
    hint: uz.status.pendingHint,
    badge: "bg-warning-tint text-warning",
    banner: "border-warning/30 bg-warning-tint text-warning",
  },
  approved: {
    label: uz.status.approved,
    hint: uz.status.approvedHint,
    badge: "bg-success-tint text-success",
    banner: "border-success/30 bg-success-tint text-success",
  },
  rejected: {
    label: uz.status.rejected,
    hint: uz.status.rejectedHint,
    badge: "bg-danger-tint text-danger",
    banner: "border-danger/30 bg-danger-tint text-danger",
  },
};

export function StatusBadge({ status }) {
  const cfg = CONFIG[status] || CONFIG.pending;
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${cfg.badge}`}>
      {cfg.label}
    </span>
  );
}

export function StatusBanner({ status, rejectionReason }) {
  const cfg = CONFIG[status] || CONFIG.pending;
  return (
    <div className={`rounded-xl border p-4 text-sm ${cfg.banner}`}>
      <p className="font-semibold">{cfg.label}</p>
      <p className="mt-1 opacity-90">{cfg.hint}</p>
      {status === "rejected" && rejectionReason && (
        <p className="mt-2">
          <span className="font-semibold">{uz.status.rejectionReasonLabel}</span> {rejectionReason}
        </p>
      )}
    </div>
  );
}
