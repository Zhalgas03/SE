// src/components/TripComponents/TripStay.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Card } from "react-bootstrap";

// ------- helpers (совпадают по духу с TripTransfer) -------
function extractFromToFromText(text = "") {
  const t = (text || "").replace(/\s+/g, " ").trim();
  let m = t.match(/([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s*(?:→|->)\s*([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+)/);
  if (m) return { from: m[1].trim().replace(/,$/, ""), to: m[2].trim().replace(/,$/, "") };
  m = t.match(/\bfrom\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s+to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)([.,]|$)/i);
  if (m) return { from: m[1].trim(), to: m[2].trim() };
  m = t.match(/\b(?:back\s+)?to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s+from\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)([.,]|$)/i);
  if (m) return { from: m[2].trim(), to: m[1].trim() };
  return { from: null, to: null };
}

function toCityName(place = "") {
  if (!place) return null;
  let s = place.replace(/\(.*?\)/g, " ");
  s = s.split(" / ")[0].split(" - ")[0];
  s = s.split(",")[0];
  const raw = s.trim().replace(/\s+/g, " ");
  return raw || null;
}

// точный парсер дат (поддерживает "15th September to 19th September", "September 15 to September 19", ISO)
function parseDates(dates) {
  if (!dates) return { start: null, end: null };
  if (typeof dates === "object" && (dates.start || dates.end)) {
    return { start: dates.start || null, end: dates.end || null };
  }
  const norm = String(dates)
    .replace(/\b(\d{1,2})(st|nd|rd|th)\b/gi, "$1")
    .replace(/\s+/g, " ")
    .trim();

  let m = norm.match(
    /(?:(\d{1,2})\s+([A-Za-z]+)|([A-Za-z]+)\s+(\d{1,2}))\s+to\s+(?:(\d{1,2})\s+([A-Za-z]+)|([A-Za-z]+)\s+(\d{1,2}))/i
  );
  if (m) {
    const d1 = m[1] || m[4], mon1 = m[2] || m[3];
    const d2 = m[5] || m[8], mon2 = m[6] || m[7];
    const year = new Date().getFullYear();
    const toISO = (d, mon) => {
      const dt = new Date(`${mon} ${d}, ${year}`);
      return Number.isNaN(dt.getTime()) ? null : dt.toISOString().slice(0, 10);
    };
    return { start: toISO(d1, mon1), end: toISO(d2, mon2) };
  }

  m = norm.match(/(\d{4}-\d{2}-\d{2}).+?(\d{4}-\d{2}-\d{2})/);
  if (m) return { start: m[1], end: m[2] };

  return { start: null, end: null };
}

function nightsCount(a, b) {
  if (!a || !b) return 1;
  const ms = new Date(b) - new Date(a);
  return Math.max(1, Math.round(ms / 86400000));
}

function RatingView({ rating }) {
  if (!rating) return null;
  const num = Number(rating);
  if (!Number.isFinite(num)) return null;
  if (num <= 5) {
    const stars = Math.round(num);
    return <span title={`${num}★`}>{"★".repeat(stars)}{"☆".repeat(5 - stars)}</span>;
  }
  return <span>{num.toFixed(1)}/10</span>;
}

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5001";

function pickStayCity(summary) {
  const dest = toCityName(summary?.destination || summary?.Destination);
  if (dest) return dest;

  const tr = Array.isArray(summary?.transfers) ? summary.transfers[0] : null;
  const txt = (tr?.route || tr?.details || "").toLowerCase();
  const { from, to } = extractFromToFromText(tr?.route || tr?.details || "");
  const fromCity = toCityName(from);
  const toCity = toCityName(to);

  if (/back\s+to|return\s+to/.test(txt)) return fromCity || dest || toCity;
  return fromCity || dest || toCity || null;
}

// -------------------- Component --------------------
export default function TripStay({ summary }) {
  const city = useMemo(() => pickStayCity(summary), [summary]);
  const datesParsed = useMemo(() => parseDates(summary?.travel_dates || summary?.Dates), [summary]);
  const haveDates = !!(datesParsed.start && datesParsed.end);
  const nights = useMemo(() => nightsCount(datesParsed.start, datesParsed.end), [datesParsed]);

  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState(null);
  const [err, setErr] = useState(null);

  const canQuery = !!(city && haveDates);

  useEffect(() => {
    if (!canQuery) return;
    const controller = new AbortController();

    const fetchHotels = async (radiusKm) => {
      const params = new URLSearchParams({
        city,
        checkin: datesParsed.start,
        checkout: datesParsed.end,
        rooms: "1",
        adults: "1",
        radius_km: String(radiusKm),
        max: "100", // запрашиваем побольше, чтобы было из чего выбирать
      });
      const res = await fetch(`${API_BASE}/api/hotel?${params.toString()}`, {
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    };

    (async () => {
      try {
        setLoading(true);
        setErr(null);
        setOptions([]);
        setMeta(null);

        for (const r of [12, 20, 30]) {
          const js = await fetchHotels(r);
          if (js?.success && Array.isArray(js.options) && js.options.length > 0) {
            setOptions(js.options);
            setMeta(js.meta || null);
            return;
          }
          setMeta(js?.meta || null);
        }
        setOptions([]);
      } catch (e) {
        if (e.name !== "AbortError") {
          setErr(e.message || "Request failed");
          setOptions([]);
        }
      } finally {
        setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [canQuery, city, datesParsed.start, datesParsed.end]);

  // ---------- новинка: выбор стиля/бюджета + вычисление итоговых 6 ----------
  const travelStyleRaw = (summary?.travel_style || summary?.TravelStyle || "").toString().toLowerCase();
  const travelStyle = /^(budget|relaxed|luxury)$/.test(travelStyleRaw) ? travelStyleRaw : "budget";

  const dailyBudget = useMemo(() => {
    const raw = (summary?.budget || summary?.Budget || "").toString();
    const m = raw.match(/(\d+(?:[.,]\d+)?)/);
    return m ? parseFloat(m[1].replace(",", ".")) : null;
  }, [summary]);

  const perNight = (o) => {
    const total = o?.price?.amount ?? null;
    if (total == null) return Infinity;
    return total / Math.max(1, nights || 1);
  };
  const rating10 = (o) => {
    const r = Number(o?.rating);
    if (!Number.isFinite(r)) return 6;
    return r <= 5 ? r * 2 : r;
  };
  const distKm = (o) => {
    const v = o?.distance?.value;
    return v == null ? 5 : Number(v);
  };
  const hasBreakfast = (o) => /breakfast|half\s*board/i.test(o?.board_type || "");
  const isBrand = (o) => /(hilton|marriott|hyatt|accor|ibis|novotel|mercure|radisson|ritz|four\s*seasons)/i.test(o?.name || "");

  const scoreRelaxed = (o) =>
    0.45 * rating10(o) +
    0.35 * (1 / (1 + distKm(o))) +
    0.20 * (1 / (1 + perNight(o))) +
    (hasBreakfast(o) ? 0.2 : 0) +
    (isBrand(o) ? 0.2 : 0);

  const scoreLuxury = (o) =>
    0.55 * rating10(o) +
    0.20 * (isBrand(o) ? 1 : 0) +
    0.15 * (hasBreakfast(o) ? 1 : 0) +
    0.10 * (1 / (1 + perNight(o)));

  const shownOptions = useMemo(() => {
    if (!Array.isArray(options) || options.length === 0) return [];

    let pool = options;
    let note = null;

    if (travelStyle === "budget") {
      // уже по цене; фильтруем по бюджету (строго), мягко расширяем до +15% если нужно
      if (dailyBudget != null) {
        const strict = pool.filter(o => perNight(o) <= dailyBudget);
        if (strict.length >= 6) {
          pool = strict;
        } else {
          const soft = pool.filter(o => perNight(o) <= dailyBudget * 1.15);
          if (soft.length >= 6) {
            pool = soft;
            note = "Budget relaxed to +15% to fill results.";
          } else {
            // добираем без фильтра, но пометим выход за бюджет
            note = "Some picks exceed daily budget.";
          }
        }
      }
      // порядок не меняем — уже по цене
      pool = pool.slice(0, 6);
    } else if (travelStyle === "relaxed") {
      // мягкий учёт бюджета — отсекаем только экстремально дорогие, если есть dailyBudget
      let base = options;
      if (dailyBudget != null) {
        const softCap = dailyBudget * 2.0; // не жёстко, но удерживаем в разумных пределах
        base = options.filter(o => perNight(o) <= softCap) || options;
        if (base.length < 6) {
          base = options; // если совсем мало — вернём всё
          note = "Budget used softly; showing best comfort picks.";
        }
      }
      pool = [...base]
        .map(o => ({ o, s: scoreRelaxed(o) }))
        .sort((a, b) => b.s - a.s || (perNight(a.o) - perNight(b.o)))
        .map(x => x.o)
        .slice(0, 6);
    } else {
      // luxury — бюджет не фильтруем вовсе
      pool = [...options]
        .map(o => ({ o, s: scoreLuxury(o) }))
        .sort((a, b) => b.s - a.s || (perNight(a.o) - perNight(b.o)))
        .map(x => x.o)
        .slice(0, 6);
      note = "Luxury mode ignores daily budget.";
    }

    // добавим вычисленные поля для бейджей
    return pool.map(o => {
      const pn = perNight(o);
      const within = dailyBudget == null ? true : pn <= dailyBudget;
      const overPct = dailyBudget == null ? 0 : Math.max(0, (pn / (dailyBudget || 1) - 1) * 100);
      return { ...o, _perNight: Math.round(pn), _withinBudget: within, _overPct: Math.round(overPct), _note: note };
    });
  }, [options, travelStyle, dailyBudget, nights]);

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-1">Stay &amp; Hotels</h5>

        <div className="text-muted small mb-2">
          City: <span className="fw-semibold">{city || "—"}</span>
          {" "}• {datesParsed.start || "—"} → {datesParsed.end || "—"}
          {haveDates ? <> · {nights} night(s)</> : null}
        </div>

        {/* Подсказка по режиму/бюджету */}
        <div className="small text-muted mb-2">
          Mode: <span className="fw-semibold text-capitalize">{travelStyle}</span>
          {dailyBudget != null && <> · Daily budget: <span className="fw-semibold">€{dailyBudget}</span></>}
          <> · Showing top 6</>
        </div>
        {shownOptions[0]?._note && (
          <div className="small text-muted mb-2">{shownOptions[0]._note}</div>
        )}

        {(!haveDates || !city) && (
          <div className="text-muted small mb-0">
            {city ? "Choose dates to see hotel options." : "Choose destination and dates to see hotel options."}
          </div>
        )}

        {meta?.source && (
          <div className="small text-muted mb-2">
            Source: <span className="fw-semibold">{meta.source}</span>
            {Array.isArray(meta.sources_tried) && meta.sources_tried.length > 0 ? (
              <> · tried: {meta.sources_tried.join(", ")}</>
            ) : null}
          </div>
        )}

        {loading && <div className="text-muted small mb-0">Loading…</div>}
        {!loading && err && <div className="text-danger small mb-0">Error: {String(err)}</div>}

        {!loading && !err && canQuery && options.length === 0 && (
          <p className="text-muted small mb-0">
            No hotel options for {city} ({datesParsed.start} → {datesParsed.end}).
          </p>
        )}

        {!loading && !err && shownOptions.length > 0 && (
          <div className="row g-3 mt-2">
            {shownOptions.map((o, i) => {
              const total = o.price?.amount ?? null;
              const curr = o.price?.currency || "EUR";
              const perNightPrice = o._perNight ?? (total != null ? Math.round(total / Math.max(1, nights)) : null);
              const hasGeo = o.geo?.lat && o.geo?.lon;

              return (
                <div key={o.hotel_id || `${o.name || "Hotel"}-${i}`} className="col-12 col-sm-6 col-md-4 hotel-col">
                  <div className="border rounded-3 p-2 h-100 hotel-card">
                    {/* верх: название + рейтинг + МАЛЕНЬКАЯ цена за ночь */}
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="fw-semibold hotel-name">{o.name || "Hotel"}</div>
                      <div className="text-end">
                        <div className="small text-muted">
                          {perNightPrice != null ? `≈ ${perNightPrice} ${curr} / night` : "—"}
                        </div>
                        <div className="ms-2 text-nowrap"><RatingView rating={o.rating} /></div>
                      </div>
                    </div>

                    {/* бюджетная метка */}
                    {dailyBudget != null && (
                      <div className="mt-1">
                        {o._withinBudget ? (
                          <span className="badge text-bg-success">Within budget</span>
                        ) : (
                          <span className="badge text-bg-warning">
                            +{o._overPct}% over budget
                          </span>
                        )}
                      </div>
                    )}

                    <div className="small text-muted mt-1">
                      {o.address || "—"}
                      {o.distance?.value != null ? <> · {o.distance.value} {o.distance.unit || "KM"}</> : null}
                    </div>

                    {/* низ: БОЛЬШАЯ TOTAL */}
                    <div className="mt-2">
                      <div className="fs-5 fw-bold hotel-total">
                        {total != null ? `${total} ${curr}` : "—"}
                        <span className="fw-normal text-muted ms-2">total</span>
                      </div>
                      {o.board_type ? (
                        <div className="small text-muted mt-1">Board: {o.board_type}</div>
                      ) : null}
                    </div>

                    <div className="mt-2 d-flex gap-2">
                      <a
                        className="small"
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                          (o.name || "Hotel") + " " + (o.address || city || "")
                        )}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open in Maps
                      </a>
                      {hasGeo && (
                        <span className="badge text-bg-light ms-auto">
                          {Number(o.geo.lat).toFixed(3)}, {Number(o.geo.lon).toFixed(3)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card.Body>
    </Card>
  );
}
