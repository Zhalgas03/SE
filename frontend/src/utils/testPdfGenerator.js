import { generateTripPDF } from './pdfGenerator';

// Test data
const testTripData = {
  destination: "Paris, France",
  origin: "New York",
  travel_dates: "June 15-22, 2024",
  style: "Cultural",
  budget: "$3000",
  activities: "Museums, Food Tours",
  group: "Solo Traveler",
  overview: "A week-long cultural exploration of Paris including visits to the Louvre, Eiffel Tower, and local food markets.",
  highlights: [
    "Visit the Louvre Museum",
    "Climb the Eiffel Tower",
    "Explore Montmartre",
    "Take a Seine River cruise"
  ],
  itinerary: [
    {
      title: "Day 1: Arrival",
      description: "Arrive in Paris, check into hotel, evening walk along the Seine"
    },
    {
      title: "Day 2: Museums",
      description: "Visit the Louvre and Musée d'Orsay"
    }
  ],
  transfers: [
    {
      route: "Airport to Hotel",
      details: "Private transfer from CDG Airport to hotel in city center"
    }
  ]
};

// Test function with enhanced diagnostics
export const testPDFGeneration = () => {
  try {
    console.log('🧪 Testing PDF generation...');
    console.log('🧪 Test data:', testTripData);
    
    const pdf = generateTripPDF(testTripData, "Test Trip to Paris");
    console.log('✅ PDF generation successful!');
    console.log('✅ PDF object:', pdf);
    console.log('✅ PDF pages:', pdf.getNumberOfPages());
    
    // Save the PDF
    pdf.save('test-trip.pdf');
    console.log('✅ PDF saved as test-trip.pdf');
    
    return true;
  } catch (error) {
    console.error('❌ PDF generation failed:', error);
    console.error('❌ Error details:', error.message);
    console.error('❌ Error stack:', error.stack);
    return false;
  }
};

// Export for use in browser console
if (typeof window !== 'undefined') {
  window.testPDFGeneration = testPDFGeneration;
  console.log('🔧 PDF Test: testPDFGeneration function available in browser console');
}

/**
 * Sample trip data for testing
 */
export const sampleTripData = {
  destination: "Paris, France",
  origin: "New York, USA",
  travel_dates: "2025-07-15 to 2025-07-22",
  style: "Cultural",
  budget: "$3000",
  activities: "Museums, Food Tours, Architecture",
  group: "Couple",
  overview: "A romantic 7-day cultural journey through the heart of Paris, exploring world-famous museums, indulging in French cuisine, and experiencing the city's iconic architecture.",
  highlights: [
    "Visit the Louvre Museum and see the Mona Lisa",
    "Take a Seine River cruise at sunset",
    "Explore the charming Montmartre neighborhood",
    "Enjoy authentic French pastries and coffee",
    "Visit the Eiffel Tower and Arc de Triomphe"
  ],
  itinerary: [
    {
      title: "Day 1: Arrival & Introduction",
      description: "Arrive in Paris, check into hotel, and take a leisurely walk along the Seine River. Visit Notre-Dame Cathedral and enjoy dinner at a traditional French bistro."
    },
    {
      title: "Day 2: Art & Culture",
      description: "Spend the morning at the Louvre Museum exploring masterpieces. Afternoon visit to Musée d'Orsay to see Impressionist works. Evening at a wine bar in the Marais district."
    },
    {
      title: "Day 3: Iconic Landmarks",
      description: "Morning visit to the Eiffel Tower for panoramic views. Walk along the Champs-Élysées to the Arc de Triomphe. Evening Seine River cruise with dinner."
    }
  ],
  transfers: [
    {
      route: "Airport to Hotel",
      details: "Private transfer from Charles de Gaulle Airport to hotel in central Paris (45 minutes)"
    },
    {
      route: "Return Trip",
      details: "High-speed TGV train from Paris to Lyon, then flight from Lyon to New York"
    }
  ]
}; 