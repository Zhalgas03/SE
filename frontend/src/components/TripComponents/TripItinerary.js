import React, { useState } from 'react';
import { Card, Accordion } from 'react-bootstrap';
import MapPreview from '../MapPreview';

const timeStyles = {
  base: {
    fontWeight: 600,
    borderRadius: '0.5rem',
    fontSize: '0.875rem',
    padding: '0.35em 0.75em',
    display: 'inline-block',
    minWidth: '100px',
    textAlign: 'center',
    backgroundColor: '#f0f0f0',
    color: '#000',
  },
  Morning: { backgroundColor: '#FFE08A' },
  Midday: { backgroundColor: '#A5C9FF', color: '#002b66' },
  Afternoon: { backgroundColor: '#FFD6A5' },
  Evening: { backgroundColor: '#D1C3FF', color: '#2e0066' },
  'Full day': { backgroundColor: '#DDD' },
  'All Day': { backgroundColor: '#DDD' },
};

function TimeBadge({ time }) {
  const style = { ...timeStyles.base, ...timeStyles[time] };
  return <span className="time-badge" style={style}>{time}</span>;
}

function TripItinerary({ summary, isGeneratingPDF }) {
  const [activeKey, setActiveKey] = useState('0');

  const itinerary = Array.isArray(summary?.itinerary) ? summary.itinerary : [];
  const intro = summary?.itinerary_intro || '';
  const coordinates = summary?.coordinates || [];

  const handleToggle = (key) => {
    setActiveKey(activeKey === key ? null : key);
  };

  return (
    <Card className="mb-4 shadow-sm trip-card it-card" style={{ overflow: 'visible' }}>
      <Card.Body>
        <h5 className="fw-bold mb-3">Itinerary</h5>

        {intro && <p className="it-intro">{intro}</p>}

        {!isGeneratingPDF && coordinates.length > 0 && (
          <div className="rounded-3 it-map" style={{ height: '260px' }}>
            <MapPreview coordinates={coordinates} />
          </div>
        )}

        {itinerary.length > 0 ? (
          <div className="it-acc">
          <Accordion activeKey={activeKey}>
            {itinerary.map((day, i) => (
              <Accordion.Item
                eventKey={i.toString()}
                key={i}
                onClick={() => handleToggle(i.toString())}
              >
                <Accordion.Header>{day.title}</Accordion.Header>
                <Accordion.Body>
                  {Array.isArray(day.parts) && day.parts.length > 0 ? (
                    day.parts.map((part, idx) => (
                      <div key={idx} className="d-flex mb-3 it-part">
                        <div className="it-left" style={{ marginRight: '25px' }}>
                          <TimeBadge time={part.time} />
                        </div>
                        <div style={{ flex: 1 }}>{part.text}</div>
                      </div>
                    ))
                  ) : (
                    <p>{day.description || 'No details available for this day.'}</p>
                  )}
                </Accordion.Body>
              </Accordion.Item>
            ))}
          </Accordion>
          </div>
        ) : (
          <p className="text-muted">No itinerary available.</p>
        )}
      </Card.Body>
    </Card>
  );
}

export default TripItinerary;
