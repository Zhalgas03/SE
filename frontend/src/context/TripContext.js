import React, { createContext, useContext, useState, useEffect } from 'react';

const TripContext = createContext();

export const TripProvider = ({ children }) => {
  const [tripSummary, setTripSummary] = useState(null);

  const updateTripSummary = (summary) => {
    if (JSON.stringify(summary) === JSON.stringify(tripSummary)) return;
    setTripSummary(summary);
  };

  useEffect(() => {
    console.log("Trip summary updated:", tripSummary);
  }, [tripSummary]);

  return (
    <TripContext.Provider value={{ tripSummary, updateTripSummary }}>
      {children}
    </TripContext.Provider>
  );

};




export const useTrip = () => useContext(TripContext);
