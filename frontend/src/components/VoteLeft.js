import React from "react";
import ConfirmVoteModal from "./ConfirmVote";
import "../styles/VoteLeft.css";

function VoteLeft({
  session,
  comment,
  setComment,
  voted,
  voteValue,
  setVoteValue,
  confirmVote,
  setConfirmVote,
  submitVote,
  message,
  error,
  yourVoteValue,
}) {
  if (!session) return null;

  const { title, description, status, expires_at, counts, comments, created_at } = session;

  const now = new Date();
  const end = new Date(expires_at);
  const start = new Date(created_at);
  const total = end - start;
  const elapsed = now - start;
  const progress = Math.max(0, Math.min(1, elapsed / total));

  const remaining = end - now;
  const timeLeftText =
    remaining <= 0
      ? "Expired"
      : remaining < 60 * 60 * 1000
      ? `${Math.floor(remaining / (60 * 1000))} min left`
      : `${Math.floor(remaining / (60 * 60 * 1000))} h left`;

  const percentFor = counts.total ? (counts.for / counts.total) * 100 : 0;
  const percentAgainst = counts.total ? (counts.against / counts.total) * 100 : 0;

  let progressColor = "#3b82f6"; // default: blue
  if (progress > 0.75) progressColor = "#facc15";
  if (progress > 0.9) progressColor = "#ef4444";

  return (
    <div className="vote-wrapper">
      <div className="vote-card">
        <h1 className="vote-title">{title}</h1>
        <p className="vote-description">{description}</p>

        <p className="vote-status">🕓 Voting active until {end.toLocaleString()}</p>
        <div className="vote-progress-bar">
          <div
            className="vote-progress-fill"
            style={{
              width: `${progress * 100}%`,
              backgroundColor: progressColor,
            }}
          ></div>
        </div>
        <p className="vote-progress-label">{timeLeftText}</p>

        <hr />

        {/* Statistics */}
        <div className="vote-section">
          <h2 className="vote-section-title">📊 Statistics</h2>
          <div className="vote-stat-total">
            Total votes: <strong>{counts.total}</strong>
          </div>
          <div className="vote-stat-row">
            <div className="vote-stat-box vote-stat-for">
              <div className="vote-stat-fill" style={{ width: `${percentFor}%` }}></div>
              <div className="vote-stat-box-content">
                <div className="vote-stat-label">Votes For</div>
                <div className="vote-stat-count">{counts.for}</div>
              </div>
            </div>
            <div className="vote-stat-box vote-stat-against">
              <div className="vote-stat-fill" style={{ width: `${percentAgainst}%` }}></div>
              <div className="vote-stat-box-content">
                <div className="vote-stat-label">Votes Against</div>
                <div className="vote-stat-count">{counts.against}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Voting section */}
        <div className="vote-section">
          <h2 className="vote-section-title">🗳️ Your vote</h2>

          {status !== "active" || end <= now ? (
            <p className="vote-voted-text">❌ Voting session has ended</p>
          ) : voted ? (
            <div className="vote-voted-text">
              ✅ You already voted. You cannot vote again.
              <br />
              You voted: <strong>{yourVoteValue === 1 ? "FOR 👍" : "AGAINST 👎"}</strong>
            </div>
          ) : (
            <>
              <textarea
                className="vote-comment"
                placeholder="Comment (optional)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              {error && (
                <div className="vote-error-text">
                  ❌ {error}
                </div>
              )}
              <div className="vote-buttons">
                <button
                  className="vote-button vote-button-for"
                  onClick={() => {
                    setVoteValue(1);
                    setConfirmVote(true);
                  }}
                >
                  For 👍
                </button>
                <button
                  className="vote-button vote-button-against"
                  onClick={() => {
                    setVoteValue(0);
                    setConfirmVote(true);
                  }}
                >
                  Against 👎
                </button>
              </div>
            </>
          )}
        </div>

        {/* Comments section */}
        <div className="vote-section">
          <h2 className="vote-section-title">💬 Comments</h2>
          {comments.length === 0 ? (
            <p className="vote-no-comments">No comments yet</p>
          ) : (
            comments.map((c, idx) => (
              <div key={idx} className="vote-comment-item">
                <div className="vote-comment-meta">
                  <span className="vote-comment-user">{c.username}</span>
                  <span className="vote-comment-time">
                    {new Date(c.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="vote-comment-text">{c.comment}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Confirmation modal */}
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

export default VoteLeft;