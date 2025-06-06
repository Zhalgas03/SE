import React from 'react';

const sampleData = [
  {
    day: 1,
    title: "Arrival in Almaty",
    activity: "Explore Almaty, enjoy local food",
    hotel: "Almaty Comfort Hostel",
    weather: "☀️ Sunny, 22°C"
  },
  {
    day: 2,
    title: "Local Market & Museums",
    activity: "Visit Green Market and museums",
    hotel: "Hotel Kazakhstan",
    weather: "⛅ Partly cloudy, 20°C"
  },
  {
    day: 3,
    title: "Mountain Adventure",
    activity: "Hiking in the Tian Shan mountains",
    hotel: "Mountain Eco Lodge",
    weather: "🌄 Clear, 18°C"
  }
];

function TripVisualizer() {
  return (
    <div className="p-4">
      <h2 className="fs-4 fw-bold mb-4">Your Itinerary</h2>
      <div className="d-flex flex-column gap-3">
        {sampleData.map((item) => (
          <div key={item.day} className="border rounded-4 shadow-sm p-3 bg-white">
            <h5 className="fw-semibold mb-2">📅 Day {item.day}: {item.title}</h5>
            <p className="mb-1">📍 <strong>Activity:</strong> {item.activity}</p>
            <p className="mb-1">🛏 <strong>Hotel:</strong> {item.hotel}</p>
            <p className="mb-0">🌤 <strong>Weather:</strong> {item.weather}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TripVisualizer;
