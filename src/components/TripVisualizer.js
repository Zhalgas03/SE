import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import TripHeader from './TripComponents/TripHeader';
import TripOverview from './TripComponents/TripOverview';
import TripHighlights from './TripComponents/TripHighlights';
import TripItinerary from './TripComponents/TripItinerary';
import TripTransfer from './TripComponents/TripTransfer';


function TripVisualizer() {
  const { tripId } = useParams();
  const [trip, setTrip] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!tripId || !token) return;

    fetch(`http://localhost:5001/api/trip/${tripId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setTrip(data.trip);
        }
      });
  }, [tripId]);

  if (!trip) return <div className="p-4">Loading trip...</div>;

  return (
    <div className="px-4 py-4" style={{ backgroundColor: '#f9f9f9' }}>
      <TripHeader name={trip.name} date_start={trip.date_start} date_end={trip.date_end} />

<div className="bg-white border rounded-lg shadow p-4 mb-4">
  <h3 className="text-xl font-bold mb-2">Trip Summary from DB</h3>
  <ul className="list-disc list-inside text-sm">
    <li><strong>Name:</strong> {trip.name}</li>
    <li><strong>Start:</strong> {trip.date_start}</li>
    <li><strong>End:</strong> {trip.date_end}</li>
    <li><strong>ID:</strong> {trip.id}</li>
  </ul>
</div>

      <TripOverview trip={trip} />
      <TripHighlights trip={trip} />
      <TripItinerary trip={trip} />
      <TripTransfer trip={trip} />
    </div>
  );
}

export default TripVisualizer;
