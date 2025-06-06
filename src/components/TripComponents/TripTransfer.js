import React from 'react';
import { Card } from 'react-bootstrap';

function TripTransfer() {
  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Transfer & Transportation</h5>

        <div className="mb-4">
          <div className="fw-semibold">🚗 Milan, Italy → Rome, Italy</div>
          <div className="text-muted small ms-4">Wed, Jul 2 • 5h 34m • Non-stop</div>
        </div>

        <div>
          <div className="fw-semibold">🚗 Rome, Italy → Milan, Italy</div>
          <div className="text-muted small ms-4">Sat, Jul 5 • 5h 21m • Non-stop</div>
        </div>

        <div className="mt-3" style={{ height: '250px', borderRadius: '10px', background: '#f0f0f0' }}>
          <div className="d-flex justify-content-center align-items-center h-100 text-muted">
            Route map preview (future)
          </div>
        </div>
      </Card.Body>
    </Card>
  );
}

export default TripTransfer;
