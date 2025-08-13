import React, { useEffect, useState } from "react";

export default function TripOfTheWeek({ apiBase = "http://localhost:5001" }) {
  const [weekly, setWeekly] = useState(null);
  const [loadingWeekly, setLoadingWeekly] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${apiBase}/weekly/current`);
        const j = await r.json();
        if (!cancelled && j?.success) {
          setWeekly({
            token: j.token,
            preview_url: j.preview_url,
            destination: j.summary?.destination || "Trip of the Week",
            teaser: j.summary?.teaser || "",
            days: j.meta?.duration_days || 5,
          });
        }
      } catch (e) {
        console.warn("weekly/current failed", e);
      } finally {
        if (!cancelled) setLoadingWeekly(false);
      }
    })();
    return () => { cancelled = true; };
  }, [apiBase]);

  const openPreview = () => {
    if (!weekly?.preview_url) return;
    const jwt = localStorage.getItem("token");
    const url = jwt ? `${weekly.preview_url}#rt=${jwt}` : weekly.preview_url;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const saveNow = async () => {
    if (!weekly?.token) return;
    setSaving(true);
    try {
      const res = await fetch(`${apiBase}/weekly/save-favorite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
        },
        body: JSON.stringify({ t: weekly.token }),
      });
      if (res.status === 401) {
        alert("Please log in to save this trip.");
        window.location.href = `/login?next=${encodeURIComponent(weekly.preview_url)}`;
        return;
      }
      const j = await res.json();
      if (j?.success) {
        // мягко: просто дернем обновление страницы избранного
        window.location.href = "/favorites?just_saved=1";
      } else {
        alert(j?.message || "Save failed");
      }
    } catch (e) {
      console.error(e);
      alert("Server error");
    } finally {
      setSaving(false);
    }
  };

  if (loadingWeekly || !weekly) return null;

  return (
    <div className="weekly-banner rounded-4 p-3 mb-4">
      <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between gap-3">
        <div>
          <div className="badge text-bg-warning mb-2">Trip of the Week</div>
          <h5 className="mb-1">🌟 {weekly.destination} — {weekly.days} days</h5>
          {weekly.teaser && <p className="text-muted mb-2">{weekly.teaser}</p>}
        </div>
        <div className="d-flex gap-2 ms-md-auto">
          <button className="btn btn-outline-secondary btn-sm" onClick={openPreview}>
            🔎 Open preview
          </button>
          <button className="btn btn-primary btn-sm" onClick={saveNow} disabled={saving}>
            {saving ? "Saving…" : "➕ Save now"}
          </button>
        </div>
      </div>
    </div>
  );
}
