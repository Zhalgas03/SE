import React, { createContext, useContext, useState, useEffect } from 'react';

const TripContext = createContext();

export const TripProvider = ({ children }) => {
  const [tripSummary, setTripSummary] = useState(null);

  // Load trip data from localStorage on component mount
  useEffect(() => {
    try {
      const savedTrip = localStorage.getItem('lastGeneratedTrip');
      if (savedTrip) {
        const parsedTrip = JSON.parse(savedTrip);
        setTripSummary(parsedTrip);
        console.log("Trip data restored from localStorage:", parsedTrip);
      }
    } catch (error) {
      console.error("Error loading trip from localStorage:", error);
    }
  }, []);

  const updateTripSummary = (summary) => {
    if (JSON.stringify(summary) === JSON.stringify(tripSummary)) return;
    setTripSummary(summary);
  };

  // Save trip data to localStorage whenever it changes
  useEffect(() => {
    if (tripSummary) {
      try {
        localStorage.setItem('lastGeneratedTrip', JSON.stringify(tripSummary));
        console.log("Trip data saved to localStorage:", tripSummary);
      } catch (error) {
        console.error("Error saving trip to localStorage:", error);
      }
    }
  }, [tripSummary]);

  const clearSavedTrip = () => {
    try {
      localStorage.removeItem('lastGeneratedTrip');
      setTripSummary(null);
      console.log("Saved trip cleared from localStorage");
    } catch (error) {
      console.error("Error clearing trip from localStorage:", error);
    }
  };

  return (
    <TripContext.Provider value={{ tripSummary, updateTripSummary, clearSavedTrip }}>
      {children}
    </TripContext.Provider>
  );
};

export const useTrip = () => useContext(TripContext);
