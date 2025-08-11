import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import VoteLeft from "../components/VoteLeft";
import VoteRight from "../components/VoteRight";
import "./VotePage.css"; // добавим стиль ниже

function VotePage() { 
  const { share_link } = useParams();
  const [session, setSession] = useState(null);
  const [voteValue, setVoteValue] = useState(null);
  const [comment, setComment] = useState("");
  const [voted, setVoted] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [confirmVote, setConfirmVote] = useState(false);
  const [yourVoteValue, setYourVoteValue] = useState(null);


  const fetchSession = async () => {
    try {
      const res = await axios.get(`http://localhost:5001/api/votes/results/${share_link}`, {
        withCredentials: true,
      });
      setSession(res.data);
      setYourVoteValue(res.data.your_vote_value);
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
      const res = await axios.post("http://localhost:5001/api/votes/submit", {
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
      const message = err.response?.data?.message || "Something went wrong";
  
      // Покажем модалку снова, если ошибка
      setError(message);
      setConfirmVote(false);
  
      // Если уже голосовал — явно покажем предупреждение
      if (message === "You already voted") {
        alert("⚠️ You already voted. You cannot vote again.");
        await fetchSession(); // Обновим статус
      }
    }
  };

  if (!session) return <div className="vote-container">Loading...</div>;

  return (
    <div className="vote-container">
      <div className="vote-left">
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
        />
      </div>
      <div className="vote-right">
        <VoteRight />
      </div>
    </div>
  );
}

export default VotePage;