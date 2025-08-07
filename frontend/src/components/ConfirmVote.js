import React from "react";

function ConfirmVoteModal({ open, onClose, onConfirm, voteValue, comment }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-md shadow-lg max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Confirm your vote</h2>
        <p>
          Are you sure you want to vote <b>{voteValue === 1 ? "FOR" : "AGAINST"}</b>?
        </p>

        {comment && (
          <div className="mt-4">
            <p className="text-sm text-gray-500 mb-1">Comment:</p>
            <div className="border p-2 rounded bg-gray-100">
              {comment}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-4 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Vote
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmVoteModal;
