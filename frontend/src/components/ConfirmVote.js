// ConfirmVoteModal.js
import React, { useState } from "react";
import "../styles/ConfirmVoteModal.css";

function ConfirmVoteModal({ open, onClose, onConfirm, voteValue, comment }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!open) return null;

  const handleConfirm = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      // поддержка как async, так и sync обработчиков
      await Promise.resolve(onConfirm());
    } finally {
      // если родитель не закроет модалку, снимаем лоадер
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" aria-busy={isSubmitting}>
      <div className="modal-box" role="dialog" aria-modal="true">
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
          <button
            className="btn-cancel"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </button>

          <button
            className={`btn-vote ${isSubmitting ? "is-loading" : ""}`}
            onClick={handleConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting && <span className="spinner" aria-hidden="true" />}
            {isSubmitting ? "Voting..." : "Vote"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmVoteModal;
