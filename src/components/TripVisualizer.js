import React from 'react';
import TripHeader from './TripComponents/TripHeader';
import TripOverview from './TripComponents/TripOverview';
import TripHighlights from './TripComponents/TripHighlights';
import TripItinerary from './TripComponents/TripItinerary';
import TripTransfer from './TripComponents/TripTransfer';

function TripVisualizer() {
  return (
    <div className="px-4 py-4" style={{ backgroundColor: '#f9f9f9' }}>
      <TripHeader />
      <TripOverview />
      <TripHighlights />
      <TripItinerary />
      <TripTransfer />
    </div>
  );
}

export default TripVisualizer;
