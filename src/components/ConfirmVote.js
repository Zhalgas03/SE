import { useState } from "react";

function ConfirmVoteModal({ open, onClose, onConfirm, voteValue, comment, setComment }) {
  const [submitting, setSubmitting] = useState(false);

  const handleConfirm = async () => {
    setSubmitting(true);
    await onConfirm();
    setSubmitting(false);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Confirm your vote</h2>
        <div className="mb-4">
          <p>
            Are you sure you want to vote <b>{voteValue === 1 ? "FOR" : "AGAINST"}</b>?
          </p>
          {comment && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Comment:</p>
              <p className="text-base border p-2 rounded-md bg-gray-50">
                {comment}
              </p>
            </div>
          )}
        </div>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={submitting}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Voting..." : "Vote"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmVoteModal;
