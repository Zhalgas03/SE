import React, { useEffect, useState } from "react";
import axios from "axios";
import { useUser } from "../context/UserContext"; // путь проверь!

const clean = (val) =>
  typeof val === "string"
    ? val.replace(/[^\x20-\x7Eа-яА-ЯёЁіІїЇґҐ\u0400-\u04FF]/g, "�")
    : val ?? "—";

const API_BASE = "http://localhost:5001";

function AdminPanelPage() {
  const { token, isAdmin, isAuthenticated } = useUser();
  const [users, setUsers] = useState([]);
  const [trips, setTrips] = useState([]);
  const [votes, setVotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 🗑️ Удаление пользователя
  const handleDeleteUser = async (userId, username, role) => {
    if (role === "admin") {
      alert("⚠️ You can't delete admin users.");
      return;
    }
  
    if (!window.confirm(`Delete user ${username}? This cannot be undone!`)) return;
  
    try {
      const response = await axios.delete(`${API_BASE}/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
  
      if (response.data.success) {
        setUsers((prev) => prev.filter((u) => u.id !== userId));
      } else {
        alert(response.data.message || "Failed to delete user.");
      }
    } catch (err) {
      const msg = err.response?.data?.message || "Error deleting user.";
      alert(msg); // Вот здесь гарантированно выводим
      console.error("[DELETE USER]", err);
    }
  };
  
  

  // 🗑️ Удаление поездки
  const handleDeleteTrip = async (tripId, tripName) => {
    if (!window.confirm(`Delete trip "${tripName}"? This cannot be undone!`)) return;
    try {
      await axios.delete(`${API_BASE}/api/admin/trips/${tripId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrips((prev) => prev.filter((t) => t.id !== tripId));
    } catch (err) {
      alert("Failed to delete trip.");
      console.error(err);
    }
  };

  // 🗑️ Удаление голосования
  const handleDeleteVote = async (voteId, voteTitle) => {
    if (!window.confirm(`Delete voting session "${voteTitle}"? This cannot be undone!`)) return;
    try {
      await axios.delete(`${API_BASE}/api/admin/votes/${voteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVotes((prev) => prev.filter((v) => v.id !== voteId));
    } catch (err) {
      alert("Failed to delete voting session.");
      console.error(err);
    }
  };

  useEffect(() => {
    if (!isAdmin || !token) return;
    setLoading(true);
    Promise.all([
      axios.get(`${API_BASE}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      axios.get(`${API_BASE}/api/admin/trips`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      axios.get(`${API_BASE}/api/admin/votes`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ])
      .then(([usersRes, tripsRes, votesRes]) => {
        setUsers(usersRes.data || []);
        setTrips(tripsRes.data || []);
        setVotes(votesRes.data || []);
        setError(null);
      })
      .catch((err) => {
        setError("Failed to load admin data.");
        console.error("Admin panel error:", err);
      })
      .finally(() => setLoading(false));
  }, [isAdmin, token]);

  if (!isAuthenticated) {
    return (
      <div style={{ padding: 32, fontSize: 22, textAlign: "center" }}>
        Please log in.
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div style={{ padding: 32, fontSize: 22, textAlign: "center", color: "red" }}>
        Not allowed. Only admin can see this page.
      </div>
    );
  }

  // Только для админа ниже 👇
  return (
    <div style={{ maxWidth: 1000, margin: "32px auto", padding: 24 }}>
      <h1 style={{ textAlign: "center", marginBottom: 32, color: "#248e46" }}>
        🛠️ Welcome, admin!
      </h1>

      {loading && <div style={{ fontSize: 20 }}>Загрузка...</div>}
      {error && <div style={{ color: "red", padding: 12 }}>{error}</div>}

      {/* Users */}
      <section style={{ marginBottom: 40 }}>
        <h2>👤 Users</h2>
        <div style={{ overflowX: "auto", border: "1px solid #eee", borderRadius: 8 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ background: "#f3f3f3" }}>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>2FA</th>
                <th>Subscribed</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: "center", padding: 12 }}>No users found.</td></tr>
              ) : users.map((u, i) => (
                <tr key={u.id || i}>
                  <td>{clean(u.username)}</td>
                  <td>{clean(u.email)}</td>
                  <td>{clean(u.role)}</td>
                  <td>{u.is_2fa_enabled ? "✅" : "❌"}</td>
                  <td>{u.is_subscribed ? "✅" : "❌"}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      style={{ fontSize: 13, padding: "3px 8px" }}
                      onClick={() => handleDeleteUser(u.id, u.username, u.role)}
                      disabled={u.role === "admin"}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Trips */}
      <section style={{ marginBottom: 40 }}>
        <h2>✈️ Trips</h2>
        <div style={{ overflowX: "auto", border: "1px solid #eee", borderRadius: 8 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ background: "#f3f3f3" }}>
              <tr>
                <th>Name</th>
                <th>Start</th>
                <th>End</th>
                <th>Creator</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {trips.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: "center", padding: 12 }}>No trips found.</td></tr>
              ) : trips.map((t, i) => (
                <tr key={t.id || i}>
                  <td>{clean(t.name)}</td>
                  <td>{clean(t.date_start)}</td>
                  <td>{clean(t.date_end)}</td>
                  <td>{clean(t.creator_username)}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      style={{ fontSize: 13, padding: "3px 8px" }}
                      onClick={() => handleDeleteTrip(t.id, t.name)}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Voting */}
      <section style={{ marginBottom: 40 }}>
        <h2>🗳️ Voting Sessions</h2>
        <div style={{ overflowX: "auto", border: "1px solid #eee", borderRadius: 8 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ background: "#f3f3f3" }}>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Creator</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {votes.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: "center", padding: 12 }}>No voting sessions found.</td></tr>
              ) : votes.map((v, i) => (
                <tr key={v.id || i}>
                  <td>{clean(v.title)}</td>
                  <td>{clean(v.status)}</td>
                  <td>{v.expires_at ? new Date(v.expires_at).toLocaleString() : "—"}</td>
                  <td>{clean(v.creator_username)}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      style={{ fontSize: 13, padding: "3px 8px" }}
                      onClick={() => handleDeleteVote(v.id, v.title)}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default AdminPanelPage;
