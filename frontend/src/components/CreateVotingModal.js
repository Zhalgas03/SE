import React, { useState, useEffect, useRef } from "react";
import "./CreateVotingModal.css";

function CreateVotingModal({ open, onClose, trip, origin }) {
  const containerRef = useRef();
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [expectedVotes, setExpectedVotes] = useState(3);
  const [allowAnonymous, setAllowAnonymous] = useState(true);
  const [message, setMessage] = useState("");
  const [votingLink, setVotingLink] = useState("");

  // 👉 Сброс всех полей при открытии
  useEffect(() => {
    if (open && trip?.id) {
      const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
      const iso = tomorrow.toISOString().slice(0, 16); // 'YYYY-MM-DDTHH:mm'

      setTitle("");
      setDescription("");
      setExpiresAt(iso);
      setExpectedVotes(3);
      setAllowAnonymous(true);
      setMessage("");
      setVotingLink("");

      setIsVisible(true);
      setIsClosing(false);
    }
  }, [open, trip?.id]);

  // Scale-in эффект
  useEffect(() => {
    if (open && containerRef.current && origin) {
      const modal = containerRef.current;
      const x = origin.x - window.innerWidth / 2;
      const y = origin.y - window.innerHeight / 2;
      modal.style.transformOrigin = `${50 + (x / modal.offsetWidth) * 100}% ${50 + (y / modal.offsetHeight) * 100}%`;

      modal.classList.remove("scale-out");
      requestAnimationFrame(() => {
        modal.classList.add("scale-in");
      });
    }
  }, [open, origin]);

  const handleClose = () => {
    const modal = containerRef.current;
    modal.classList.remove("scale-in");
    modal.classList.add("scale-out");
    setIsClosing(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, 250);
  };

  const handleBackdropClick = (e) => {
    if (e.target.classList.contains("modal-overlay")) {
      handleClose();
    }
  };

  const handleCreate = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await fetch("http://localhost:5001/api/votes/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          trip_id: trip.id,
          title,
          description,
          expires_at: expiresAt,
          rules: {
            expected_votes: expectedVotes,
            anonymous_allowed: allowAnonymous,
          },
        }),
      });

      if (!res.ok) throw new Error("Failed to create voting");

      const data = await res.json();
      const fullLink = `${window.location.origin}/vote/${data.share_link}`;
      setVotingLink(fullLink);
      navigator.clipboard.writeText(fullLink);
      setMessage("✅ Voting created! Link copied.");
    } catch (err) {
      console.error(err);
      setMessage("❌ Error creating voting");
    }
  };

  if (!open && !isVisible) return null;

  return (
    <div className="modal-overlay" onClick={handleBackdropClick}>
      <div ref={containerRef} className="modal-container">
        <h2 className="modal-title">🗳️ Create Voting</h2>
        <p className="modal-subtitle">For “{trip?.name || "Unnamed Trip"}”</p>

        <label className="modal-label">Title</label>
        <input className="modal-input" value={title} onChange={(e) => setTitle(e.target.value)} />

        <label className="modal-label">Description</label>
        <textarea
          className="modal-textarea"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <div className="modal-row">
          <div>
            <label className="modal-label">Expires At</label>
            <input
              type="datetime-local"
              className="modal-input"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </div>
          <div>
            <label className="modal-label">Votes</label>
            <input
              type="number"
              className="modal-input"
              value={expectedVotes}
              min={1}
              onChange={(e) => setExpectedVotes(Number(e.target.value))}
            />
          </div>
        </div>

        <label className="modal-checkbox-label">
          <input
            type="checkbox"
            checked={allowAnonymous}
            onChange={(e) => setAllowAnonymous(e.target.checked)}
            className="modal-checkbox"
          />
          Allow anonymous voting
        </label>

        {message && <div className="modal-message">{message}</div>}
        {votingLink && (
          <div className="modal-link">
            <a href={votingLink} target="_blank" rel="noopener noreferrer">
              {votingLink}
            </a>
          </div>
        )}

        <div className="modal-buttons">
          <button className="modal-btn cancel" onClick={handleClose}>
            Cancel
          </button>
          <button className="modal-btn create" onClick={handleCreate}>
            + Create
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateVotingModal;
