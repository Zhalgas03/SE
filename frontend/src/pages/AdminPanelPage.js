import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { useUser } from "../context/UserContext";

import AdminSidebar from "../components/admin/AdminSidebar";
import StatCard from "../components/admin/StatCard";

import UsersTable from "../components/admin/UsersTable";
import TripsTable from "../components/admin/TripsTable";
import VotesTable from "../components/admin/VotesTable";
import AdminAnalyticsBoard from "../components/AdminAnalyticsBoard";

const API_BASE = "http://localhost:5001";

export default function AdminPanelPage() {
  const { token, isAdmin, isAuthenticated } = useUser();
  const [users, setUsers] = useState([]);
  const [trips, setTrips] = useState([]);
  const [votes, setVotes] = useState([]);
  const [totals, setTotals] = useState(null); // из /analytics
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // refs для якорной навигации
  const usersRef = useRef(null);
  const analyticsRef = useRef(null);
  const tripsRef = useRef(null);
  const votesRef = useRef(null);

  const jump = (key) => {
    const node = { users: usersRef, analytics: analyticsRef, trips: tripsRef, votes: votesRef }[key]?.current;
    if (node) node.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // DELETE handlers
  const handleDeleteUser = async (userId, username, role) => {
    if (role === "admin") return alert("⚠️ You can't delete admin users.");
    if (!window.confirm(`Delete user ${username}? This cannot be undone!`)) return;
    try {
      const r = await axios.delete(`${API_BASE}/api/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (r.data?.success) setUsers((prev) => prev.filter((u) => u.id !== userId));
      else alert(r.data?.message || "Failed to delete user.");
    } catch (e) {
      alert(e.response?.data?.message || "Error deleting user.");
    }
  };

  const handleDeleteTrip = async (tripId, tripName) => {
    if (!window.confirm(`Delete trip "${tripName}"? This cannot be undone!`)) return;
    try {
      const r = await axios.delete(`${API_BASE}/api/admin/trips/${tripId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (r.data?.success) setTrips((prev) => prev.filter((t) => t.id !== tripId));
      else alert(r.data?.message || "Failed to delete trip.");
    } catch {
      alert("Failed to delete trip.");
    }
  };

  const handleDeleteVote = async (voteId, voteTitle) => {
    if (!window.confirm(`Delete voting session "${voteTitle}"? This cannot be undone!`)) return;
    try {
      const r = await axios.delete(`${API_BASE}/api/admin/votes/${voteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (r.data?.success) setVotes((prev) => prev.filter((v) => v.id !== voteId));
      else alert(r.data?.message || "Failed to delete voting session.");
    } catch {
      alert("Failed to delete voting session.");
    }
  };

  // загрузка данных
  useEffect(() => {
    if (!isAuthenticated || !isAdmin || !token) return;
    setLoading(true);
    Promise.all([
      axios.get(`${API_BASE}/api/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`${API_BASE}/api/admin/trips`, { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`${API_BASE}/api/admin/votes`, { headers: { Authorization: `Bearer ${token}` } }),
      axios.get(`${API_BASE}/api/admin/analytics`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => null),
    ])
      .then(([u, t, v, a]) => {
        setUsers(u.data || []);
        setTrips(t.data || []);
        setVotes(v.data || []);
        setTotals(a?.data?.totals || null);
        setError(null);
      })
      .catch((err) => {
        setError("Failed to load admin data.");
        console.error("[ADMIN]", err);
      })
      .finally(() => setLoading(false));
  }, [isAuthenticated, isAdmin, token]);

  if (!isAuthenticated)
    return <div style={{ padding: 32, fontSize: 22, textAlign: "center" }}>Please log in.</div>;

  if (!isAdmin)
    return <div style={{ padding: 32, fontSize: 22, textAlign: "center", color: "red" }}>
      Not allowed. Only admin can see this page.
    </div>;

  // KPI-фоллбек если analytics не ответил
  const usersTotal = totals?.users_total ?? users.length;
  const premiumTotal = totals?.users_premium ?? users.filter(x => x.role === "premium").length;
  const tripsTotal = totals?.trips_total ?? trips.length;
  const votesTotal = totals?.votes_total ?? votes.length;

  return (
    <div className="admin-shell">
      <AdminSidebar onJump={jump} />

      <main className="admin-main">
        {/* Top bar */}
        <div className="admin-top">
          <div className="admin-top-title">Admin Dashboard</div>
          <div className="admin-top-state">{loading ? "Loading…" : error ? <span style={{ color: "red" }}>{error}</span> : "Ready"}</div>
        </div>

        {/* KPI row */}
        <div className="stat-row">
          <StatCard title="Users" value={usersTotal} hint={`${premiumTotal} premium`} />
          <StatCard title="Trips" value={tripsTotal} />
          <StatCard title="Votes" value={votesTotal} />
          <StatCard title="2FA Enabled" value={users.filter(u => u.is_2fa_enabled).length} />
        </div>

        {/* Analytics */}
        <section ref={analyticsRef} className="admin-section">
          <h2 className="admin-h2">📊 Analytics</h2>
          <AdminAnalyticsBoard />
        </section>

        {/* Users */}
        <section ref={usersRef} className="admin-section">
          <UsersTable users={users} onDelete={handleDeleteUser} />
        </section>



        {/* Trips */}
        <section ref={tripsRef} className="admin-section">
          <TripsTable trips={trips} onDelete={handleDeleteTrip} />
        </section>

        {/* Votes */}
        <section ref={votesRef} className="admin-section">
          <VotesTable votes={votes} onDelete={handleDeleteVote} />
        </section>
      </main>

      {/* Минимал стилей прямо здесь, чтобы ничего не тянуть */}
      <style>{`
        .admin-shell {
          display: grid;
          grid-template-columns: 240px 1fr;
          min-height: 100vh;
          background: #f6f7f9;
        }
        .admin-aside {
          background: #fff;
          border-right: 1px solid #eee;
          padding: 16px;
          position: sticky;
          top: 0;
          align-self: start;
          height: 100vh;
        }
        .admin-brand { font-weight: 800; font-size: 20px; margin-bottom: 12px; }
        .admin-nav { display: grid; gap: 6px; }
        .admin-link {
          text-align: left; width: 100%;
          padding: 10px 12px; border-radius: 8px; border: none; cursor: pointer;
          background: transparent; color: #333; font-size: 14px;
        }
        .admin-link:hover { background: #f2f4f7; }

        .admin-main { padding: 20px; }
        .admin-top {
          background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 12px 16px;
          display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
        }
        .admin-top-title { font-weight: 600; }
        .stat-row {
          display: grid; gap: 12px;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          margin-bottom: 16px;
        }
        .stat-card { background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 14px; }
        .stat-title { font-size: 12px; color: #6b7280; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .03em; }
        .stat-value { font-size: 24px; font-weight: 700; }
        .stat-hint { font-size: 12px; color: #6b7280; margin-top: 2px; }

        .admin-section { background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 16px; margin-bottom: 20px; }
        .admin-h2 { margin: 0 0 12px 0; font-size: 18px; }
      `}</style>
    </div>
  );
}
