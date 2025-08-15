import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import VoteLeft from "../components/VoteLeft";
import VoteRight from "../components/VoteRight";
import "./VotePage.css";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5001";

function VotePage() {
  const { share_link } = useParams();

  // data state
  const [session, setSession] = useState(null);
  const [voteValue, setVoteValue] = useState(null);
  const [comment, setComment] = useState("");
  const [voted, setVoted] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [confirmVote, setConfirmVote] = useState(false);
  const [yourVoteValue, setYourVoteValue] = useState(null);
  const [pdfUrl, setPdfUrl] = useState("");

  // responsive (как в PlannerPage)
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" ? window.innerWidth < 768 : false
  );
  const [activeTab, setActiveTab] = useState("voting"); // 'voting' | 'details'

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // -------- helpers --------
  const fetchTripById = async (tripId) => {
    try {
      const res = await axios.get(`${API_BASE}/api/trips/${tripId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        withCredentials: true,
      });
      const t = res.data?.trip;
      if (t?.pdf_file_path) return `${API_BASE}/${t.pdf_file_path}`;
    } catch (_) {}
    return "";
  };

  const derivePdfUrl = async (s) => {
    const path = s?.trip?.pdf_file_path || s?.pdf_file_path || s?.trip?.pdf_path;
    const url = s?.trip?.pdf_url || s?.pdf_url;
    if (url) return url;
    if (path) return `${API_BASE}/${path}`;
    const tripId = s?.trip_id || s?.trip?.id || s?.vote?.trip_id;
    if (tripId) return await fetchTripById(tripId);
    return "";
  };

  const fetchSession = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/votes/results/${share_link}`, {
        withCredentials: true,
      });
      const s = res.data;
      setSession(s);
      setYourVoteValue(s.your_vote_value);
      setVoted(s.you_voted);
      setPdfUrl(await derivePdfUrl(s));
    } catch (err) {
      console.error(err);
      setError("Error loading voting session.");
    }
  };

  useEffect(() => {
    fetchSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [share_link]);

  const submitVote = async () => {
    try {
      await axios.post(`${API_BASE}/api/votes/submit`, {
        share_link,
        value: voteValue,
        comment: comment || undefined,
      });
      setMessage("✅ Vote counted!");
      setError("");
      setVoteValue(null);
      setComment("");
      setConfirmVote(false);
      await fetchSession();
    } catch (err) {
      console.error("Vote error:", err);
      const msg = err.response?.data?.message || "Something went wrong";
      setError(msg);
      setConfirmVote(false);
      if (msg === "You already voted") {
        alert("⚠️ You already voted. You cannot vote again.");
        await fetchSession();
      }
    }
  };

  if (!session) {
    return (
      <div className="vote-loading container-fluid d-flex align-items-center justify-content-center">
        Loading...
      </div>
    );
  }

  // ---------- Mobile (как в PlannerPage) ----------
  if (isMobile) {
    return (
      <div className="container-fluid px-3 py-3 vote-mobile-page">
        <div className="btn-group w-100 mb-3" role="group" aria-label="Voting tabs">
          <button
            className={`btn btn-outline-primary ${activeTab === "voting" ? "active" : ""}`}
            onClick={() => setActiveTab("voting")}
          >
            Voting
          </button>
          <button
            className={`btn btn-outline-primary ${activeTab === "details" ? "active" : ""}`}
            onClick={() => setActiveTab("details")}
          >
            Details
          </button>
        </div>

        <div
          className="vote-mobile-box border rounded-4 p-2 shadow-sm"
          style={{
            height: "82vh",                 // ровно как в PlannerPage
            overflowY: "auto",
            backgroundColor: "var(--bg-color)",
            color: "var(--text-color)",
          }}
        >
          {activeTab === "voting" ? (
            <VoteLeft
              session={session}
              comment={comment}
              setComment={setComment}
              voted={voted}
              voteValue={voteValue}
              setVoteValue={setVoteValue}
              confirmVote={confirmVote}
              setConfirmVote={setConfirmVote}
              submitVote={submitVote}
              message={message}
              error={error}
              yourVoteValue={yourVoteValue}
            />
          ) : (
            <VoteRight pdfUrl={pdfUrl} />
          )}
        </div>
      </div>
    );
  }

  // ---------- Desktop ----------
  return (
    <div
      className="d-flex vote-desktop main-content"
      style={{ backgroundColor: "var(--bg-color)", color: "var(--text-color)" }}
    >
      <div className="w-50 border-end p-3 overflow-auto">
        <VoteLeft
          session={session}
          comment={comment}
          setComment={setComment}
          voted={voted}
          voteValue={voteValue}
          setVoteValue={setVoteValue}
          confirmVote={confirmVote}
          setConfirmVote={setConfirmVote}
          submitVote={submitVote}
          message={message}
          error={error}
          yourVoteValue={yourVoteValue}
        />
      </div>
      <div className="w-50 p-3 overflow-auto">
        <VoteRight pdfUrl={pdfUrl} apiBase={API_BASE} />
      </div>
    </div>
  );
}

export default VotePage;
