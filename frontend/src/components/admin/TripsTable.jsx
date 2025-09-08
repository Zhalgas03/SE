// src/components/admin/TripsTable.jsx
import React from "react";

const clean = (val) =>
  typeof val === "string"
    ? val.replace(/[^\x20-\x7Eа-яА-ЯёЁіІїЇґҐ\u0400-\u04FF]/g, "�")
    : val ?? "—";

export default function TripsTable({ trips = [], onDelete }) {
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
          <i className="bi bi-airplane-fill me-2" />
          Trips
        </div>
        <div className="small opacity-75">{trips.length} total</div>
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
                <th className="fw-semibold ps-3">Name</th>
                <th className="fw-semibold">Start</th>
                <th className="fw-semibold">End</th>
                <th className="fw-semibold">Creator</th>
                <th className="text-end pe-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {trips.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-4 text-muted">
                    No trips found
                  </td>
                </tr>
              ) : (
                trips.map((t) => (
                  <tr key={t.id} className="border-top">
                    <td className="ps-3 fw-semibold">{clean(t.name)}</td>
                    <td>{formatDate(t.date_start)}</td>
                    <td>{formatDate(t.date_end)}</td>
                    <td>
                      <span className="badge bg-light text-dark">
                        {clean(t.creator_username)}
                      </span>
                    </td>
                    <td className="text-end pe-3">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger rounded-pill px-3"
                        onClick={() => onDelete?.(t.id, t.name)}
                        title="Delete trip"
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
function formatDate(val) {
  if (!val) return "—";
  try {
    return new Date(val).toLocaleDateString();
  } catch {
    return clean(val);
  }
}
