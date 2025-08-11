import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import PdfViewer from "../components/PdfViewer";
import axios from "axios";
import ConfirmVoteModal from "../components/ConfirmVote";

function VotePage() {
  const { share_link } = useParams();
  const [session, setSession] = useState(null);
  const [voteValue, setVoteValue] = useState(null);
  const [comment, setComment] = useState("");
  const [voted, setVoted] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [confirmVote, setConfirmVote] = useState(false);

  const fetchSession = async () => {
    try {
      const res = await axios.get(`/api/votes/results/${share_link}`);
      setSession(res.data);
      setVoted(res.data.you_voted);
    } catch (err) {
      console.error(err);
      setError("Error loading voting session.");
    }
  };

  useEffect(() => {
    fetchSession();
  }, [share_link]);

  const submitVote = async () => {
    try {
      const res = await axios.post("/api/votes/submit", {
        share_link,
        value: voteValue,
        comment: comment || undefined,
      });
      setMessage("Vote counted!");
      setVoteValue(null);
      setComment("");
      setConfirmVote(false);
      await fetchSession();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.message || "Error voting.");
    }
  };

  if (!session) return <div className="p-6">Loading...</div>;

  const { title, description, status, expires_at, counts, comments } = session;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">{title}</h1>
      <p className="text-gray-700 mb-4">{description}</p>

      {status === "completed" ? (
        <p className="text-green-700 font-semibold mb-2">Voting completed</p>
      ) : new Date(expires_at) < new Date() ? (
        <p className="text-red-700 font-semibold mb-2">Voting expired</p>
      ) : (
        <p className="text-blue-700 mb-2">Voting active until {new Date(expires_at).toLocaleString()}</p>
      )}

      <PdfViewer url={`/static/trips/${session.share_link}.pdf`} />

      <div className="my-4">
        <h2 className="font-semibold mb-1">Statistics:</h2>
        <p>Total votes: {counts.total}</p>
        <p>For: {counts.for}</p>
        <p>Against: {counts.against}</p>
      </div>

      {!voted && status === "active" && new Date(expires_at) > new Date() && (
        <div className="bg-gray-100 p-4 rounded mb-6">
          <h2 className="font-semibold mb-2">Your vote:</h2>
          <textarea
            placeholder="Comment (optional)"
            className="w-full border rounded p-2 mb-2"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <div className="flex gap-4">
            <button
              onClick={() => {
                setVoteValue(1);
                setConfirmVote(true);
              }}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              👍 For
            </button>
            <button
              onClick={() => {
                setVoteValue(0);
                setConfirmVote(true);
              }}
              className="bg-red-600 text-white px-4 py-2 rounded"
            >
              👎 Against
            </button>
          </div>
        </div>
      )}

      {voted && <p className="text-green-600 mb-4">You have already voted</p>}
      {message && <p className="text-green-700 mb-4">{message}</p>}
      {error && <p className="text-red-700 mb-4">{error}</p>}

      <div className="mt-6">
        <h2 className="font-semibold mb-2">Comments:</h2>
        {comments.length === 0 ? (
          <p className="text-gray-500">No comments yet</p>
        ) : (
          comments.map((c, idx) => (
            <div key={idx} className="mb-2">
              <strong>{c.username}</strong> —{" "}
              <span className="text-sm text-gray-500">
                {new Date(c.created_at).toLocaleString()}
              </span>
              <p>{c.comment}</p>
            </div>
          ))
        )}
      </div>

      <ConfirmVoteModal
        open={confirmVote}
        onClose={() => setConfirmVote(false)}
        onConfirm={submitVote}
        voteValue={voteValue}
        comment={comment}
        setComment={setComment}
      />
    </div>
  );
}

export default VotePage;
