import React, { useState, useEffect } from 'react';

/**
 * Voting Interface Component
 * Handles voting functionality with proper error handling and user feedback
 */
function VotingInterface({ tripId, onVoteComplete }) {
  const [hasVoted, setHasVoted] = useState(false);
  const [voteValue, setVoteValue] = useState(null); // null, 1 (yes), or -1 (no)
  const [isVoting, setIsVoting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [votingActive, setVotingActive] = useState(false);
  const [expiresAt, setExpiresAt] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [showDurationModal, setShowDurationModal] = useState(false);
  const [durationMinutes, setDurationMinutes] = useState(60); // Default 1 hour

  // Check if user has already voted for this trip
  const checkVoteStatus = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Authentication required to vote");
        return;
      }

      console.log(`🔍 Checking vote status for trip ${tripId}...`);
      const response = await fetch(`/api/votes/status/${tripId}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        console.error(`❌ Vote status check failed: ${response.status} ${response.statusText}`);
        setError(`Server error: ${response.status}`);
        return;
      }

      const data = await response.json();
      console.log("📊 Vote status response:", data);
      
      if (data.success) {
        setVotingActive(data.votingActive || false);
        setExpiresAt(data.expiresAt);
        
        if (data.hasVoted) {
          setHasVoted(true);
          setVoteValue(data.voteValue);
          console.log(`✅ User has already voted: ${data.voteValue === 1 ? 'Yes' : 'No'}`);
        } else {
          console.log("✅ User has not voted yet");
        }
      } else {
        console.error("❌ Error checking vote status:", data.message);
        setError(data.message || "Failed to check vote status");
      }
    } catch (error) {
      console.error("❌ Network error checking vote status:", error);
      setError("Network error. Please check your connection and try again.");
    }
  };

  useEffect(() => {
    checkVoteStatus();
  }, [tripId]);

  // Calculate and update time remaining
  useEffect(() => {
    if (!expiresAt) return;

    const updateTimeRemaining = () => {
      const now = new Date();
      const expires = new Date(expiresAt);
      const diff = expires - now;

      if (diff <= 0) {
        setTimeRemaining(null);
        setVotingActive(false);
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        setTimeRemaining(`${hours}h ${minutes}m`);
      }
    };

    updateTimeRemaining();
    const interval = setInterval(updateTimeRemaining, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [expiresAt]);

  /**
   * Submit vote to the backend
   * @param {number} value - 1 for YES, -1 for NO
   */
  const submitVote = async (value) => {
    if (hasVoted || isVoting || !votingActive) return;

    setIsVoting(true);
    setError(null);
    setSuccess(false);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Authentication token not found");
      }

      console.log(`🗳️ Submitting vote ${value} for trip ${tripId}...`);
      const response = await fetch(`/api/votes/${tripId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ value })
      });

      if (!response.ok) {
        console.error(`❌ Vote submission failed: ${response.status} ${response.statusText}`);
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.message || `Server error: ${response.status}`);
        return;
      }

      const data = await response.json();
      console.log("📊 Vote submission response:", data);

      if (data.success) {
        setHasVoted(true);
        setVoteValue(value);
        setSuccess(true);
        console.log(`✅ Vote submitted successfully: ${value === 1 ? 'Yes' : 'No'}`);
        
        // Call callback if provided
        if (onVoteComplete) {
          onVoteComplete(value);
        }
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(false), 3000);
      } else {
        console.error("❌ Vote submission failed:", data.message);
        setError(data.message || "Failed to submit vote");
      }
    } catch (error) {
      console.error("❌ Network error submitting vote:", error);
      setError("Network error. Please check your connection and try again.");
    } finally {
      setIsVoting(false);
    }
  };

  /**
   * Start voting session with duration
   */
  const startVotingSession = async (duration) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Authentication required");
        return;
      }

      console.log(`🔗 Starting voting session for trip ${tripId} with duration ${duration} minutes...`);
      const response = await fetch(`/api/votes/start/${tripId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ duration_minutes: duration })
      });

      if (!response.ok) {
        console.error(`❌ Voting session start failed: ${response.status} ${response.statusText}`);
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.message || `Server error: ${response.status}`);
        return;
      }

      const data = await response.json();
      console.log("📊 Voting session response:", data);
      
      if (data.success && data.link) {
        await navigator.clipboard.writeText(data.link);
        console.log("✅ Voting session started and link copied to clipboard:", data.link);
        alert(`✅ Voting session started!\n\nDuration: ${duration} minutes\nLink copied to clipboard:\n${data.link}`);
        
        // Refresh vote status to get updated expiration
        checkVoteStatus();
      } else {
        console.error("❌ Failed to start voting session:", data.message);
        setError("Failed to start voting session");
      }
    } catch (error) {
      console.error("❌ Network error starting voting session:", error);
      setError("Network error. Please check your connection and try again.");
    }
  };

  /**
   * Generate voting link for sharing (legacy function)
   */
  const generateVotingLink = async () => {
    setShowDurationModal(true);
  };

  // Show error message
  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <strong>Error:</strong> {error}
        <button 
          className="btn btn-sm btn-outline-danger ms-2"
          onClick={() => setError(null)}
        >
          Dismiss
        </button>
      </div>
    );
  }

  // Show success message
  if (success) {
    return (
      <div className="alert alert-success" role="alert">
        ✅ Thank you for your vote!
      </div>
    );
  }

  // Show duration modal
  if (showDurationModal) {
    return (
      <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Start Voting Session</h5>
              <button 
                type="button" 
                className="btn-close" 
                onClick={() => setShowDurationModal(false)}
              ></button>
            </div>
            <div className="modal-body">
              <p>Set the voting duration (5 minutes to 24 hours):</p>
              <div className="mb-3">
                <label htmlFor="durationInput" className="form-label">Duration (minutes):</label>
                <input
                  type="number"
                  className="form-control"
                  id="durationInput"
                  min="5"
                  max="1440"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(parseInt(e.target.value) || 60)}
                />
                <div className="form-text">
                  Minimum: 5 minutes, Maximum: 24 hours (1440 minutes)
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={() => setShowDurationModal(false)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={() => {
                  startVotingSession(durationMinutes);
                  setShowDurationModal(false);
                }}
              >
                Start Voting Session
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show voting interface
  return (
    <div className="voting-interface">
      {!votingActive && !hasVoted && (
        <div className="text-center">
          <div className="alert alert-warning">
            <strong>No active voting session</strong>
            <br />
            Start a voting session to allow voting on this trip.
          </div>
          <button
            className="btn btn-primary"
            onClick={generateVotingLink}
          >
            🗳️ Start Voting Session
          </button>
        </div>
      )}

      {!votingActive && hasVoted && (
        <div className="text-center">
          <div className="alert alert-info">
            <strong>Voting session has ended</strong>
            <br />
            You voted: {voteValue === 1 ? "👍 Yes" : "👎 No"}
          </div>
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={generateVotingLink}
          >
            🗳️ Start New Voting Session
          </button>
        </div>
      )}

      {votingActive && hasVoted && (
        <div className="text-center">
          <div className="alert alert-info">
            <strong>You have voted:</strong> {voteValue === 1 ? "👍 Yes" : "👎 No"}
            {timeRemaining && (
              <>
                <br />
                <small>Time remaining: {timeRemaining}</small>
              </>
            )}
          </div>
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={generateVotingLink}
          >
            📋 Share Voting Link
          </button>
        </div>
      )}

      {votingActive && !hasVoted && (
        <div className="text-center">
          <p className="mb-3">Do you like this trip plan?</p>
          {timeRemaining && (
            <div className="alert alert-info mb-3">
              <small>⏰ Voting ends in: {timeRemaining}</small>
            </div>
          )}
          <div className="d-flex justify-content-center gap-2">
            <button
              className="btn btn-success"
              onClick={() => submitVote(1)}
              disabled={isVoting}
            >
              {isVoting ? "Voting..." : "👍 Yes"}
            </button>
            <button
              className="btn btn-danger"
              onClick={() => submitVote(-1)}
              disabled={isVoting}
            >
              {isVoting ? "Voting..." : "👎 No"}
            </button>
          </div>
          <button
            className="btn btn-outline-secondary btn-sm mt-2"
            onClick={generateVotingLink}
            disabled={isVoting}
          >
            📋 Share Voting Link
          </button>
        </div>
      )}
    </div>
  );
}

export default VotingInterface; 