import React from 'react';

// Функция форматирования дат
function formatTravelDates(datesString) {
  if (!datesString) return null;

  // Ищем два диапазона дат, поддержка "10.08 to 12.08" или "10th August to 12th August 2025"
  const regex = /(\d{1,2}(?:st|nd|rd|th)?\s?\w*\s?\d{0,4})\s*(?:to|-)\s*(\d{1,2}(?:st|nd|rd|th)?\s?\w*\s?\d{0,4})/i;
  const match = datesString.match(regex);

  if (match) {
    const start = match[1].replace(/st|nd|rd|th/gi, '');
    const end = match[2].replace(/st|nd|rd|th/gi, '');
    return `${start} – ${end}`;
  }

  // Если формат другой (например, просто одна дата)
  return datesString;
}

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
    tags
  } = summary;

  const title = trip_name || `Trip from ${origin || 'Origin'} to ${destination || 'Destination'}`;

  // Используем функцию форматирования
  const displayDates = travel_dates ? `📅 ${formatTravelDates(travel_dates)}` : '📅 Dates not set';

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