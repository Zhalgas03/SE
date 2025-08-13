// src/pages/Favorites.jsx
import React from "react";
import TripOfTheWeek from "../components/TripOfTheWeek";
import SavedTrips from "../components/SavedTrips";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5001";

export default function Favorites() {
  return (
    <div className="container fav-container">
      <TripOfTheWeek apiBase={API_BASE} />
      <SavedTrips apiBase={API_BASE} />
    </div>
  );
}
