import React from 'react';
import { Card, Accordion } from 'react-bootstrap';
import MapPreview from '../MapPreview';

function TripItinerary({ summary, isGeneratingPDF }) {
  const itinerary = Array.isArray(summary?.itinerary) && summary.itinerary.length > 0
  ? summary.itinerary
  : [];
  const intro = summary?.itinerary_intro || 'No itinerary available.';

  return (
    <Card className="mb-4 shadow-sm" style={{ overflow: 'visible' }}>
      <Card.Body>
        <h5 className="fw-bold mb-3">Itinerary</h5>

        {intro && <p>{intro}</p>}

        {!isGeneratingPDF && (
          <div className="rounded-3" style={{ height: '260px', marginBottom: '2.5rem' }}>
            <MapPreview />
          </div>
        )}

        {itinerary.length > 0 ? (
          isGeneratingPDF ? (
            itinerary.map((d, i) => (
              <div key={i} className="mb-3">
                <h6 className="fw-bold">{d.title}</h6>
                <p>{d.description}</p>
              </div>
            ))
          ) : (
            <Accordion defaultActiveKey="0">
              {itinerary.map((d, i) => (
                <Accordion.Item eventKey={i.toString()} key={i}>
                  <Accordion.Header>{d.title}</Accordion.Header>
                  <Accordion.Body>{d.description}</Accordion.Body>
                </Accordion.Item>
              ))}
            </Accordion>
          )
        ) : (
          <p className="text-muted">No itinerary available.</p>
        )}
      </Card.Body>
    </Card>
  );
}

export default TripItinerary;
