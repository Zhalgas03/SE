// src/components/admin/UsersTable.jsx
import React from "react";

/** sanitize */
const clean = (val) =>
  typeof val === "string"
    ? val.replace(/[^\x20-\x7Eа-яА-ЯёЁіІїЇґҐ\u0400-\u04FF]/g, "�")
    : val ?? "—";

export default function UsersTable({ users = [], onDelete }) {
  return (
    <section className="mb-4">
      {/* Header bar */}
      <div
        className="d-flex align-items-center justify-content-between px-3 py-2 rounded-top"
        style={{
          background: "#1e88e5",
          color: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,.08)",
        }}
      >
        <div className="fw-semibold">
          <i className="bi bi-people-fill me-2" />
          User Management
        </div>
        <div className="small opacity-75">{users.length} total</div>
      </div>

      {/* Table card */}
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
                <th className="fw-semibold ps-3" style={{ width: 220 }}>
                  Username
                </th>
                <th className="fw-semibold" style={{ width: 300 }}>
                  Email
                </th>
                <th className="fw-semibold" style={{ width: 120 }}>
                  Role
                </th>
                <th className="fw-semibold" style={{ width: 120 }}>
                  2FA
                </th>
                <th className="fw-semibold" style={{ width: 140 }}>
                  Subscribed
                </th>
                <th className="text-end pe-3" style={{ width: 90 }}>
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-4 text-muted">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="border-top">
                    <td className="ps-3">
                      <div className="d-flex align-items-center gap-2">
                        {/* Автарка-инициал */}
                        <div
                          className="rounded-circle d-inline-flex align-items-center justify-content-center"
                          style={{
                            width: 28,
                            height: 28,
                            background: "#e3f2fd",
                            color: "#1565c0",
                            fontSize: 12,
                            fontWeight: 700,
                          }}
                          aria-hidden
                        >
                          {String(u.username || "?").slice(0, 1).toUpperCase()}
                        </div>
                        <span className="fw-semibold">{clean(u.username)}</span>
                      </div>
                    </td>

                    <td className="text-body">{clean(u.email)}</td>

                    <td>
                      <RoleBadge role={u.role} />
                    </td>

                    <td>
                      <StateDot ok={!!u.is_2fa_enabled} okLabel="Enabled" noLabel="Disabled" />
                    </td>

                    <td>
                      <StateDot ok={!!u.is_subscribed} okLabel="Yes" noLabel="No" />
                    </td>

                    <td className="text-end pe-3">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger rounded-pill px-3"
                        onClick={() => onDelete?.(u.id, u.username, u.role)}
                        disabled={u.role === "admin"}
                        title={u.role === "admin" ? "Can't delete admin" : "Delete user"}
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

/* --- UI helpers --- */

function RoleBadge({ role }) {
  const r = String(role || "").toLowerCase();
  const { text, cls } =
    r === "admin"
      ? { text: "Admin", cls: "bg-danger-subtle text-danger" }
      : r === "premium"
      ? { text: "Premium", cls: "bg-warning-subtle text-warning" }
      : { text: "User", cls: "bg-secondary-subtle text-secondary" };

  return (
    <span className={`badge rounded-pill fw-semibold ${cls}`} style={{ padding: "6px 10px" }}>
      {text}
    </span>
  );
}

function StateDot({ ok, okLabel = "Yes", noLabel = "No" }) {
  return ok ? (
    <span className="d-inline-flex align-items-center gap-1">
      <i className="bi bi-dot text-success fs-3 lh-1" />
      <span className="text-success fw-semibold">{okLabel}</span>
    </span>
  ) : (
    <span className="d-inline-flex align-items-center gap-1">
      <i className="bi bi-dot text-danger fs-3 lh-1" />
      <span className="text-danger fw-semibold">{noLabel}</span>
    </span>
  );
}
