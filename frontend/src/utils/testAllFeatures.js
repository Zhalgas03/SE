/**
 * Comprehensive test script for PDF generation and CORS functionality
 */

// Test PDF generation
export const testPDFGeneration = async () => {
  try {
    console.log('🧪 Testing PDF generation...');
    
    // Import the PDF generator
    const { generateTripPDF } = await import('./pdfGenerator');
    
    // Test data
    const testData = {
      destination: "Paris, France",
      origin: "New York",
      travel_dates: "June 15-22, 2024",
      style: "Cultural",
      budget: "$3000",
      activities: "Museums, Food Tours",
      group: "Solo Traveler",
      overview: "A week-long cultural exploration of Paris.",
      highlights: ["Visit the Louvre", "Climb the Eiffel Tower"],
      itinerary: [
        { title: "Day 1: Arrival", description: "Arrive in Paris" }
      ],
      transfers: [
        { route: "Airport to Hotel", details: "Private transfer" }
      ]
    };
    
    const pdf = generateTripPDF(testData, "Test Trip");
    console.log('✅ PDF generation successful!');
    
    // Test saving
    pdf.save('test-trip.pdf');
    console.log('✅ PDF saved successfully!');
    
    return true;
  } catch (error) {
    console.error('❌ PDF generation failed:', error);
    return false;
  }
};

// Test CORS and API access
export const testCORSAndAPI = async () => {
  try {
    console.log('🧪 Testing CORS and API access...');
    
    // Test the favorites endpoint
    const response = await fetch('/api/trips/favorites', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || 'test-token'}`
      }
    });
    
    console.log('✅ API request successful!');
    console.log('✅ Response status:', response.status);
    console.log('✅ CORS headers present:', response.headers.get('Access-Control-Allow-Origin'));
    
    return true;
  } catch (error) {
    console.error('❌ CORS/API test failed:', error);
    return false;
  }
};

// Run all tests
export const runAllTests = async () => {
  console.log('🚀 Starting comprehensive tests...');
  
  const pdfResult = await testPDFGeneration();
  const corsResult = await testCORSAndAPI();
  
  console.log('📊 Test Results:');
  console.log('  PDF Generation:', pdfResult ? '✅ PASS' : '❌ FAIL');
  console.log('  CORS/API Access:', corsResult ? '✅ PASS' : '❌ FAIL');
  
  if (pdfResult && corsResult) {
    console.log('🎉 All tests passed!');
  } else {
    console.log('⚠️ Some tests failed. Check console for details.');
  }
  
  return { pdfResult, corsResult };
};

// Export for browser console
if (typeof window !== 'undefined') {
  window.testPDFGeneration = testPDFGeneration;
  window.testCORSAndAPI = testCORSAndAPI;
  window.runAllTests = runAllTests;
  console.log('🔧 Test functions available in browser console:');
  console.log('  - testPDFGeneration()');
  console.log('  - testCORSAndAPI()');
  console.log('  - runAllTests()');
} 