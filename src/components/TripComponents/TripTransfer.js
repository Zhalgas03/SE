import React, { useEffect, useState } from 'react';
import { Card } from 'react-bootstrap';
import MapPreview from '../MapPreview';

const AVIATIONSTACK_API_KEY = "bb26fde6170780288bf61df797051dca";

const IATA_CODES = {
  Rome: "FCO",
  Milan: "MXP",
  Berlin: "BER",
  Almaty: "ALA",
  Astana: "NQZ",
  Paris: "CDG",
  London: "LHR",
  Barcelona: "BCN",
  Madrid: "MAD"
};

const calculateDuration = (startIso, endIso) => {
  if (!startIso || !endIso) return "N/A";
  const diffMs = new Date(endIso) - new Date(startIso);
  if (diffMs <= 0) return "N/A";
  const hours = Math.floor(diffMs / 3600000);
  const minutes = Math.round((diffMs % 3600000) / 60000);
  return `≈ ${hours}h ${minutes}min`;
};

// Парсим диапазон дат
function parseTripDates(datesString) {
  if (!datesString) return [null, null];
  const parts = datesString.split(/to|-|–/).map(p => p.trim());
  const start = new Date(parts[0].replace(/\./g, '/'));
  const end = parts[1] ? new Date(parts[1].replace(/\./g, '/')) : null;
  return [isNaN(start) ? null : start, isNaN(end) ? null : end];
}

function TripTransfer({ summary }) {
  const transfers = Array.isArray(summary?.transfers) && summary.transfers.length > 0
    ? summary.transfers
    : [];

  const [outboundFlight, setOutboundFlight] = useState(null);
  const [returnFlight, setReturnFlight] = useState(null);

  const getIataCode = (city) => {
    if (!city) return null;
    const cleanCity = city.split(/[ ,]+/)[0];
    return IATA_CODES[cleanCity] || cleanCity.slice(0, 3).toUpperCase();
  };

  useEffect(() => {
    async function fetchFlightData() {
      if (!summary?.origin || !summary?.destination) {
        console.warn("Нет origin/destination");
        return;
      }

      const depIata = getIataCode(summary.origin);
      const arrIata = getIataCode(summary.destination);

      const [tripStart, tripEnd] = parseTripDates(summary.travel_dates);

      // Рейс туда
      await fetchAndSetFlight(depIata, arrIata, tripStart, setOutboundFlight);

      // Рейс обратно
      if (tripEnd) {
        await fetchAndSetFlight(arrIata, depIata, tripEnd, setReturnFlight);
      } else {
        setReturnFlight({
          airline: "No flights found (approx.)",
          flightNumber: "N/A",
          departure: arrIata,
          arrival: depIata,
          duration: "≈ 1h 40min (approx.)"
        });
      }
    }

    async function fetchAndSetFlight(fromIata, toIata, targetDate, setter) {
      try {
        const res = await fetch(
          `http://api.aviationstack.com/v1/flights?access_key=${AVIATIONSTACK_API_KEY}&dep_iata=${fromIata}&arr_iata=${toIata}`
        );
    
        const data = await res.json();
    
        let airline = "Unknown Airline";
        let flightNumber = "N/A";
        let duration = "≈ 1h 40min (approx.)";
    
        if (data.data && data.data.length > 0) {
          const flight = data.data[0];
          airline = flight.airline?.name || airline;
          flightNumber = flight.flight?.iata || flightNumber;
    
          const depTime = flight.departure?.scheduled;
          const arrTime = flight.arrival?.scheduled;
          const dur = calculateDuration(depTime, arrTime);
          if (dur !== "N/A") duration = dur;
        }
    
        // **ДАТА ВСЕГДА ИЗ TRAVEL_DATES**
        setter({
          airline,
          flightNumber,
          departure: targetDate
            ? targetDate.toLocaleDateString("en-GB", { day: "2-digit", month: "short" })
            : fromIata,
          arrival: targetDate
            ? targetDate.toLocaleDateString("en-GB", { day: "2-digit", month: "short" })
            : toIata,
          duration
        });
      } catch (error) {
        console.error("Error fetching flights:", error);
        setter({
          airline: "API Error",
          flightNumber: "N/A",
          departure: targetDate?.toLocaleDateString("en-GB") || fromIata,
          arrival: targetDate?.toLocaleDateString("en-GB") || toIata,
          duration: "≈ 1h 40min (approx.)"
        });
      }
    }

    fetchFlightData();
  }, [summary?.origin, summary?.destination, summary?.travel_dates]);

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-3">Transfer & Transportation</h5>
        {summary.travel_dates && (
          <div className="text-muted mb-2">Travel Dates: {summary.travel_dates}</div>
        )}

        {/* Рейс туда */}
        {outboundFlight ? (
          <div className="mb-3">
            <div><strong>Airline:</strong> {outboundFlight.airline}</div>
            <div><strong>Flight:</strong> {outboundFlight.flightNumber}</div>
            <div><strong>Departure:</strong> {outboundFlight.departure}</div>
            <div><strong>Arrival:</strong> {outboundFlight.arrival}</div>
            <div><strong>Duration:</strong> {outboundFlight.duration}</div>
          </div>
        ) : (
          <p className="text-muted">Loading outbound flight...</p>
        )}

        {/* Рейс обратно */}
        {returnFlight ? (
          <div className="mb-3">
            <div className="fw-semibold">Return Trip</div>
            <div><strong>Airline:</strong> {returnFlight.airline}</div>
            <div><strong>Flight:</strong> {returnFlight.flightNumber}</div>
            <div><strong>Departure:</strong> {returnFlight.departure}</div>
            <div><strong>Arrival:</strong> {returnFlight.arrival}</div>
            <div><strong>Duration:</strong> {returnFlight.duration}</div>
          </div>
        ) : (
          <p className="text-muted">Loading return flight...</p>
        )}

        {/* Дополнительный текст из чата */}
        {transfers.length > 0 && transfers.map((tr, i) => (
          <div key={i} className="mb-4">
            <div className="fw-semibold">{tr.route}</div>
            <div className="text-muted small ms-4">{tr.details}</div>
          </div>
        ))}

        <MapPreview coordinates={summary.coordinates} />
      </Card.Body>
    </Card>
  );
}

export default TripTransfer;