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
          // ❗ оставим только поездки с PDF    
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

  if (loading) return <p>Loading...</p>;
  if (trips.length === 0) return <p>No saved trips with PDF yet.</p>;

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
              <a
                className="btn btn-outline-primary btn-sm"
                href={`http://localhost:5001/${trip.pdf_file_path}`}
                download
                target="_blank"
                rel="noopener noreferrer"
              >
                📥 Download PDF
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Favorites;
