// ConfirmVoteModal.js
import React from "react";
import "../styles/ConfirmVoteModal.css";

function ConfirmVoteModal({ open, onClose, onConfirm, voteValue, comment }) {
  if (!open) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <h2 className="modal-title">Confirm your vote</h2>
        <p className="modal-question">
          Are you sure you want to vote <b>{voteValue === 1 ? "FOR" : "AGAINST"}</b>?
        </p>

        {comment && (
          <div className="modal-comment-block">
            <p className="modal-comment-label">Comment:</p>
            <div className="modal-comment-content">{comment}</div>
          </div>
        )}

        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-vote" onClick={onConfirm}>
            Vote
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmVoteModal;
