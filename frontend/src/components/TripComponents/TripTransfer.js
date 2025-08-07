import React from 'react';
import { Card } from 'react-bootstrap';

function TripTransfer({ summary }) {
  const transfers = Array.isArray(summary?.transfers) && summary.transfers.length > 0
  ? summary.transfers
  : [];

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Transfer & Transportation</h5>

        {transfers.length > 0 ? (
          transfers.map((tr, i) => (
            <div key={i} className="mb-4">
              <div className="fw-semibold">{tr.route}</div>
              <div className="text-muted small ms-4">{tr.details}</div>
            </div>
          ))
        ) : (
          <p className="text-muted">No transfer info provided.</p>
        )}

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
