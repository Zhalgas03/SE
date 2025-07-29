// src/pages/GuestVotePage.jsx
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

function GuestVotePage() {
  const { tripId } = useParams();
  
  // Log the tripId to console for debugging
  console.log("🎯 GuestVotePage: tripId =", tripId);
  
  const [tripTitle, setTripTitle] = useState("");
  const [hasVoted, setHasVoted] = useState(false);
  const [voteStatus, setVoteStatus] = useState(null); // null | "success" | "error"
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        if (!document.cookie.includes("session_token")) {
          await fetch("/api/session/init", {
            credentials: "include",
          });
        }

        const res = await fetch(`/api/trips/${tripId}`);
        const data = await res.json();

        if (data.success && data.trip) {
          setTripTitle(data.trip.title || "Trip");
        } else {
          setTripTitle("Trip not found");
        }
      } catch (err) {
        console.error("Trip load error:", err);
        setTripTitle("Error loading trip");
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [tripId]);

  // 2. Отправка голоса
  const sendVote = async (value) => {
    if (hasVoted) return;

    try {
      const res = await fetch(`/api/votes/guest/${tripId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ value }),
      });

      const data = await res.json();

      if (data.success) {
        setVoteStatus("success");
        setHasVoted(true);
      } else {
        setVoteStatus("error");
        alert(data.message || "Vote not accepted.");
      }
    } catch (err) {
      console.error("Vote error:", err);
      setVoteStatus("error");
      alert("Something went wrong.");
    }
  };

  return (
    <div className="container text-center mt-5">
      <h2 className="mb-4">Vote for Trip</h2>
      {loading ? (
        <p>Loading trip...</p>
      ) : (
        <>
          <h4 className="mb-4">{tripTitle}</h4>
          {hasVoted ? (
            <div className="alert alert-success">✅ Thank you for your vote!</div>
          ) : (
            <div>
              <p className="mb-3">Do you like this trip?</p>
              <button
                onClick={() => sendVote(1)}
                className="btn btn-success mx-2"
              >
                👍 Yes
              </button>
              <button
                onClick={() => sendVote(-1)}
                className="btn btn-danger mx-2"
              >
                👎 No
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default GuestVotePage;
