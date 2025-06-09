import React from 'react';
import { Card, Accordion } from 'react-bootstrap';
import MapPreview from '../MapPreview';

function TripItinerary() {
  const days = [
    { header: "Day 1: Arrival in Rome", content: "Arrival, hotel check-in, and evening walk in the historic center." },
    { header: "Day 2: Ancient Rome & Colosseum", content: "Explore the Colosseum, Roman Forum, and enjoy a traditional Roman dinner." },
    { header: "Day 3: Vatican & Culinary Experience", content: "Morning visit to the Vatican Museums and St. Peter’s Basilica, followed by a pasta class." },
    { header: "Day 4: Departure", content: "Breakfast and check-out. Optional morning walk or souvenir shopping." }
  ];

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Itinerary</h5>
        <p>
          Rome is a city of deep history and culture, where you can visit iconic landmarks like the
          Colosseum, Roman Forum, and Pantheon. In 3 days, you'll soak up the Eternal City's
          atmosphere, stroll scenic alleys, and enjoy gelato near Trevi Fountain.
        </p>

        <div className="rounded-3 overflow-hidden mb-4" style={{ height: '260px' }}>
          <MapPreview />
        </div>

        <Accordion defaultActiveKey="0">
          {days.map((d, i) => (
            <Accordion.Item eventKey={i.toString()} key={i}>
              <Accordion.Header>{d.header}</Accordion.Header>
              <Accordion.Body>{d.content}</Accordion.Body>
            </Accordion.Item>
          ))}
        </Accordion>
      </Card.Body>
    </Card>
  );
}

export default TripItinerary;
