import React from 'react';
import { Card } from 'react-bootstrap';

function TripHighlights({ summary }) {
  const highlights = Array.isArray(summary?.highlights) && summary.highlights.length > 0
  ? summary.highlights
  : [];


  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Highlights</h5>
        {highlights ? (
        <ul className="list-unstyled">
          {highlights.map((line, i) => (
            <li key={i} className="mb-1">✅ {line}</li>
          ))}
        </ul>
      ) : (
        <p className="text-muted">No highlights available yet.</p>
      )}

      </Card.Body>
    </Card>
  );
}

export default TripHighlights;
