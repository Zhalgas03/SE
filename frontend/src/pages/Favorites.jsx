import React, { useEffect, useState } from 'react';

function Favorites() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);

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
              <div className="d-flex justify-content-between align-items-center">
                <a
                  className="btn btn-outline-primary btn-sm"
                  href={`http://localhost:5001/${trip.pdf_file_path}`}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  📥 Overview
                </a>
                <button
                  className="btn btn-outline-danger btn-sm ms-2"
                  onClick={() => handleDelete(trip.id)}
                >
                  🗑 Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Favorites;
