import { useEffect, useRef } from "react";
import { getDocument, GlobalWorkerOptions } from "pdfjs-dist";
import workerSrc from 'pdfjs-dist/build/pdf.worker.entry';

// Устанавливаем путь к воркеру
GlobalWorkerOptions.workerSrc = workerSrc;

function PdfViewer({ url }) {
  const containerRef = useRef();

  useEffect(() => {
    const renderAllPages = async () => {
      try {
        const loadingTask = getDocument(url);
        const pdf = await loadingTask.promise;

        const container = containerRef.current;
        if (!container) return;

        container.innerHTML = "";
        const dpr = window.devicePixelRatio || 1;

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
          const page = await pdf.getPage(pageNum);
          const baseViewport = page.getViewport({ scale: 1 });

          const containerWidth = container.offsetWidth;
          const scale = containerWidth / baseViewport.width;
          const viewport = page.getViewport({ scale });

          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");

          canvas.width = viewport.width * dpr;
          canvas.height = viewport.height * dpr;
          canvas.style.width = `${viewport.width}px`;
          canvas.style.height = `${viewport.height}px`;
          canvas.style.borderRadius = "12px";
          canvas.style.boxShadow = "0 0 10px rgba(0,0,0,0.1)";
          canvas.style.marginBottom = "1rem";

          context.setTransform(dpr, 0, 0, dpr, 0, 0);
          await page.render({ canvasContext: context, viewport }).promise;

          container.appendChild(canvas);
        }
      } catch (err) {
        console.error("PDF rendering error:", err);
      }
    };

    renderAllPages();
  }, [url]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        overflowX: "auto",
        textAlign: "center",
        padding: "1rem 0",
      }}
    />
  );
}

export default PdfViewer;
