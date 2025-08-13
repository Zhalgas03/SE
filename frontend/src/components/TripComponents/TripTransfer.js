// src/components/TripComponents/TripTransfer.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Card } from "react-bootstrap";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5001";

/* ---------------- helpers ---------------- */
function extractFromToFromText(text = "") {
  const t = (text || "").replace(/\s+/g, " ").trim();
  let m = t.match(/([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+?)\s*(?:→|->)\s*([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+)/);
  if (m) return { from: m[1].trim().replace(/,$/, ""), to: m[2].trim().replace(/,$/, "") };
  m = t.match(/\bfrom\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+?)\s+to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+?)([.,]|$)/i);
  if (m) return { from: m[1].trim(), to: m[2].trim() };
  m = t.match(/\b(?:back\s+|return\s+)?to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+?)\s+from\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+?)([.,]|$)/i);
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

function parseDateRangeSmart(dates) {
  if (!dates) return { start: null, end: null };
  if (typeof dates === "object" && (dates.start || dates.end)) {
    return { start: dates.start || null, end: dates.end || null };
  }
  const str = String(dates).trim();
  const mIso = str.match(/(\d{4}-\d{2}-\d{2}).+?(\d{4}-\d{2}-\d{2})/);
  if (mIso) return { start: mIso[1], end: mIso[2] };

  const months = { january:0,february:1,march:2,april:3,may:4,june:5,july:6,august:7,september:8,october:9,november:10,december:11 };
  const clean = str.toLowerCase().replace(/(\d+)(st|nd|rd|th)/g, "$1");
  let m1 = clean.match(/\b(\d{1,2})\s+([a-z]+)\s+to\s+(\d{1,2})\s+([a-z]+)/i);
  let m2 = clean.match(/\b(\d{1,2})\s+to\s+(\d{1,2})\s+([a-z]+)/i);
  const year = new Date().getFullYear();
  const toISO = (d, mon, y=year) => `${y}-${String(mon+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
  if (m1 && months[m1[2]]!=null && months[m1[4]]!=null)
    return { start: toISO(+m1[1], months[m1[2]]), end: toISO(+m1[3], months[m1[4]]) };
  if (m2 && months[m2[3]]!=null)
    return { start: toISO(+m2[1], months[m2[3]]), end: toISO(+m2[2], months[m2[3]]) };
  const m3 = clean.match(/\b(\d{1,2})\s+([a-z]+)\b/);
  if (m3 && months[m3[2]]!=null) {
    const iso = toISO(+m3[1], months[m3[2]]);
    return { start: iso, end: iso };
  }
  return { start: null, end: null };
}

function prettyISO(iso) {
  if (!iso?.startsWith("PT")) return iso || "";
  return iso.replace(/^PT/, "").replace(/H/, "h ").replace(/M/, "m").replace(/S/, "s").trim();
}

// markdown “Departure City: …”
function findDepartureInSummary(any) {
  const s = (typeof any === "string" ? any : JSON.stringify(any)) || "";
  const m = s.match(/Departure\s*City[:*]*\s*([A-Za-zÀ-ÖØ-öø-ÿ'’\-.\s]+)/i);
  return m ? toCityName(m[1]) : null;
}

/* --- airline visuals --- */
function carrierFromSegment(seg) {
  // "VY 6253" -> "VY"
  const raw = (seg?.carrier || "").trim();
  const code = raw.split(/\s+/)[0] || "";
  return code.toUpperCase().slice(0, 3);
}
function flightNumberFromSegment(seg) {
  // вернём как есть, например "VY 6253"
  return (seg?.carrier || "").trim();
}
function airlineLogoUrl(iata2) {
  const code = (iata2 || "").toLowerCase();
  return `https://images.kiwi.com/airlines/64/${code}.png`;
}
function airlineName(iata2) {
  const m = {
    VY: "Vueling", IB: "Iberia", FR: "Ryanair", U2: "easyJet", W6: "Wizz Air",
    LH: "Lufthansa", AZ: "ITA Airways", AF: "Air France", KL: "KLM",
    BA: "British Airways", TK: "Turkish Airlines", QR: "Qatar Airways",
    EK: "Emirates", LX: "SWISS", OS: "Austrian", TP: "TAP Air Portugal"
  };
  const k = (iata2 || "").toUpperCase();
  return m[k] || k || "Airline";
}
function AirlineAvatar({ code }) {
  const c = (code || "").toUpperCase();
  const [err, setErr] = useState(false);
  return (
    <div className="d-flex align-items-center" style={{ width: 28, height: 28 }}>
      {!err ? (
        <img
          src={airlineLogoUrl(c)}
          alt={c}
          width={28}
          height={28}
          style={{ borderRadius: 6, objectFit: "contain" }}
          onError={() => setErr(true)}
        />
      ) : (
        <div
          style={{
            width: 28, height: 28, borderRadius: 6,
            background: "#f1f3f5", color: "#2b2f33",
            fontSize: 12, fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "center"
          }}
          title={c}
        >
          {c.slice(0,2)}
        </div>
      )}
    </div>
  );
}

/* ------------- hook: загрузка одного плеча ------------- */
function useTransportLeg(fromCity, toCity, date) {
  const [state, setState] = useState({ loading: false, options: [], error: null });
  useEffect(() => {
    if (!fromCity || !toCity || !date) {
      setState({ loading: false, options: [], error: null });
      return;
    }
    const controller = new AbortController();
    (async () => {
      try {
        setState({ loading: true, options: [], error: null });
        const qs = new URLSearchParams({ from: fromCity, to: toCity, date }).toString();
        const res = await fetch(`${API_BASE}/api/transport?${qs}`, { signal: controller.signal });
        const data = await res.json();
        const ok = data?.success && Array.isArray(data?.options);
        setState({ loading: false, options: ok ? data.options : [], error: ok ? null : "no_data" });
      } catch (e) {
        if (e.name !== "AbortError") setState({ loading: false, options: [], error: String(e) });
      }
    })();
    return () => controller.abort();
  }, [fromCity, toCity, date]);

  return state;
}

/* ---------------- component ---------------- */
export default function TripTransfer({ summary }) {
  const transfers = Array.isArray(summary?.transfers) ? summary.transfers : [];
  const transferText = [transfers[0]?.route, transfers[0]?.details].filter(Boolean).join(" ");
  const parsed = extractFromToFromText(transferText);
  const hasReturnWord = /\b(back|return)\b/i.test(transferText);

  const tripCity = toCityName(summary?.destination || summary?.Destination || parsed.to) || null;

  let departCity =
    toCityName(summary?.departure_city || summary?.departureCity || summary?.from) ||
    findDepartureInSummary(summary) ||
    null;

  if (!departCity && hasReturnWord && tripCity && parsed.from && parsed.to) {
    const fromCity = toCityName(parsed.from);
    const toCity = toCityName(parsed.to);
    if (fromCity && toCity && fromCity.toLowerCase() === tripCity.toLowerCase()) {
      departCity = toCity;
    }
  }
  if (!departCity && parsed.from) departCity = toCityName(parsed.from);

  const ensuredTripCity = tripCity || toCityName(parsed.to) || null;

  const range = useMemo(
    () => parseDateRangeSmart(summary?.travel_dates || summary?.Dates),
    [summary]
  );
  const startDate = range.start || null;
  const endDate = range.end || null;

  const origin = departCity || null;
  const destination = ensuredTripCity || null;

  const outLeg = useTransportLeg(origin, destination, startDate);
  const retLeg = useTransportLeg(destination, origin, endDate);

  /* --- Omio-like option card (flight/car aware) --- */
  function OptionCard({ o }) {
    const isFlight = o.mode === "flight";
    const isCar = o.mode === "car";
    const dur = prettyISO(o.duration);

    const firstSeg = o?.segments?.[0];
    const lastSeg = o?.segments?.[o.segments?.length - 1] || firstSeg;

    const depT = firstSeg?.dep ? firstSeg.dep.slice(11,16) : null;
    const arrT = lastSeg?.arr ? lastSeg.arr.slice(11,16) : null;
    const depD = firstSeg?.dep ? firstSeg.dep.slice(0,10) : null;
    const arrD = lastSeg?.arr ? lastSeg.arr.slice(0,10) : null;

    const stops = (o?.segments?.length || 1) - 1;
    const airlineCode = isFlight ? carrierFromSegment(firstSeg) : null;
    const flightNo = isFlight ? flightNumberFromSegment(firstSeg) : null;

    let fallbackUrl = null;
    if (isFlight && !o.booking_url && firstSeg && lastSeg) {
      const depDate = (firstSeg.dep || "").slice(0, 10);
      if (firstSeg.from && lastSeg.to && depDate) {
        const route = `${firstSeg.from}${depDate.replace(/-/g,"")}/${lastSeg.to}${depDate.replace(/-/g,"")}`;
        fallbackUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(route)}`;
      }
    }

    return (
      <div className="omio-card">
        {/* HEADER: логотип + название авиакомпании + номер рейса */}
        {isFlight && (
          <div className="omio-head">
            <div className="d-flex align-items-center gap-2">
             
              <div className="omio-airline">
                {airlineName(airlineCode)}
              </div>
            </div>
            <div className="omio-operated">
              Flight operated by {flightNo || airlineCode}
            </div>
          </div>
        )}

        {/* BODY */}
        <div className="omio-row">
          <div className="omio-left">
            {isFlight ? (
              <span style={{fontSize:18}}>✈️</span>
            ) : (
              <span style={{ fontSize: 18 }}>🚗</span>
            )}
          </div>

          <div className="omio-mid">
            <div className="omio-times">
              <span className="omio-time">{depT || (isCar ? "—" : "--:--")}</span>
              <span className="omio-dur">— {dur || "—"} —</span>
              <span className="omio-time">{arrT || (isCar ? "—" : "--:--")}</span>
            </div>

            <div className="omio-sub">
              {isFlight ? (
                <>
                  <span>{firstSeg?.from || "—"} • {depD || ""}</span>
                  <span className="mx-2">→</span>
                  <span>{lastSeg?.to || "—"} • {arrD || ""}</span>
                  <span className="omio-badge ms-2">{stops > 0 ? `${stops} transfer(s)` : "Direct"}</span>
                </>
              ) : (
                <>
                  <span>Driving route</span>
                  <span className="mx-2">•</span>
                  <span className="text-muted">{o.note || "Approx. route"}</span>
                </>
              )}
            </div>
          </div>

          <div className="omio-right">
            <div className="omio-price">
              {o.price?.amount != null ? `${o.price.amount} ${o.price.currency}` : (isCar ? "" : "—")}
            </div>

            {isFlight ? (
              o.booking_url || fallbackUrl ? (
                <a className="omio-cta" href={o.booking_url || fallbackUrl} target="_blank" rel="noreferrer">
                  Select
                </a>
              ) : null
            ) : (
              <span className="omio-cta disabled" title="Open Google route in map apps">
                Route
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  const Leg = ({ title, from, to, date, state }) => (
    <>
      <div className="mb-2">
        <span className="fw-semibold">{title}</span>{" "}
        <span className="text-muted small">— {from || "—"} → {to || "—"} {date ? `• ${date}` : ""}</span>
      </div>

      {state.loading && <div className="text-muted small mb-2">Loading…</div>}
      {!state.loading && state.options.length === 0 && (
        <div className="text-muted small mb-3">No options found.</div>
      )}

      {state.options.length > 0 && (
        <div className="d-flex flex-column gap-2 mb-3">
          {state.options.map((o, i) => <OptionCard key={i} o={o} />)}
        </div>
      )}
    </>
  );

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-1">Transfer &amp; Transportation</h5>

        {Array.isArray(transfers) && transfers.length > 0 ? (
          transfers.map((tr, i) => (
            <div key={i} className="mb-3">
              <div className="fw-semibold">{tr.route}</div>
              <div className="text-muted small ms-4" style={{ whiteSpace: "pre-wrap" }}>
                {tr.details}
              </div>
            </div>
          ))
        ) : (
          <p className="text-muted mb-2">No transfer info provided.</p>
        )}

        <Leg title="Outbound" from={origin} to={destination} date={startDate} state={outLeg} />
        <Leg title="Return"   from={destination} to={origin} date={endDate}   state={retLeg} />
      </Card.Body>

      {/* minimal Omio-like styles + header */}
      <style>{`
        .omio-card{
          border:1px solid rgba(0,0,0,.08);
          border-radius:12px;
          background:#fff;
        }
        .omio-head{
          display:flex; align-items:center; justify-content:space-between;
          gap:12px; padding:10px 14px;
          border-bottom:1px solid #eef1f4; background:#fafbfd; border-top-left-radius:12px; border-top-right-radius:12px;
        }
        .omio-airline{ font-weight:700; font-size:14px; }
        .omio-operated{ font-size:12px; color:#6b7280; }

        .omio-row{
          display:flex; align-items:center; gap:12px; padding:12px 14px;
        }
        .omio-left{ width:44px; display:flex; justify-content:center; }
        .omio-mid{ flex:1; min-width:0; }
        .omio-times{ font-weight:700; display:flex; align-items:center; gap:8px; }
        .omio-time{ font-size:16px; }
        .omio-dur{ font-size:12px; color:#6b7280; }
        .omio-sub{ font-size:12px; color:#6b7280; display:flex; align-items:center; gap:6px; margin-top:2px; }
        .omio-badge{ background:#eef2ff; color:#4338ca; border-radius:999px; padding:2px 8px; font-size:11px; }
        .omio-right{ display:flex; flex-direction:column; align-items:flex-end; gap:6px; min-width:120px; }
        .omio-price{ font-size:18px; font-weight:800; }
        .omio-cta{ font-size:12px; font-weight:600; text-decoration:none; border:1px solid #d1d5db; padding:6px 10px; border-radius:8px; }
        .omio-cta:hover{ background:#f9fafb; }
        .omio-cta.disabled{ opacity:.6; pointer-events:none; }
      `}</style>
    </Card>
  );
}
