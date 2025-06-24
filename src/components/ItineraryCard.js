// src/components/ItineraryCard.jsx
import React from 'react';
import './ItineraryCard.css'; // 👈 подключим кастомный стиль

function ItineraryCard({ day, title, activity, hotel, weather }) {
  return (
    <div className="card itinerary-card fade-in mb-4 border-0 shadow-sm rounded-4">
      <div className="card-body">
        <h5 className="fw-bold mb-3">
          📅 Day {day}: <span className="text-dark">{title}</span>
        </h5>
        <ul className="list-unstyled ms-2">
          <li><span className="fw-semibold">📍 Activity:</span> {activity}</li>
          <li><span className="fw-semibold">🏨 Hotel:</span> {hotel}</li>
          <li><span className="fw-semibold">🌤️ Weather:</span> {weather}</li>
        </ul>
      </div>
    </div>
  );
}

export default ItineraryCard;
