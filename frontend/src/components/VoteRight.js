// src/components/VoteRight.jsx
import React from "react";
import PdfViewer from "./PdfViewer";
import "../styles/VoteRight.css";  // <— добавили

export default function VoteRight({ pdfUrl }) {
  return (
    <div className="vote-right-pane">
      {pdfUrl ? (
        <div className="pdf-scroll">
          <PdfViewer url={pdfUrl} />
        </div>
      ) : (
        <div className="text-muted">No PDF attached for this voting session.</div>
      )}
    </div>
  );
}
