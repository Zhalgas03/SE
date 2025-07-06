import React from 'react';

function TripHeader({ summary }) {
  if (!summary) {
    return (
      <div className="mb-4">
        <h2 className="fw-bold">Trip Plan</h2>
        <div className="text-muted">📅 Dates not set</div>
      </div>
    );
  }

  const {
    destination,
    origin,
    travel_dates,
    activities,
    style,
    budget,
    trip_name,
    dates,
    tags
  } = summary;

  const title = trip_name || `Trip from ${origin || 'Origin'} to ${destination || 'Destination'}`;
  const displayDates = dates || (travel_dates ? `📅 ${travel_dates}` : '📅 Dates not set');

  const defaultTags = [
    activities ? `🎯 ${activities}` : null,
    style ? `💼 ${style}` : null,
    budget ? `💰 ${budget}` : null,
  ].filter(Boolean);

  const displayTags = Array.isArray(tags) && tags.length > 0 ? tags : defaultTags;

  return (
    <div className="d-flex justify-content-between align-items-start mb-4">
      <div>
        <h2 className="fw-bold">{title}</h2>
        <div className="mb-2 text-muted">{displayDates}</div>
        <div>
          {displayTags.map((tag, i) => (
            <span key={i} className="badge bg-primary me-2">{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TripHeader;
