// components/TripComponents/TripOverview.js
import React from 'react';
import { Card } from 'react-bootstrap';

function TripOverview() {
  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold">Trip Overview</h5>
        <p>
          Dive into a <strong>3-day cultural journey in Rome</strong>, visiting world-famous museums,
          exploring the historic city center, and enjoying authentic Italian cuisine. Highlights include
          the Vatican, the Colosseum, pasta-making workshops, and charming cafés.
        </p>
      </Card.Body>
    </Card>
  );
}

export default TripOverview;
