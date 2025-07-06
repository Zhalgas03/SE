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

  // Check if user has already voted for this trip
  useEffect(() => {
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

    checkVoteStatus();
  }, [tripId]);

  /**
   * Submit vote to the backend
   * @param {number} value - 1 for YES, -1 for NO
   */
  const submitVote = async (value) => {
    if (hasVoted || isVoting) return;

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
   * Generate voting link for sharing
   */
  const generateVotingLink = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Authentication required");
        return;
      }

      console.log(`🔗 Generating voting link for trip ${tripId}...`);
      const response = await fetch(`/api/votes/start/${tripId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        console.error(`❌ Voting link generation failed: ${response.status} ${response.statusText}`);
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.message || `Server error: ${response.status}`);
        return;
      }

      const data = await response.json();
      console.log("📊 Voting link response:", data);
      
      if (data.success && data.link) {
        await navigator.clipboard.writeText(data.link);
        console.log("✅ Voting link copied to clipboard:", data.link);
        alert("✅ Voting link copied to clipboard!\n\n" + data.link);
      } else {
        console.error("❌ Failed to generate voting link:", data.message);
        setError("Failed to generate voting link");
      }
    } catch (error) {
      console.error("❌ Network error generating voting link:", error);
      setError("Network error. Please check your connection and try again.");
    }
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

  // Show voting interface
  return (
    <div className="voting-interface">
      {hasVoted ? (
        <div className="text-center">
          <div className="alert alert-info">
            <strong>You have voted:</strong> {voteValue === 1 ? "👍 Yes" : "👎 No"}
          </div>
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={generateVotingLink}
            disabled={isVoting}
          >
            📋 Share Voting Link
          </button>
        </div>
      ) : (
        <div className="text-center">
          <p className="mb-3">Do you like this trip plan?</p>
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