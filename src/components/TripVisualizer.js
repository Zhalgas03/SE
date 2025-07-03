import React, { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import TripHeader from './TripComponents/TripHeader';
import TripOverview from './TripComponents/TripOverview';
import TripHighlights from './TripComponents/TripHighlights';
import TripItinerary from './TripComponents/TripItinerary';
import TripTransfer from './TripComponents/TripTransfer';

function TripVisualizer() {
  const pdfRef = useRef();
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  const handleSaveToPDF = async () => {
    setIsGeneratingPDF(true);

    // 🔓 1. Принудительно раскрываем все Accordion'ы
    const collapses = document.querySelectorAll('.accordion-collapse');
    collapses.forEach(el => {
      el.classList.add('show');     // класс Bootstrap, делает body видимым
      el.style.height = 'auto';     // гарантирует высоту
    });

    await new Promise(resolve => setTimeout(resolve, 500)); // Ждём отрисовки

    const input = pdfRef.current;
    if (!input) {
      setIsGeneratingPDF(false);
      return;
    }

    const rect = input.getBoundingClientRect();
    if (rect.height === 0 || rect.width === 0) {
      alert('Error: Trip content is not fully rendered or visible.');
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
      pdf.save('trip-plan.pdf');
    } catch (error) {
      alert('Failed to generate PDF: ' + error.message);
      console.error(error);
    } finally {
      // 🔒 2. Возвращаем всё назад (чистим show и height)
      collapses.forEach(el => {
        el.classList.remove('show');
        el.style.height = '';
      });

      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="px-4 py-4" style={{ backgroundColor: '#f9f9f9' }}>
      <div className="text-end mb-3">
        <button className="btn btn-outline-secondary" onClick={handleSaveToPDF}>
          Save to PDF
        </button>
      </div>

      <div ref={pdfRef} id="trip-pdf-content">
        <TripHeader />
        <TripOverview />
        <TripHighlights />
        <TripItinerary isGeneratingPDF={isGeneratingPDF} />
        <TripTransfer />
      </div>
    </div>
  );
}

export default TripVisualizer;
