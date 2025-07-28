import jsPDF from 'jspdf';
import 'jspdf-autotable';

console.log('🔧 PDF Generator: jsPDF imported successfully');
console.log('🔧 PDF Generator: jspdf-autotable imported successfully');

/**
 * Generates a PDF from trip data using jsPDF and jsPDF-autotable
 * @param {Object} tripData - The trip summary data
 * @param {string} tripName - Name of the trip
 * @returns {jsPDF} The generated PDF document
 */
export const generateTripPDF = (tripData, tripName = "Trip Plan") => {
  try {
    console.log('🔧 PDF Generator: Starting PDF generation...');
    
    // Initialize PDF with A4 format
    const pdf = new jsPDF('p', 'mm', 'a4');
    console.log('🔧 PDF Generator: jsPDF instance created successfully');
    
    // Check if autoTable function is available on the instance
    if (typeof pdf.autoTable !== 'function') {
      console.error('❌ PDF Generator: autoTable not available on pdf instance');
      console.error('❌ PDF Generator: Available methods on pdf:', Object.getOwnPropertyNames(pdf));
      console.error('❌ PDF Generator: jsPDF prototype methods:', Object.getOwnPropertyNames(jsPDF.prototype));
      throw new Error('autoTable function is not available on PDF instance. Please check jspdf-autotable installation.');
    }
    
    console.log('🔧 PDF Generator: autoTable function is available on PDF instance');
    
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 20;
    const contentWidth = pageWidth - (2 * margin);
    
    let yPosition = margin;
    const lineHeight = 7;
    const sectionSpacing = 15;

    // Helper function to add text with word wrapping
    const addWrappedText = (text, x, y, maxWidth) => {
      const lines = pdf.splitTextToSize(text, maxWidth);
      pdf.text(lines, x, y);
      return lines.length * lineHeight;
    };

    // Helper function to check if we need a new page
    const checkPageBreak = (requiredHeight) => {
      if (yPosition + requiredHeight > pageHeight - margin) {
        pdf.addPage();
        yPosition = margin;
        return true;
      }
      return false;
    };

    // Title
    pdf.setFontSize(24);
    pdf.setFont('helvetica', 'bold');
    pdf.text(tripName, margin, yPosition);
    yPosition += 15;

    // Trip Details Section
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.text('Trip Details', margin, yPosition);
    yPosition += 10;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');

    // Create trip details table
    const tripDetails = [];
    if (tripData.destination) tripDetails.push(['Destination', tripData.destination]);
    if (tripData.origin) tripDetails.push(['Departure City', tripData.origin]);
    if (tripData.travel_dates) tripDetails.push(['Dates', tripData.travel_dates]);
    if (tripData.style) tripDetails.push(['Travel Style', tripData.style]);
    if (tripData.budget) tripDetails.push(['Budget', tripData.budget]);
    if (tripData.activities) tripDetails.push(['Activities', tripData.activities]);
    if (tripData.group) tripDetails.push(['Travel Group', tripData.group]);

    if (tripDetails.length > 0) {
      try {
        console.log('🔧 PDF Generator: Creating trip details table using pdf.autoTable...');
        pdf.autoTable({
          startY: yPosition,
          head: [['Field', 'Value']],
          body: tripDetails,
          theme: 'grid',
          headStyles: { fillColor: [66, 139, 202], textColor: 255 },
          styles: { fontSize: 9 },
          margin: { left: margin, right: margin },
          tableWidth: contentWidth,
        });
        yPosition = pdf.lastAutoTable.finalY + sectionSpacing;
        console.log('🔧 PDF Generator: Trip details table created successfully');
      } catch (tableError) {
        console.error('❌ PDF Generator: Error creating table:', tableError);
        // Fallback to text
        tripDetails.forEach(([field, value]) => {
          pdf.text(`${field}: ${value}`, margin, yPosition);
          yPosition += 8;
        });
        yPosition += sectionSpacing;
      }
    }

    // Overview Section
    if (tripData.overview) {
      checkPageBreak(20);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Overview', margin, yPosition);
      yPosition += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      const overviewHeight = addWrappedText(tripData.overview, margin, yPosition, contentWidth);
      yPosition += overviewHeight + sectionSpacing;
    }

    // Highlights Section
    if (tripData.highlights && tripData.highlights.length > 0) {
      checkPageBreak(30);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Highlights', margin, yPosition);
      yPosition += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      
      tripData.highlights.forEach((highlight, index) => {
        checkPageBreak(10);
        pdf.text(`• ${highlight}`, margin + 5, yPosition);
        yPosition += 8;
      });
      yPosition += sectionSpacing;
    }

    // Itinerary Section
    if (tripData.itinerary && tripData.itinerary.length > 0) {
      checkPageBreak(30);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Itinerary', margin, yPosition);
      yPosition += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');

      tripData.itinerary.forEach((day, index) => {
        checkPageBreak(25);
        
        // Day title
        pdf.setFont('helvetica', 'bold');
        pdf.text(day.title || `Day ${index + 1}`, margin, yPosition);
        yPosition += 8;
        
        // Day description
        pdf.setFont('helvetica', 'normal');
        const descriptionHeight = addWrappedText(day.description, margin + 5, yPosition, contentWidth - 5);
        yPosition += descriptionHeight + 8;
      });
      yPosition += sectionSpacing;
    }

    // Transfers Section
    if (tripData.transfers && tripData.transfers.length > 0) {
      checkPageBreak(30);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Transportation & Transfers', margin, yPosition);
      yPosition += 10;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      
      tripData.transfers.forEach((transfer, index) => {
        checkPageBreak(20);
        pdf.setFont('helvetica', 'bold');
        pdf.text(transfer.route, margin, yPosition);
        yPosition += 8;
        
        pdf.setFont('helvetica', 'normal');
        const detailsHeight = addWrappedText(transfer.details, margin + 5, yPosition, contentWidth - 5);
        yPosition += detailsHeight + 8;
      });
    }

    // Footer
    const totalPages = pdf.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Page ${i} of ${totalPages}`, pageWidth - margin - 30, pageHeight - 10);
      pdf.text(`Generated on ${new Date().toLocaleDateString()}`, margin, pageHeight - 10);
    }

    console.log('🔧 PDF Generator: PDF generation completed successfully');
    return pdf;
  } catch (error) {
    console.error('❌ PDF Generator: Error during PDF generation:', error);
    throw new Error(`PDF generation failed: ${error.message}`);
  }
};

/**
 * Saves the PDF to the server and downloads it locally
 * @param {jsPDF} pdf - The PDF document
 * @param {Object} tripData - Trip data for server storage
 * @param {string} tripName - Name of the trip
 * @returns {Promise<Object>} Server response
 */
export const savePDFToServer = async (pdf, tripData, tripName) => {
  try {
    // Convert PDF to base64
    const pdfBase64 = pdf.output('datauristring');
    const token = localStorage.getItem("token");

    if (!token) {
      throw new Error("Authentication token not found");
    }

    const response = await fetch("/api/trips/save-with-pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        name: tripName,
        date_start: new Date().toISOString().split('T')[0],
        date_end: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        pdf_base64: pdfBase64
      })
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error saving PDF to server:", error);
    throw error;
  }
}; 