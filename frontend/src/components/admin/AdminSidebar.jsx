import React from "react";

export default function AdminSidebar({ onJump }) {
  return (
    <aside className="admin-aside">
      <nav className="admin-nav">
        <button onClick={() => onJump("analytics")} className="admin-link">📊 Analytics</button>
        <button onClick={() => onJump("users")}  className="admin-link">👤 Users</button>
        <button onClick={() => onJump("trips")}  className="admin-link">✈️ Trips</button>
        <button onClick={() => onJump("votes")}  className="admin-link">🗳️ Votes</button>
      </nav>
    </aside>
  );
}
