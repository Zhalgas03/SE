// src/components/TripVisualizer.jsx
import React, { useRef, useState } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import TripHeader from "./TripComponents/TripHeader";
import TripOverview from "./TripComponents/TripOverview";
import TripHighlights from "./TripComponents/TripHighlights";
import TripItinerary from "./TripComponents/TripItinerary";
import TripTransfer from "./TripComponents/TripTransfer";
import { useTrip } from "../context/TripContext";

function TripVisualizer() {
  const { tripSummary } = useTrip();
  const pdfRef = useRef();
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [savedSuccessfully, setSavedSuccessfully] = useState(false);

  const today = new Date().toISOString().split("T")[0];
  const twoDaysLater = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split("T")[0];

  function generateTripName(summary) {
    if (!summary || !summary.destination || !summary.travel_dates) return "My Trip";
    const { destination, travel_dates, style } = summary;
    const d1 = new Date(travel_dates.start || today);
    const d2 = new Date(travel_dates.end || twoDaysLater);
    const diffDays = Math.ceil((d2 - d1) / (1000 * 60 * 60 * 24)) + 1;
    const daysText = `${diffDays}-Day`;
    const styleText = style ? `${style} Trip` : "Trip";
    return `${daysText} ${styleText} to ${destination}`;
  }

  const handleSaveToPDF = async () => {
    setIsGeneratingPDF(true);

    // раскрываем аккордеоны
    const collapses = document.querySelectorAll(".accordion-collapse");
    collapses.forEach((el) => {
      el.classList.add("show");
      el.style.height = "auto";
    });

    // светлая тема для снимка
    const body = document.body;
    const wasDark = body.classList.contains("dark-theme");
    if (wasDark) body.classList.remove("dark-theme");

    // фиксируем ширину контента ровно под A4 (≈ 794px @96dpi)
    const content = pdfRef.current;
    if (!content) {
      if (wasDark) body.classList.add("dark-theme");
      collapses.forEach((el) => {
        el.classList.remove("show");
        el.style.height = "";
      });
      setIsGeneratingPDF(false);
      return;
    }

    const prevStyle = {
      width: content.style.width,
      margin: content.style.margin,
      boxShadow: content.style.boxShadow,
      background: content.style.background,
      color: content.style.color,
      borderRadius: content.style.borderRadius,
      overflow: content.style.overflow,
      padding: content.style.padding,
    };

    // минимальная, “плоская” верстка без теней и лишних паддингов
    content.style.width = "794px";
    content.style.margin = "0 auto";
    content.style.boxShadow = "none";
    content.style.background = "#ffffff";
    content.style.color = "#000000";
    content.style.borderRadius = "0";
    content.style.overflow = "visible";
    // оставь свои внутренние паддинги компонентов — тут общий паддинг не нужен

    // подождать перерисовку
    await new Promise((r) => setTimeout(r, 200));

    try {
      // делаем большой canvas
      const canvas = await html2canvas(content, {
        scale: 2,
        backgroundColor: "#ffffff",
        useCORS: true,
        scrollX: 0,
        scrollY: -window.scrollY,
      });

      // создаем PDF и режем canvas на страницы
      const pdf = new jsPDF("p", "mm", "a4");
      const pageWidth = pdf.internal.pageSize.getWidth();   // 210
      const pageHeight = pdf.internal.pageSize.getHeight(); // 297

      // соответствующая высота в пикселях для одного PDF-листа
      const pxPerMm = canvas.width / pageWidth;
      const pageCanvasHeightPx = Math.floor(pageHeight * pxPerMm);

      const sliceCanvas = document.createElement("canvas");
      sliceCanvas.width = canvas.width;
      sliceCanvas.height = pageCanvasHeightPx;
      const sctx = sliceCanvas.getContext("2d");

      let renderedHeight = 0;
      let firstPage = true;

      while (renderedHeight < canvas.height) {
        const sliceHeight = Math.min(pageCanvasHeightPx, canvas.height - renderedHeight);

        // очистить и нарисовать срез
        sctx.clearRect(0, 0, sliceCanvas.width, sliceCanvas.height);
        sctx.fillStyle = "#ffffff";
        sctx.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height);
        sctx.drawImage(
          canvas,
          0,
          renderedHeight,
          canvas.width,
          sliceHeight,
          0,
          0,
          sliceCanvas.width,
          sliceHeight
        );

        const imgData = sliceCanvas.toDataURL("image/png");
        const imgHeightMm = (sliceHeight / pxPerMm); // сколько мм занимает этот срез по высоте

        if (!firstPage) pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, 0, pageWidth, imgHeightMm, undefined, "FAST");

        firstPage = false;
        renderedHeight += sliceHeight;
      }

      pdf.setProperties({ title: generateTripName(tripSummary) });

      // сохранить на сервер
      const pdfBase64 = pdf.output("datauristring");
      const token = localStorage.getItem("token");

      const res = await fetch("http://localhost:5001/api/trips/save-with-pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: generateTripName(tripSummary),
          date_start: today,
          date_end: twoDaysLater,
          pdf_base64: pdfBase64,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setSavedSuccessfully(true);
        setTimeout(() => setSavedSuccessfully(false), 3000);
      } else {
        console.error("❌ Failed to save trip:", data.message || "Unknown error");
      }
    } catch (err) {
      console.error("❌ Error saving trip:", err);
    } finally {
      // вернуть стили
      Object.assign(content.style, prevStyle);

      // вернуть аккордеоны/тему
      collapses.forEach((el) => {
        el.classList.remove("show");
        el.style.height = "";
      });
      if (wasDark) body.classList.add("dark-theme");

      setIsGeneratingPDF(false);
    }
  };

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

  return (
    <div className="trip-visualizer-container px-4 py-4 rounded-4">
      <div className="d-flex justify-content-end align-items-center gap-3 mb-3">
        <button
          className="btn btn-outline-secondary"
          onClick={handleSaveToPDF}
          disabled={isGeneratingPDF}
        >
          {isGeneratingPDF ? "Saving…" : savedSuccessfully ? "✅ Trip saved" : "Save trip"}
        </button>
      </div>

      {/* Контент для PDF: централизован и без теней (тени мешают html2canvas) */}
      <div
        ref={pdfRef}
        id="trip-pdf-content"
        style={{
          width: "860px",           // шире для UI (на экране)
          maxWidth: "100%",
          margin: "0 auto",
          background: "transparent",
        }}
      >
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
