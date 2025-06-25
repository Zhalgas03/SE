import React from 'react';

export default function TestTripPost() {
  const handleSubmit = async () => {
    const token = localStorage.getItem("token");
    console.log("🪪 JWT token:", token);

    if (!token) {
      alert("❌ No token found in localStorage. Please log in first.");
      return;
    }

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
          "Authorization": `Bearer ${token}` // ❗ обязательно с заглавной буквы!
        },
        body: JSON.stringify(body)
      });

      const data = await res.json();
      console.log("📡 Server response:", data);

      if (res.ok && data.success) {
        alert(`✅ Trip created successfully! Trip ID: ${data.trip_id}`);
      } else {
        alert(`❌ Error: ${data.message || "Unknown error"}`);
      }
    } catch (err) {
      console.error("❌ Request failed:", err);
      alert("❌ Network error or backend is down");
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">🚀 Test Trip POST</h2>
      <button
        className="btn btn-primary px-4 py-2 rounded"
        onClick={handleSubmit}
      >
        Send Test Trip
      </button>
    </div>
  );
}
