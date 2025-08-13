import React from "react";

function VoteRight() {
  return (
    <div style={{
      height: "100%",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      textAlign: "center",
    }}>
      <h2 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "16px" }}>
        📄 PDF Preview
      </h2>
      <p style={{ color: "#777", fontStyle: "italic" }}>
        No preview available yet.
      </p>
    </div>
  );
}

export default VoteRight;
