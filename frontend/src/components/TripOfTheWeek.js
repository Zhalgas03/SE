import React, { useEffect, useMemo, useState } from "react";
import { useUser } from "../context/UserContext";

export default function TripOfTheWeek({
  apiBase = "http://localhost:5001",
  trips = [],
  onSaved,
}) {
  const { isPremium, token } = useUser();

  // хуки — всегда вызываются
  const [weekly, setWeekly] = useState(null);
  const [saving, setSaving] = useState(false);

  const buildWeeklyName = (w) => {
    if (!w) return "";
    const metaTitle = w.meta?.title?.trim();
    const dst = w.summary?.destination?.trim();
    return metaTitle || dst || "Trip of the Week";
  };

  useEffect(() => {
    // если не премиум — просто ничего не грузим и чистим состояние
    if (!isPremium) {
      setWeekly(null);
      return;
    }
    (async () => {
      try {
        const r = await fetch(`${apiBase}/weekly/current`, {
          headers: { Authorization: `Bearer ${token || localStorage.getItem("token") || ""}` },
        });
        if (r.status === 401 || r.status === 403) {
          setWeekly(null);
          return;
        }
        const j = await r.json();
        if (j?.success) {
          setWeekly({
            token: j.token,
            preview_url: j.preview_url,
            summary: j.summary || {},
            meta: j.meta || {},
          });
        } else {
          setWeekly(null);
        }
      } catch (e) {
        console.warn("weekly/current failed", e);
        setWeekly(null);
      }
    })();
  }, [apiBase, token, isPremium]);

  const weeklyName = useMemo(() => buildWeeklyName(weekly), [weekly]);
  const isAlreadyAdded = useMemo(() => {
    const name = (weeklyName || "").toLowerCase();
    return !!name && trips.some((t) => (t?.name || "").trim().toLowerCase() === name);
  }, [trips, weeklyName]);

  const openPreview = () => {
    if (!weekly?.preview_url) return;
    const jwt = token || localStorage.getItem("token");
    const url = jwt ? `${weekly.preview_url}#rt=${jwt}` : weekly.preview_url;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const saveNow = async () => {
    if (!weekly?.token) return;
    if (isAlreadyAdded) {
      alert("You’ve already saved this Trip of the Week.");
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${apiBase}/weekly/save-favorite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token || localStorage.getItem("token") || ""}`,
        },
        body: JSON.stringify({ t: weekly.token }),
      });
      if (res.status === 401) {
        alert("Please log in to save this trip.");
        window.location.href = `/login?next=${encodeURIComponent("/favorites")}`;
        return;
      }
      if (res.status === 403) {
        alert("Premium feature. Upgrade to save this trip.");
        return;
      }
      const j = await res.json();
      if (j?.success) onSaved?.();
      else alert(j?.message || "Save failed");
    } catch {
      alert("Server error");
    } finally {
      setSaving(false);
    }
  };

  // рендер: если не премиум или нет weekly — ничего не показываем
  if (!isPremium || !weekly) return null;

  const destination = weekly.summary?.destination || "Trip of the Week";
  const days = weekly.meta?.duration_days || 5;
  const teaser = weekly.summary?.teaser || "";

  return (
    <div className="weekly-banner rounded-4 p-3 mb-4">
      <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between gap-3">
        <div>
          <div className="badge text-bg-warning mb-2">Trip of the Week</div>
          <h5 className="mb-1">🌟 {destination} — {days} {days === 1 ? "day" : "days"}</h5>
          {teaser && <p className="text-muted mb-2">{teaser}</p>}
        </div>
        <div className="d-flex gap-2 ms-md-auto">
          <button className="btn btn-outline-secondary btn-sm" onClick={openPreview}>
            🔎 Open preview
          </button>
          <button
            className={`btn btn-sm ${isAlreadyAdded ? "btn-outline-success" : "btn-primary"}`}
            onClick={saveNow}
            disabled={saving || isAlreadyAdded}
            title={isAlreadyAdded ? "Already saved" : "Save to favorites"}
          >
            {isAlreadyAdded ? "Saved ✓" : saving ? "Saving…" : "Save now"}
          </button>
        </div>
      </div>
    </div>
  );
}
