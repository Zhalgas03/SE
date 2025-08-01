import { useState } from 'react';
import { useTrip } from '../context/TripContext';
import { generateTripPDF, savePDFToServer } from '../utils/pdfGenerator';
import TripHeader from './TripComponents/TripHeader';
import TripHighlights from './TripComponents/TripHighlights';
import TripItinerary from './TripComponents/TripItinerary';
import TripOverview from './TripComponents/TripOverview';
import TripTransfer from './TripComponents/TripTransfer';

function TripVisualizer() {
  const { tripSummary, clearSavedTrip } = useTrip();
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [savedSuccessfully, setSavedSuccessfully] = useState(false);

  const today = new Date().toISOString().split('T')[0];
  const twoDaysLater = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

  if (!tripSummary) {
    return (
      <div className="d-flex justify-content-center align-items-center h-100 text-muted p-4">
        <div className="text-center">
          <h5 className="fw-semibold mb-2">🧭 Trip Plan will appear here</h5>
          <p className="mb-0">Start planning your trip using the chat on the left!</p>
        </div>
      </div>
    );
  }

  function generateTripName(summary) {
    if (!summary || !summary.destination || !summary.travel_dates) return "My Trip";

    const { destination, travel_dates, style } = summary;

    const date1 = new Date(travel_dates.start || today);
    const date2 = new Date(travel_dates.end || twoDaysLater);
    const diffDays = Math.ceil((date2 - date1) / (1000 * 60 * 60 * 24)) + 1;

    const daysText = `${diffDays}-Day`;
    const styleText = style ? `${style} Trip` : "Trip";

    return `${daysText} ${styleText} to ${destination}`;
  }

  const handleAddToFavorites = async () => {
    if (!tripSummary) {
      alert("❌ No trip data available.");
      return;
    }

    setIsGeneratingPDF(true);

    try {
      console.log('🔧 TripVisualizer: Starting add to favorites process...');
      const tripName = generateTripName(tripSummary);
      console.log('🔧 TripVisualizer: Generated trip name:', tripName);
      
      const pdf = generateTripPDF(tripSummary, tripName);
      console.log('🔧 TripVisualizer: PDF generated successfully');
      
      const serverResponse = await savePDFToServer(pdf, tripSummary, tripName);
      console.log('🔧 TripVisualizer: Server response received:', serverResponse);

      if (serverResponse.success) {
        setSavedSuccessfully(true);
        alert("✅ Trip added to favorites successfully!");
      } else {
        const errorMsg = serverResponse.message || 'Unknown server error';
        console.error('❌ TripVisualizer: Server returned error:', errorMsg);
        alert("❌ Failed to save trip: " + errorMsg);
      }

    } catch (error) {
      console.error("❌ TripVisualizer: Add to favorites error:", {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      
      // Provide user-friendly error messages
      let userMessage = "❌ Error saving trip: ";
      if (error.message.includes("Authentication token not found")) {
        userMessage += "Please log in again to save your trip.";
      } else if (error.message.includes("Server returned HTML error page")) {
        userMessage += "Server connection issue. Please try again later.";
      } else if (error.message.includes("Failed to fetch")) {
        userMessage += "Network error. Please check your connection and try again.";
      } else {
        userMessage += error.message;
      }
      
      alert(userMessage);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const handleSaveToPDF = async () => {
    if (!tripSummary) {
      alert("❌ No trip data available to generate PDF.");
      return;
    }

    setIsGeneratingPDF(true);

    try {
      console.log('🔧 TripVisualizer: Starting PDF download process...');
      const tripName = generateTripName(tripSummary);
      console.log('🔧 TripVisualizer: Generated trip name:', tripName);
      
      const pdf = generateTripPDF(tripSummary, tripName);
      console.log('🔧 TripVisualizer: PDF generated successfully');
      
      const serverResponse = await savePDFToServer(pdf, tripSummary, tripName);
      console.log('🔧 TripVisualizer: Server response received:', serverResponse);
      
      if (serverResponse.success) {
        setSavedSuccessfully(true);
        pdf.save(`${tripName.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`);
        alert("✅ Trip saved and downloaded successfully!");
      } else {
        const errorMsg = serverResponse.message || 'Unknown server error';
        console.error('❌ TripVisualizer: Server returned error:', errorMsg);
        alert("❌ Failed to save trip: " + errorMsg);
      }

    } catch (error) {
      console.error("❌ TripVisualizer: PDF generation error:", {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      
      // Provide user-friendly error messages
      let userMessage = "❌ Error generating PDF: ";
      if (error.message.includes("Authentication token not found")) {
        userMessage += "Please log in again to download your trip.";
      } else if (error.message.includes("Server returned HTML error page")) {
        userMessage += "Server connection issue. Please try again later.";
      } else if (error.message.includes("Failed to fetch")) {
        userMessage += "Network error. Please check your connection and try again.";
      } else {
        userMessage += error.message;
      }
      
      alert(userMessage);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const handleClearTrip = () => {
    if (window.confirm("Are you sure you want to clear this trip? This action cannot be undone.")) {
      clearSavedTrip();
      setSavedSuccessfully(false);
    }
  };

  return (
    <div className="trip-visualizer-container px-4 py-4 rounded-4">
      <div className="text-end mb-3 d-flex gap-2 justify-content-end">
        <button className="btn btn-outline-primary" onClick={handleAddToFavorites}>
          {savedSuccessfully ? "✅ Added to Favourites" : "Add to Favourites"}
        </button>
        <button className="btn btn-outline-secondary" onClick={handleSaveToPDF}>
          Download PDF
        </button>
        <button className="btn btn-outline-danger" onClick={handleClearTrip}>
          Clear Trip
        </button>
      </div>

      <div id="trip-pdf-content">
        <TripHeader summary={tripSummary} />
        <TripOverview summary={tripSummary} />
        <TripHighlights summary={tripSummary} />
        <TripItinerary summary={tripSummary} isGeneratingPDF={isGeneratingPDF} />
        <TripTransfer summary={tripSummary} />
      </div>
    </div>
  );
}

export default TripVisualizer;
