import React from 'react';

export default function TestTripPost() {
  const handleSubmit = async () => {
    const token = localStorage.getItem("token");

    const body = {
      name: "Trip to Rome",
      date_start: "2025-06-23",
      date_end: "2025-06-30"
    };

    try {
      const res = await fetch("http://localhost:5001/api/trips", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      const data = await res.json();
      console.log("📡 Response:", data);
      alert(data.success ? `Trip created: ${data.trip_id}` : `Error: ${data.message}`);
    } catch (err) {
      console.error("❌ Request failed:", err);
      alert("Request failed");
    }
  };

  return (
    <div className="p-4">
      <h2>🚀 Test Trip POST</h2>
      <button className="btn btn-primary" onClick={handleSubmit}>
        Send Test Trip
      </button>
    </div>
  );
}
