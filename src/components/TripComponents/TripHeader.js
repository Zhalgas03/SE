import React from 'react';
import { Button } from 'react-bootstrap';

function TripHeader() {
  return (
    <div className="d-flex justify-content-between align-items-start mb-4">
      <div>
        <h2 className="fw-bold">3-Day Cultural Trip to Rome</h2>
        <div className="mb-2 text-muted">📅 Jul 2 – Jul 5 • 🧍 Solo traveler</div>
        <div>
          <span className="badge bg-primary me-2">Museums</span>
          <span className="badge bg-info text-dark me-2">Cafes</span>
          <span className="badge bg-danger">Solo Trip</span>
        </div>
      </div>
    </div>
  );
}

export default TripHeader;
