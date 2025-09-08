// src/components/AdminAnalyticsBoard.jsx
import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer,
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend, CartesianGrid,
} from "recharts";
import { useUser } from "../context/UserContext";

const API_BASE = "http://localhost:5001";
const CARD = { background: "#fff", borderRadius: 8, padding: 12, boxShadow: "0 1px 3px rgba(0,0,0,.08)" };
const COLORS = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#00C49F", "#0088FE", "#FFBB28", "#FF8042"];

export default function AdminAnalyticsBoard() {
  const { token } = useUser();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    axios
      .get(`${API_BASE}/api/admin/analytics`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((r) => setData(r.data))
      .catch((e) => setErr(e.response?.data?.message || "Failed to load analytics"))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div style={{ padding: 16 }}>Loading analytics…</div>;
  if (err) return <div style={{ padding: 16, color: "crimson" }}>{err}</div>;
  if (!data) return null;

  const { totals = {}, live = {}, ratios = {}, series = {}, trips = {}, recent = {} } = data;

  // нормализуем серии (на случай пустых)
  const usersPerMonth = series.users_per_month || [];
  const tripsPerMonth = series.trips_per_month || [];
  const votesPerMonth = series.votes_per_month || [];
  const votesByStatus = series.votes_by_status || [];
  const usersByRole = series.users_by_role || [];

  return (
    <div style={{ display: "grid", gap: 24 }}>
      {/* KPI */}
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(6, minmax(140px, 1fr))" }}>
        <Kpi title="Users" value={totals.users_total} />
        <Kpi title="Premium" value={totals.users_premium} sub={pct(ratios.premium_share)} />
        <Kpi title="2FA enabled" value={totals.users_2fa_enabled} sub={pct(ratios.twofa_share)} />
        <Kpi title="Trips" value={totals.trips_total} sub={`Upcoming: ${totals.trips_upcoming || 0}`} />
        <Kpi title="Votes" value={totals.votes_total} sub={`Active: ${totals.votes_active || 0}`} />
        <Kpi title="24h" value={`U ${live.users_new_24h || 0} · T ${live.trips_new_24h || 0} · V ${live.votes_new_24h || 0}`} />
      </div>

      {/* Линии по месяцам */}
      <div style={{ ...CARD, height: 280 }}>
        <h4 style={{ margin: 0, marginBottom: 8 }}>Users per month</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={usersPerMonth}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="cnt" name="Users" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "grid", gap: 24, gridTemplateColumns: "repeat(2, 1fr)" }}>
        <div style={{ ...CARD, height: 280 }}>
          <h4 style={{ margin: 0, marginBottom: 8 }}>Trips per month</h4>
          <ResponsiveContainer width="100%" height="100%">
<BarChart data={tripsPerMonth}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="month" />
  <YAxis allowDecimals={false} />
  <Tooltip />
  <Legend />
  <Bar dataKey="cnt" name="Trips">
    {tripsPerMonth.map((_, i) => (
      <Cell key={`t-${i}`} fill={COLORS[i % COLORS.length]} />
    ))}
  </Bar>
</BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ ...CARD, height: 280 }}>
          <h4 style={{ margin: 0, marginBottom: 8 }}>Votes per month</h4>
          <ResponsiveContainer width="100%" height="100%">
           <BarChart data={votesPerMonth}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="month" />
  <YAxis allowDecimals={false} />
  <Tooltip />
  <Legend />
  <Bar dataKey="cnt" name="Votes">
    {votesPerMonth.map((_, i) => (
      <Cell key={`v-${i}`} fill={COLORS[(i + 3) % COLORS.length]} />
    ))}
  </Bar>
</BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Пироги */}
      <div style={{ display: "grid", gap: 24, gridTemplateColumns: "repeat(2, 1fr)" }}>
        <div style={{ ...CARD, height: 410 }}>
          <h4 style={{ margin: 0, marginBottom: 8 }}>Votes by status</h4>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={votesByStatus} dataKey="cnt" nameKey="status" outerRadius={130} label>
                {votesByStatus.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ ...CARD, height: 410 }}>
          <h4 style={{ margin: 0, marginBottom: 8 }}>Users by role</h4>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={usersByRole} dataKey="cnt" nameKey="role" outerRadius={130} label>
                {usersByRole.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Топы и средние */}
      <div style={{ ...CARD }}>
        <h4 style={{ margin: 0, marginBottom: 12 }}>Trips insights</h4>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(3, 1fr)" }}>
          <div>
            <div style={{ fontSize: 13, color: "#666" }}>Average duration</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{(trips.avg_duration_days || 0).toFixed(1)} days</div>
          </div>
          <div>
            <div style={{ fontSize: 13, color: "#666" }}>Top creators</div>
            <ol style={{ margin: 0, paddingLeft: 18 }}>
              {(trips.top_creators || []).map((r) => (
                <li key={r.creator_username}>{r.creator_username} — {r.cnt}</li>
              ))}
            </ol>
          </div>
          <div>
            <div style={{ fontSize: 13, color: "#666" }}>Popular trip names</div>
            <ol style={{ margin: 0, paddingLeft: 18 }}>
              {(trips.top_names || []).map((r) => (
                <li key={r.name}>{r.name} — {r.cnt}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>

      {/* Последние записи */}
      <div style={{ display: "grid", gap: 24, gridTemplateColumns: "1fr 1fr" }}>
        <RecentTable
  title="Recent users"
  icon="people"
  rows={recent.users || []}
  cols={[
    { k: "username", h: "Username" },
    { k: "role", h: "Role" },
    { k: "created_at", h: "Created", fmt: (d) => (d ? new Date(d).toLocaleString() : "—") },
  ]}
/>

<RecentTable
  title="Recent trips"
  icon="map"
  rows={recent.trips || []}
  cols={[
    { k: "name", h: "Name" },
    { k: "creator_username", h: "Creator" },
    { k: "date_start", h: "Start", fmt: (d) => (d ? new Date(d).toLocaleDateString() : "—") },
    { k: "date_end", h: "End", fmt: (d) => (d ? new Date(d).toLocaleDateString() : "—") },
  ]}
/>

<RecentTable
  title="Recent voting sessions"
  icon="check2-square"
  rows={recent.votes || []}
  cols={[
    { k: "title", h: "Title" },
    { k: "status", h: "Status" },
    { k: "expires_at", h: "Expires", fmt: (d) => (d ? new Date(d).toLocaleString() : "—") },
    { k: "creator_username", h: "Creator", right: true },
  ]}
/>

      </div>
    </div>
  );
}

/* helpers */
function Kpi({ title, value, sub }) {
  return (
    <div style={{ ...CARD }}>
      <div style={{ fontSize: 13, color: "#666" }}>{title}</div>
      <div style={{ fontSize: 26, fontWeight: 700 }}>{value ?? 0}</div>
      {sub ? <div style={{ fontSize: 12, color: "#888" }}>{sub}</div> : null}
    </div>
  );
}
const pct = (x) => `${Math.round((x || 0) * 100)}%`;
const time = (s) => (s ? new Date(s).toLocaleString() : "—");
const dateOnly = (s) => (s ? new Date(s).toLocaleDateString() : "—");

function RecentTable({ title, rows = [], cols = [], icon = "clock-history" }) {
  return (
    <section className="mb-4">
      {/* Header */}
      <div
        className="d-flex align-items-center justify-content-between px-3 py-2 rounded-top"
        style={{
          background: "#1e88e5",
          color: "#fff",
          boxShadow: "0 1px 3px rgba(0,0,0,.08)",
        }}
      >
        <div className="fw-semibold">
          <i className={`bi bi-${icon} me-2`} />
          {title}
        </div>
        <div className="small opacity-75">{rows.length} total</div>
      </div>

      {/* Table */}
      <div
        className="rounded-bottom"
        style={{
          border: "1px solid #e9ecef",
          borderTop: "none",
          boxShadow: "0 2px 4px rgba(0,0,0,.04)",
          overflow: "hidden",
        }}
      >
        <div className="table-responsive">
          <table className="table table-sm table-striped mb-0 align-middle" style={{ fontSize: 14 }}>
            <thead style={{ background: "#f8f9fa" }}>
              <tr className="text-muted">
                {cols.map((c) => (
                  <th key={c.k} className={`fw-semibold ${c.right ? "text-end pe-3" : "ps-3"}`}>
                    {c.h}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={cols.length} className="text-center py-4 text-muted">
                    <i className="bi bi-inboxes me-2" />
                    No data
                  </td>
                </tr>
              ) : (
                rows.map((r, i) => (
                  <tr key={i} className="border-top">
                    {cols.map((c) => {
                      const raw = r[c.k];
                      const val = c.fmt ? c.fmt(raw, r) : raw ?? "—";
                      return (
                        <td
                          key={c.k}
                          className={`${c.right ? "text-end pe-3" : "ps-3"}`}
                          style={{ whiteSpace: "nowrap" }}
                        >
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
