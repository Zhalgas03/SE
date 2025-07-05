import { useEffect, useRef } from "react";
import * as pdfjsLib from "pdfjs-dist";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker.entry";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

function PdfViewer({ url }) {
  const canvasRef = useRef();

  useEffect(() => {
    const render = async () => {
      const loadingTask = pdfjsLib.getDocument(url);
      const pdf = await loadingTask.promise;
      const page = await pdf.getPage(1);

      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");

      // 🔍 Получаем ширину контейнера
      const containerWidth = canvas.parentElement.offsetWidth;

      // 🧠 Базовый viewport (масштаб = 1)
      const baseViewport = page.getViewport({ scale: 1 });

      // 📐 Новый масштаб, чтобы вписать PDF точно в ширину
      const scale = containerWidth / baseViewport.width;

      // ⚡️ Финальный viewport
      const viewport = page.getViewport({ scale });

      // ✅ High-DPI (Retina) поддержка
      const dpr = window.devicePixelRatio || 1;
      canvas.width = viewport.width * dpr;
      canvas.height = viewport.height * dpr;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      context.setTransform(dpr, 0, 0, dpr, 0, 0);

      await page.render({
        canvasContext: context,
        viewport,
      }).promise;
    };

    render();
  }, [url]);

  return (
    <div style={{ width: "100%", overflowX: "auto", textAlign: "center" }}>
      <canvas
        ref={canvasRef}
        style={{
          maxWidth: "100%",
          height: "auto",
          borderRadius: "12px",
          boxShadow: "0 0 10px rgba(0,0,0,0.1)",
        }}
      />
    </div>
  );
}

export default PdfViewer;
