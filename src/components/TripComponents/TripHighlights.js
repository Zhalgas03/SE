import React from 'react';
import { Card } from 'react-bootstrap';

function TripHighlights() {
  const highlights = [
    "✅ Visit the Vatican Museums and Sistine Chapel",
    "✅ Explore Piazza Navona and Trevi Fountain",
    "✅ Pasta-making workshop with wine tasting",
    "✅ Tour of the Colosseum and Roman Forum"
  ];

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Highlights</h5>
        <ul className="list-unstyled">
          {highlights.map((line, i) => (
            <li key={i} className="mb-1">{line}</li>
          ))}
        </ul>
      </Card.Body>
    </Card>
  );
}

export default TripHighlights;
