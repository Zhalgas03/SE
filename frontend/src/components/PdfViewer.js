import { useEffect, useRef } from "react";
import { getDocument, GlobalWorkerOptions } from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker.entry";

GlobalWorkerOptions.workerSrc = workerSrc;

export default function PdfViewer({
  url,
  maxWidth = 860, // шире по умолчанию
}) {
  const containerRef = useRef(null);
  const pdfRef = useRef(null);
  const lastWidthRef = useRef(0);
  const resizeObsRef = useRef(null);
  const rafRef = useRef(null);

  const clear = (node) => { while (node.firstChild) node.removeChild(node.firstChild); };

  const renderAllPages = async () => {
    const container = containerRef.current;
    const pdf = pdfRef.current;
    if (!container || !pdf) return;

    clear(container);

    const innerWidth = Math.max(0, Math.floor(container.clientWidth));
    lastWidthRef.current = innerWidth;

    const dpr = window.devicePixelRatio || 1;

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const base = page.getViewport({ scale: 1 });

      // базовый масштаб = больше из 1.5 или подгонки по ширине
      const targetScale = Math.max(1.5, (innerWidth / base.width));
      const viewport = page.getViewport({ scale: targetScale });

      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      canvas.width = Math.ceil(viewport.width * dpr);
      canvas.height = Math.ceil(viewport.height * dpr);

      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      canvas.style.display = "block";
      canvas.style.margin = "0 auto";
      canvas.style.background = "#fff";

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      await page.render({ canvasContext: ctx, viewport }).promise;
      container.appendChild(canvas);
    }
  };

  const attachObserver = () => {
    if (!containerRef.current) return;

    const obs = new ResizeObserver((entries) => {
      const e = entries[0];
      if (!e) return;

      const w = Math.max(0, Math.floor(e.contentRect.width || 0));
      if (w === 0 || w === lastWidthRef.current) return;

      lastWidthRef.current = w;

      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(async () => {
        if (!containerRef.current || !pdfRef.current) return;
        try {
          obs.unobserve(containerRef.current);
          await renderAllPages();
        } finally {
          if (containerRef.current) obs.observe(containerRef.current);
        }
      });
    });

    obs.observe(containerRef.current);
    resizeObsRef.current = obs;
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const task = getDocument(url);
        const pdf = await task.promise;
        if (cancelled) return;
        pdfRef.current = pdf;

        await renderAllPages();
        attachObserver();
      } catch (err) {
        console.error("PDF rendering error:", err);
      }
    })();

    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (resizeObsRef.current) {
        try { resizeObsRef.current.disconnect(); } catch {}
        resizeObsRef.current = null;
      }
      pdfRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  return (
    <div
      ref={containerRef}
      style={{
        maxWidth: `${maxWidth}px`,
        width: "100%",
        margin: "0 auto",
        overflow: "visible",
        fontSize: 0,
      }}
    />
  );
}
