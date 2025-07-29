import React, { useEffect, useState } from 'react';
import { Card } from 'react-bootstrap';
import MapPreview from '../MapPreview';

const AVIATIONSTACK_API_KEY = "bb26fde6170780288bf61df797051dca";

function TripTransfer({ summary }) {
  const transfers = Array.isArray(summary?.transfers) && summary.transfers.length > 0
    ? summary.transfers
    : [];

  const [flightInfo, setFlightInfo] = useState(null);

  useEffect(() => {
    async function fetchFlightData() {
      try {
        const res = await fetch(
          `http://api.aviationstack.com/v1/flights?access_key=${AVIATIONSTACK_API_KEY}&dep_iata=MXP&arr_iata=ALA`
        );

        const data = await res.json();
        console.log("Flights API response:", data);

        if (data.data && data.data.length > 0) {
          const firstFlight = data.data[0];
          setFlightInfo({
            airline: firstFlight.airline?.name || "Unknown Airline",
            flightNumber: firstFlight.flight?.iata || "N/A",
            departure: firstFlight.departure?.scheduled || "Unknown",
            arrival: firstFlight.arrival?.scheduled || "Unknown",
            duration: firstFlight.arrival?.estimated
              ? "≈ " + Math.round((new Date(firstFlight.arrival.estimated) - new Date(firstFlight.departure.scheduled)) / 3600000) + "h"
              : "N/A"
          });
        } else {
          // --- Fallback: статический пример рейса ---
          setFlightInfo({
            airline: "Neos Air",
            flightNumber: "NO 432",
            departure: "Milan Malpensa (MXP)",
            arrival: "Almaty (ALA)",
            duration: "≈ 9h 20min"
          });
        }
      } catch (error) {
        console.error("Error fetching flights:", error);
        setFlightInfo({
          airline: "Neos Air",
          flightNumber: "NO 432",
          departure: "Milan Malpensa (MXP)",
          arrival: "Almaty (ALA)",
          duration: "≈ 9h 20min"
        });
      }
    }

    fetchFlightData();
  }, []);

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Transfer & Transportation</h5>

        {/* Вывод API или заглушки */}
        {flightInfo ? (
          <div className="mb-4">
            <div><strong>Airline:</strong> {flightInfo.airline}</div>
            <div><strong>Flight:</strong> {flightInfo.flightNumber}</div>
            <div><strong>Departure:</strong> {flightInfo.departure}</div>
            <div><strong>Arrival:</strong> {flightInfo.arrival}</div>
            <div><strong>Duration:</strong> {flightInfo.duration}</div>
          </div>
        ) : (
          <p className="text-muted">Loading transfer data...</p>
        )}

        {/* Основной трансфер из чата */}
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

        <MapPreview coordinates={summary.coordinates} />
      </Card.Body>
    </Card>
  );
}

export default TripTransfer;
