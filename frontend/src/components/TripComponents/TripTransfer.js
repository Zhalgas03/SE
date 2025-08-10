import React, { useEffect, useMemo, useState } from 'react';
import { Card } from 'react-bootstrap';

// --- извлекаем from/to из текста (стрелка/фразы) ---
function extractFromToFromText(text = '') {
  const t = (text || '').replace(/\s+/g, ' ').trim();

  // 1) "A → B" / "A -> B"
  let m = t.match(/([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s*(?:→|->)\s*([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+)/);
  if (m) return { from: m[1].trim().replace(/,$/, ''), to: m[2].trim().replace(/,$/, '') };

  // 2) "from A to B"
  m = t.match(/\bfrom\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s+to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)([.,]|$)/i);
  if (m) return { from: m[1].trim(), to: m[2].trim() };

  // 3) "to B from A" / "back to B from A"
  m = t.match(/\b(?:back\s+)?to\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)\s+from\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-\s]+?)([.,]|$)/i);
  if (m) return { from: m[2].trim(), to: m[1].trim() };

  return { from: null, to: null };
}

// --- получаем город из станции/аэропорта/адреса ---
function toCityName(place = '') {
  if (!place) return null;
  let s = place;

  // обрезаем содержимое в скобках: "Rome (Fiumicino)" → "Rome"
  s = s.replace(/\(.*?\)/g, ' ');

  // если есть разделители типа " - " или "/" — берём левую часть
  s = s.split(' / ')[0].split(' - ')[0];

  // убираем типовые хвосты
  const stopWords = [
    'central', 'centrale', 'station', 'gare', 'gare de', 'airport', 'aeroporto',
    'aeropuerto', 'bahnhof', 'hbf', 'stazione', 'railway', 'bus station', 'terminal'
  ];
  // отрезаем после запятой (часто "City, Country")
  s = s.split(',')[0];

  // если строка как "Paris Gare de Lyon" → оставим первое слово (город)
  // но для двухсловных городов (Rio de Janeiro, Los Angeles) сохраним пары
  const multiWordCities = [
    'rio de janeiro','los angeles','new york','são paulo','san francisco','kuala lumpur',
    'hong kong','abu dhabi','ho chi minh','las vegas','mexico city','cape town'
  ];

  const raw = s.trim().replace(/\s+/g, ' ');
  const lower = raw.toLowerCase();

  if (multiWordCities.some(c => lower.startsWith(c))) {
    const match = multiWordCities.find(c => lower.startsWith(c));
    return match
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  // общее правило: берём первое слово как город
  let city = raw.split(' ')[0];

  // если первое слово — стоп‑слово (редко), вернём исходное raw
  if (stopWords.includes(city.toLowerCase())) city = raw;

  // подчистим пунктуацию
  city = city.replace(/[.;:]+$/g, '');
  return city || null;
}

function TripTransfer({ summary }) {
  const transfers = Array.isArray(summary?.transfers) ? summary.transfers : [];

  // 1) сначала — явные поля, если ты их прокинул из ChatPanel
  let fullFrom = summary?.returnFrom || null;
  let fullTo   = summary?.returnTo   || null;

  // 2) иначе парсим из route "A → B"
  if ((!fullFrom || !fullTo) && transfers[0]?.route) {
    const { from, to } = extractFromToFromText(transfers[0].route);
    fullFrom = fullFrom || from;
    fullTo   = fullTo   || to;
  }

  // 3) иначе из подробностей
  if ((!fullFrom || !fullTo) && transfers[0]?.details) {
    const { from, to } = extractFromToFromText(transfers[0].details);
    fullFrom = fullFrom || from;
    fullTo   = fullTo   || to;
  }

  // что показываем пользователю (полные названия)
  const displayFrom = fullFrom || '—';
  const displayTo   = fullTo   || '—';

  // что отправляем в API (города)
  const fromCity = toCityName(fullFrom) || null;
  const toCity   = toCityName(fullTo)   || summary?.destination || null;

  // дата
  const travelDate = useMemo(() => {
    if (!summary?.travel_dates) return null;
    if (typeof summary.travel_dates === 'string') {
      const m = summary.travel_dates.match(/\d{4}-\d{2}-\d{2}/);
      return m ? m[0] : null;
    }
    return summary.travel_dates.end || summary.travel_dates.start || null;
  }, [summary?.travel_dates]);

  // API state
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!fromCity || !toCity) return;
    const controller = new AbortController();

    (async () => {
      try {
        setLoading(true);
        const qs = new URLSearchParams({
          from: fromCity,
          to: toCity,
          ...(travelDate ? { date: travelDate } : {}),
        }).toString();

        const res = await fetch(`http://localhost:5001/api/transport?${qs}`, {
          signal: controller.signal,
        });
        const data = await res.json();
        if (data?.success && Array.isArray(data.options)) {
          setOptions(data.options);
        } else {
          setOptions([]);
        }
      } catch (e) {
        if (e.name !== 'AbortError') setOptions([]);
      } finally {
        setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [fromCity, toCity, travelDate]);

  const prettyISO = (iso) => {
    if (!iso?.startsWith('PT')) return iso || '';
    return iso.replace(/^PT/, '').replace(/H/, 'h ').replace(/M/, 'm').replace(/S/, 's').trim();
  };

  return (
    <Card className="mb-4 shadow-sm">
      <Card.Body>
        <h5 className="fw-bold mb-1">Transfer &amp; Transportation</h5>

        {/* Return Trip текст */}
        {transfers.length > 0 ? (
          transfers.map((tr, i) => (
            <div key={i} className="mb-3">
              <div className="fw-semibold">{tr.route}</div>
              <div className="text-muted small ms-4" style={{ whiteSpace: 'pre-wrap' }}>
                {tr.details}
              </div>
            </div>
          ))
        ) : (
          <p className="text-muted mb-2">No transfer info provided.</p>
        )}

        {/* Короткая шапка направления для понятности */}
        <div className="text-muted small mb-2">
          Direction:&nbsp;<span className="fw-semibold">{displayFrom}</span> → <span className="fw-semibold">{displayTo}</span>
          {travelDate ? <> &nbsp;•&nbsp; {travelDate}</> : null}
        </div>

        {/* Suggested routes */}
        <div className="mt-1">
          <div className="d-flex align-items-center gap-2 mb-2">
            <div className="fw-semibold">Suggested routes</div>
            {loading && <span className="text-muted small">Loading…</span>}
          </div>

          {(!loading && options.length === 0) ? (
            <p className="text-muted small mb-0">
              No options found for {fromCity || '—'} → {toCity || '—'}
              {travelDate ? ` on ${travelDate}` : ''}.
            </p>
          ) : null}

          {options.length > 0 && (
            <div className="d-flex flex-column gap-2">
              {options.map((o, idx) => {
                const prettyDur = prettyISO(o.duration);

                let fallbackUrl = null;
                if (o.mode === 'flight' && !o.booking_url && o.segments?.length) {
                  const first = o.segments[0];
                  const depDate = (first.dep || '').slice(0, 10);
                  if (first.from && first.to && depDate) {
                    const route = `${first.from}${depDate.replace(/-/g, '')}/${first.to}${depDate.replace(/-/g, '')}`;
                    fallbackUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(route)}`;
                  }
                }

                return (
                  <div key={idx} className="border rounded-3 p-2">
                    <div className="d-flex align-items-center gap-2">
                      <span className="badge text-bg-secondary">{o.mode?.toUpperCase?.()}</span>
                      {prettyDur ? <span className="text-muted small">• {prettyDur}</span> : null}
                      {o.price?.amount ? <span className="text-muted small">• {o.price.amount} {o.price.currency}</span> : null}
                      <span className="text-muted small">• {o.provider}</span>
                    </div>

                    {o.segments?.length ? (
                      <div className="small mt-1 ms-1">
                        {o.segments.map((s, j) => (
                          <div key={j}>
                            {s.from} → {s.to}
                            {s.dep ? ` • ${s.dep.slice(0,16).replace('T',' ')}` : ''} 
                            {s.arr ? ` → ${s.arr.slice(0,16).replace('T',' ')}` : ''} 
                            {s.carrier ? ` (${s.carrier})` : ''}
                          </div>
                        ))}
                      </div>
                    ) : null}

                    <div className="mt-1">
                      {o.booking_url ? (
                        <a className="small" href={o.booking_url} target="_blank" rel="noreferrer">Book</a>
                      ) : fallbackUrl ? (
                        <a className="small" href={fallbackUrl} target="_blank" rel="noreferrer">Search on Google Flights</a>
                      ) : null}
                    </div>

                    {o.note ? <div className="text-muted small mt-1">{o.note}</div> : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        
      </Card.Body>
    </Card>
  );
}

export default TripTransfer;
