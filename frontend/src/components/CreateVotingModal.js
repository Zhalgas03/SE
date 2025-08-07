import React, { useState } from "react";
import axios from "axios";

function CreateVotingModal({ open, onClose, trip }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [expectedVotes, setExpectedVotes] = useState(3);
  const [allowAnonymous, setAllowAnonymous] = useState(true);
  const [message, setMessage] = useState("");
  const [votingLink, setVotingLink] = useState("");

  const handleCreate = async () => {
    try {
      const token = localStorage.getItem("token");
  
      const res = await axios.post("http://localhost:5001/api/votes/sessions", {
        trip_id: trip.id,
        title,
        description,
        expires_at: expiresAt,
        rules: {
          expected_votes: expectedVotes,
          anonymous_allowed: allowAnonymous,
        },
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
  
      const { share_link } = res.data;
      setMessage("Voting created! Link copied.");
      navigator.clipboard.writeText(`${window.location.origin}/vote/${share_link}`);
      setVotingLink(`${window.location.origin}/vote/${share_link}`);

    } catch (err) {
      console.error(err);
      setMessage("Error creating voting");
    }
  };

  if (!open || !trip) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Create voting for «{trip.name}»</h2>

        <input
          className="w-full border p-2 mb-2"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className="w-full border p-2 mb-2"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <input
          type="datetime-local"
          className="w-full border p-2 mb-2"
          value={expiresAt}
          onChange={(e) => setExpiresAt(e.target.value)}
        />
        <input
          type="number"
          min="1"
          className="w-full border p-2 mb-2"
          placeholder="Expected number of votes"
          value={expectedVotes}
          onChange={(e) => setExpectedVotes(Number(e.target.value))}
        />
        <label className="flex items-center mb-4">
          <input
            type="checkbox"
            checked={allowAnonymous}
            onChange={(e) => setAllowAnonymous(e.target.checked)}
            className="mr-2"
          />
          Allow anonymous voting
        </label>

        {message && <p className="text-blue-600 mb-2">{message}</p>}
        {votingLink && (
            <div className="mt-2">
                <p className="text-sm text-gray-600">Shareable link:</p>
                <a
                href={votingLink}
                className="text-blue-700 underline break-all"
                target="_blank"
                rel="noopener noreferrer"
                >
                {votingLink}
                </a>
            </div>
        )}
        <div className="flex justify-between">
          <button className="bg-gray-500 text-white px-4 py-2 rounded" onClick={onClose}>
            Cancel
          </button>
          <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={handleCreate}>
            Create
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateVotingModal;
