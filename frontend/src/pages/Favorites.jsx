// Favorites.jsx
import React, { useCallback, useEffect, useState } from "react";
import TripOfTheWeek from "../components/TripOfTheWeek";
import SavedTrips from "../components/SavedTrips";
import { useUser } from "../context/UserContext"; // 👈

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5001";

export default function Favorites() {
  const [trips, setTrips] = useState([]);
  const [loadingTrips, setLoadingTrips] = useState(true);
  const { isPremium } = useUser(); // 👈

  const refreshTrips = useCallback(async () => {
    setLoadingTrips(true);
    try {
      const res = await fetch(`${API_BASE}/api/trips/favorites`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
      });
      const data = await res.json();
      if (data?.success) setTrips((data.trips || []).filter((t) => t.pdf_file_path));
    } catch (e) {
      console.error("favorites fetch failed", e);
    } finally {
      setLoadingTrips(false);
    }
  }, []);

  useEffect(() => { refreshTrips(); }, [refreshTrips]);

  return (
    <div className="container fav-container">
      {/* Премиум-гейт: показываем баннер только премиум-юзерам */}
      {isPremium && (
        <TripOfTheWeek
          apiBase={API_BASE}
          trips={trips}
          onSaved={refreshTrips}
        />
      )}
      <SavedTrips
        apiBase={API_BASE}
        trips={trips}
        loading={loadingTrips}
        onRefresh={refreshTrips}
        setTrips={setTrips}
      />
    </div>
  );
}
