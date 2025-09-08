// src/components/admin/VotesTable.jsx
import React from "react";

const clean = (val) =>
  typeof val === "string"
    ? val.replace(/[^\x20-\x7Eа-яА-ЯёЁіІїЇґҐ\u0400-\u04FF]/g, "�")
    : val ?? "—";

export default function VotesTable({ votes = [], onDelete }) {
  return (
    <section className="mb-4">
      {/* Header */}
      <div
        className="d-flex align-items-center justify-content-between px-3 py-2 rounded-top"
        style={{
          background: "#1e88e5",
          color: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,.08)",
        }}
      >
        <div className="fw-semibold">
          <i className="bi bi-boxes me-2" />
          Voting Sessions
        </div>
        <div className="small opacity-75">{votes.length} total</div>
      </div>

      {/* Table */}
      <div
        className="rounded-bottom"
        style={{
          border: "1px solid #e9ecef",
          borderTop: "none",
          boxShadow: "0 2px 4px rgba(0,0,0,.04)",
          overflow: "hidden",
        }}
      >
        <div className="table-responsive">
          <table className="table mb-0 align-middle" style={{ fontSize: 14 }}>
            <thead style={{ background: "#f8f9fa" }}>
              <tr className="text-muted">
                <th className="fw-semibold ps-3">Title</th>
                <th className="fw-semibold">Status</th>
                <th className="fw-semibold">Expires</th>
                <th className="fw-semibold">Creator</th>
                <th className="text-end pe-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {votes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-4 text-muted">
                    No voting sessions found
                  </td>
                </tr>
              ) : (
                votes.map((v) => (
                  <tr key={v.id} className="border-top">
                    <td className="ps-3 fw-semibold">{clean(v.title)}</td>
                    <td>
                      <StatusBadge status={v.status} />
                    </td>
                    <td>{v.expires_at ? new Date(v.expires_at).toLocaleString() : "—"}</td>
                    <td>
                      <span className="badge bg-light text-dark">
                        {clean(v.creator_username)}
                      </span>
                    </td>
                    <td className="text-end pe-3">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger rounded-pill px-3"
                        onClick={() => onDelete?.(v.id, v.title)}
                        title="Delete voting session"
                      >
                        <i className="bi bi-trash-fill me-1" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

/* --- helpers --- */
function StatusBadge({ status }) {
  const map = {
    active: "success",
    completed: "secondary",
    pending: "warning",
    expired: "danger",
  };
  const variant = map[status?.toLowerCase()] || "light";
  return <span className={`badge bg-${variant}`}>{clean(status)}</span>;
}
