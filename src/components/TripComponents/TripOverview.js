import React from 'react';
import { Card } from 'react-bootstrap';

function TripOverview({ summary }) {
  const overview = typeof summary?.overview === 'string' && summary.overview.trim()
  ? summary.overview.trim()
  : 'No overview available yet.';

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold">Trip Overview</h5>
        <p>{overview}</p>
      </Card.Body>
    </Card>
  );
}

export default TripOverview;
