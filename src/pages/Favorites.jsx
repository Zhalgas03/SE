import React, { useEffect, useState } from 'react';
import PdfViewer from "../components/PdfViewer";
function Favorites() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPdf, setSelectedPdf] = useState(null);
  
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const res = await fetch("http://localhost:5001/api/trips/favorites", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        });
        const data = await res.json();
        if (data.success) {
          const filtered = data.trips.filter(trip => trip.pdf_file_path);
          setTrips(filtered);
        } else {
          alert("Failed to load trips.");
        }
      } catch (err) {
        console.error("Error fetching trips:", err);
        alert("Server error.");
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, []);

  const handleDelete = async (tripId) => {
    if (!window.confirm("Are you sure you want to delete this trip?")) return;

    try {
      const res = await fetch(`http://localhost:5001/api/trips/${tripId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`
        }
      });
      const data = await res.json();
      if (data.success) {
        setTrips(prev => prev.filter(trip => trip.id !== tripId));
      } else {
        alert("Failed to delete trip.");
      }
    } catch (err) {
      console.error("Error deleting trip:", err);
      alert("Server error.");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (trips.length === 0) {
    return (
      <div className="text-center py-5">
        <img src="/no-trips.svg" height="150" alt="No trips" />
        <p className="mt-3 text-muted">You haven't saved any trips yet.</p>
        <a className="btn btn-primary mt-2" href="/planner">Start Planning</a>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <h3 className="fw-bold mb-4">📄 Saved Trips</h3>
      <div className="row row-cols-1 row-cols-md-2 g-4">
        {trips.map(trip => (
          <div className="col" key={trip.id}>
            <div className="card shadow-sm rounded-4 p-3">
              <h5 className="fw-bold">{trip.name}</h5>
              <p className="text-muted small">
                {trip.date_start?.split('T')[0]} → {trip.date_end?.split('T')[0]}
              </p>
<div className="d-flex flex-wrap gap-2 mt-3">
  <button
    className="btn btn-outline-primary btn-sm"
    onClick={() => setSelectedPdf(`http://localhost:5001/${trip.pdf_file_path}`)}
  >
    📄 View
  </button>
  <button
    className="btn btn-outline-danger btn-sm"
    onClick={() => handleDelete(trip.id)}
  >
    🗑 Delete
  </button>
<button
  className="btn btn-outline-secondary btn-sm"
  onClick={async () => {
    try {
      await fetch(`http://localhost:5001/api/voting-rules/enable`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ trip_id: trip.id })
      });

      const guestLink = `http://localhost:3000/guest-vote/${trip.id}`;
      await navigator.clipboard.writeText(guestLink);
      alert("Voting link copied:\n" + guestLink);
    } catch (err) {
      console.error("Voting error:", err);
      alert("Failed to create voting link.");
    }
  }}
>
  🗳 Voting
</button>

</div>

            </div>
          </div>
        ))}
      </div>

{selectedPdf && (
  <div
    className="modal d-block bg-dark bg-opacity-75"
    tabIndex="-1"
    onClick={() => setSelectedPdf(null)}
    style={{ zIndex: 1050 }}
  >
    <div
      className="modal-dialog modal-xl modal-dialog-centered"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="modal-content">
        <div className="modal-header justify-content-between">
          <h5 className="modal-title">Trip Overview</h5>
          <div className="d-flex gap-2">
            <button
              className="btn btn-outline-danger btn-sm"
              onClick={() => {
                const trip = trips.find(t => `http://localhost:5001/${t.pdf_file_path}` === selectedPdf);
                if (trip) handleDelete(trip.id);
                setSelectedPdf(null);
              }}
            >
              🗑 Delete
            </button>
<button
  className="btn btn-outline-secondary btn-sm"
  onClick={async () => {
    const trip = trips.find(t => `http://localhost:5001/${t.pdf_file_path}` === selectedPdf);
    if (!trip) return;
    try {
      await fetch(`http://localhost:5001/api/voting-rules/enable`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ trip_id: trip.id })
      });

      const guestLink = `http://localhost:3000/guest-vote/${trip.id}`;
      await navigator.clipboard.writeText(guestLink);
      alert("Voting link copied:\n" + guestLink);
    } catch (err) {
      console.error("Voting error:", err);
      alert("Failed to create voting link.");
    }
  }}
>
  🗳 Voting
</button>

            <button
              type="button"
              className="btn-close"
              onClick={() => setSelectedPdf(null)}
            ></button>
          </div>
        </div>
<div
  className="modal-body d-flex justify-content-center"
  style={{
    maxHeight: "80vh",
    overflowY: "auto",
    padding: "1rem",
    backgroundColor: "#f8f9fa",

  
  }}
>
  <PdfViewer url={selectedPdf} />
</div>
      </div>
    </div>
  </div>
)}


    </div>
    
  );
}

export default Favorites;
