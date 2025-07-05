import React, { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import TripHeader from './TripComponents/TripHeader';
import TripOverview from './TripComponents/TripOverview';
import TripHighlights from './TripComponents/TripHighlights';
import TripItinerary from './TripComponents/TripItinerary';
import TripTransfer from './TripComponents/TripTransfer';
import { useTrip } from '../context/TripContext';

function TripVisualizer() {
  const { tripSummary } = useTrip();
  const pdfRef = useRef();
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [savedSuccessfully, setSavedSuccessfully] = useState(false);

  const today = new Date().toISOString().split('T')[0];
  const twoDaysLater = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0];

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

  const handleSaveToPDF = async () => {
    setIsGeneratingPDF(true);

    const collapses = document.querySelectorAll('.accordion-collapse');
    collapses.forEach(el => {
      el.classList.add('show');
      el.style.height = 'auto';
    });

    await new Promise(resolve => setTimeout(resolve, 500));

    const input = pdfRef.current;
    if (!input) {
      setIsGeneratingPDF(false);
      return;
    }

    try {
      const canvas = await html2canvas(input, {
        scale: 2,
        useCORS: true,
        windowWidth: document.body.scrollWidth,
        windowHeight: document.body.scrollHeight
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);

      // 📦 Отправляем PDF на сервер
      const pdfBase64 = pdf.output('datauristring');
      const token = localStorage.getItem("token");

      const res = await fetch("http://localhost:5001/api/trips/save-with-pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: generateTripName(tripSummary),
          date_start: today,
          date_end: twoDaysLater,
          pdf_base64: pdfBase64
        })
      });

      const data = await res.json();
      if (data.success) {
        setSavedSuccessfully(true);
        pdf.save("trip-plan.pdf");
        alert("✅ Trip saved and downloaded.");
      } else {
        alert("❌ Failed to save trip: " + data.message);
      }

    } catch (error) {
      alert("❌ Error: " + error.message);
      console.error(error);
    } finally {
      collapses.forEach(el => {
        el.classList.remove('show');
        el.style.height = '';
      });
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="trip-visualizer-container px-4 py-4 rounded-4">
      <div className="text-end mb-3">
        <button className="btn btn-outline-secondary" onClick={handleSaveToPDF}>
          {savedSuccessfully ? "✅ Trip saved" : "Save to PDF"}
        </button>
      </div>

      <div ref={pdfRef} id="trip-pdf-content">
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
