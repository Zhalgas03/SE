import React, { useMemo, useState } from "react";
import PdfViewer from "./PdfViewer";
import CreateVotingModal from "./CreateVotingModal";
import "../pages/Favorites.css";

const PAGE_SIZE = 6;

export default function SavedTrips({
  apiBase = "http://localhost:5001",
  trips = [],                 // ✔ приходит сверху
  setTrips,                   // ✔ чтобы убирать удалённые локально
  loading = false,            // ✔ состояние загрузки из родителя
  onRefresh,                  // ✔ рефреш с сервера
}) {
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [origin, setOrigin] = useState({ x: 0, y: 0 });
  const [page, setPage] = useState(1);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(trips.length / PAGE_SIZE)),
    [trips.length]
  );

  if (page > totalPages) setTimeout(() => setPage(totalPages), 0);

  const pagedTrips = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return trips.slice(start, start + PAGE_SIZE);
  }, [trips, page]);

  const handleDelete = async (tripId) => {
    if (!window.confirm("Are you sure you want to delete this trip?")) return;
    try {
      const res = await fetch(`${apiBase}/api/trips/${tripId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
      });
      const data = await res.json();
      if (data.success) {
        // локально снём
        setTrips?.((prev) => prev.filter((t) => t.id !== tripId));
        // и подстрахуемся актуализацией
        onRefresh?.();
        setSelectedPdf(null);
      } else {
        alert("Failed to delete trip.");
      }
    } catch (err) {
      console.error("Error deleting trip:", err);
      alert("Server error.");
    }
  };

  const Pagination = () => {
    const pages = [];
    const push = (n) => pages.push(n);
    const addRange = (a, b) => { for (let i = a; i <= b; i++) push(i); };
    if (totalPages <= 7) addRange(1, totalPages);
    else {
      const left = Math.max(2, page - 1);
      const right = Math.min(totalPages - 1, page + 1);
      push(1); if (left > 2) push("…"); addRange(left, right);
      if (right < totalPages - 1) push("…"); push(totalPages);
    }
    if (totalPages <= 1) return null;
    return (
      <nav className="d-flex justify-content-center fav-pagination">
        <ul className="pagination mb-0">
          <li className={`page-item ${page === 1 ? "disabled" : ""}`}>
            <button className="page-link" onClick={() => setPage((p) => Math.max(1, p - 1))}>‹ Prev</button>
          </li>
          {pages.map((p, idx) => (
            <li key={idx} className={`page-item ${p === page ? "active" : ""} ${p === "…" ? "disabled" : ""}`}>
              {p === "…" ? <span className="page-link">…</span> :
                <button className="page-link" onClick={() => setPage(p)}>{p}</button>}
            </li>
          ))}
          <li className={`page-item ${page === totalPages ? "disabled" : ""}`}>
            <button className="page-link" onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next ›</button>
          </li>
        </ul>
      </nav>
    );
  };

  if (loading) return <p className="py-4">Loading...</p>;

  return (
    <>
      <div className="d-flex align-items-center justify-content-between mb-2">
        <h3 className="fw-bold mb-4">📄 Saved Trips</h3>
        <small className="text-muted">
          Page {page} of {totalPages} • {trips.length} total
        </small>
      </div>

      {trips.length === 0 ? (
        <div className="text-center py-5">
          <img src="/no-trips.svg" height="150" alt="No trips" />
          <p className="mt-3 text-muted">You haven't saved any trips yet.</p>
          <a className="btn btn-primary mt-2" href="/planner">Start Planning</a>
        </div>
      ) : (
        <>
          <div className="row row-cols-1 row-cols-md-2 g-4 mt-3 fav-grid">
            {pagedTrips.map((trip) => (
              <div className="col" key={trip.id}>
                <div className="card fav-card rounded-4 p-3">
                  <h5 className="fw-bold">{trip.name}</h5>
                  <p className="text-muted small mb-2">
                    {trip.date_start?.split("T")[0]} → {trip.date_end?.split("T")[0]}
                  </p>
                  <div className="d-flex justify-content-between align-items-center">
                    <button
                      className="btn btn-outline-primary btn-sm"
                      onClick={() => setSelectedPdf(`${apiBase}/${trip.pdf_file_path}`)}
                    >
                      📄 View
                    </button>
                    <div className="d-flex gap-2">
<button
  className="btn btn-outline-secondary btn-sm"
  onClick={(e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setOrigin({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 });
    setSelectedTrip(trip); // ← ЭТО ГЛАВНОЕ
  }}
>
  🗳 Create poll
</button>
                      <button
                        className="btn btn-outline-danger btn-sm ms-2"
                        onClick={() => handleDelete(trip.id)}
                      >
                        🗑 Delete
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-3">
            <Pagination />
          </div>
        </>
      )}

      {selectedPdf && (
        <div
          className="modal d-block bg-dark bg-opacity-75 themed-modal"
          tabIndex="-1"
          onClick={() => setSelectedPdf(null)}
          style={{ zIndex: 1050 }}
        >
          <div
            className="modal-dialog modal-dialog-centered"
            style={{ maxWidth: "880px", width: "100%" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-content">
              <div className="modal-header justify-content-between">
                <h5 className="modal-title">Trip Overview</h5>
                <div className="d-flex gap-2">
                  <button
                    className="btn btn-outline-danger btn-sm"
                    onClick={() => {
                      const trip = trips.find((t) => `${apiBase}/${t.pdf_file_path}` === selectedPdf);
                      if (trip) handleDelete(trip.id);
                    }}
                  >
                    🗑 Delete
                  </button>
                  <button type="button" className="btn-close" onClick={() => setSelectedPdf(null)} />
                </div>
              </div>
              <div className="modal-body" style={{ maxHeight: "80vh", overflowY: "auto", padding: "1rem" }}>
                <div className="w-100">
                  <PdfViewer url={selectedPdf} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <CreateVotingModal
        open={!!selectedTrip}
        onClose={() => setSelectedTrip(null)}
        trip={selectedTrip}
        origin={origin}
      />
    </>
  );
}
