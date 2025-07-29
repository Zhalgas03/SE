import jsPDF from 'jspdf';
import 'jspdf-autotable';

/**
 * Simple test to verify PDF generation works
 */
export const testSimplePDF = () => {
  try {
    console.log('🧪 Testing simple PDF generation...');
    
    // Create PDF
    const pdf = new jsPDF();
    
    // Check if autoTable is available
    if (typeof pdf.autoTable !== 'function') {
      console.error('❌ autoTable not available on pdf instance');
      return false;
    }
    
    // Add some text
    pdf.text('Hello World!', 20, 20);
    
    // Try to create a simple table
    pdf.autoTable({
      head: [['Name', 'Age']],
      body: [['John', '25'], ['Jane', '30']],
      startY: 40
    });
    
    // Save the PDF
    pdf.save('test-simple.pdf');
    
    console.log('✅ Simple PDF generation successful!');
    return true;
  } catch (error) {
    console.error('❌ Simple PDF generation failed:', error);
    return false;
  }
};

// Export for browser console
if (typeof window !== 'undefined') {
  window.testSimplePDF = testSimplePDF;
  console.log('🔧 Simple PDF test available: testSimplePDF()');
} 