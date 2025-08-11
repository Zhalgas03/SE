import React, { useEffect, useRef, useState } from "react";
import Map, { Marker, Source, Layer, Popup } from "react-map-gl";
import { motion, AnimatePresence } from "framer-motion";
import "mapbox-gl/dist/mapbox-gl.css";
import "./ChatPanel.css";
import { useTrip } from "../context/TripContext";

const MAPBOX_TOKEN =
  "pk.eyJ1IjoidGFpcmFraGF5ZXYiLCJhIjoiY21kbmg5djRpMXNqaTJrczViaTF0c256dCJ9.RUMP-cv_z2UcpzHq_0IraA";

const STORAGE_KEY = "plannerChatMessages";
const INITIAL_MESSAGES = [
  {
    id: 1,
    role: "assistant",
    content:
      "\u{1F44B} Hello! I'm your smart travel planner. Let's start step-by-step!\nWhere would you like to go?",
  },
];
// --- Парсим itinerary блок ---
function parseItineraryMarkdown(markdown = "") {
  const src = markdown.replace(/\r/g, "");

  // Ловим Day с 0–2 звёздочками и любыми пробелами: **Day 5:**, *Day 5:*, Day 5:
  const dayRe =
    /\*{0,2}\s*Day\s*(\d+)\s*:\s*\*{0,2}\s*([\s\S]*?)(?=(?:\n\s*\*{0,2}\s*Day\s*\d+\s*:\s*\*{0,2})|\n\s*####|\n\s*###|$)/gi;

  // Части дня: допускаем -,–,* в начале строки, 0–2 звёздочки вокруг метки, разные регистры
  // и варианты "All Day"/"Full day"/"Night"
  const partRe =
    /(?:^|\n)\s*[-–*]?\s*\*{0,2}\s*(Morning|Midday|Afternoon|Evening|Full day|All Day|Night)\s*:\s*\*{0,2}\s*([\s\S]*?)(?=(?:\n\s*[-–*]?\s*\*{0,2}\s*(Morning|Midday|Afternoon|Evening|Full day|All Day|Night)\s*:\s*\*{0,2})|$)/gi;

  const days = [];
  let m;
  while ((m = dayRe.exec(src)) !== null) {
    const dayNum = Number(m[1]);
    const body = m[2].trim();

    const parts = [];
    let pm;
    while ((pm = partRe.exec(body)) !== null) {
      parts.push({
        time: pm[1],
        text: pm[2].trim().replace(/\s*\*+$/g, "") // убрать хвостовые ***
      });
    }

    days.push({
      title: `Day ${dayNum}`,
      parts: parts.length
        ? parts
        : [{ time: "All Day", text: body.replace(/\s*\*+$/g, "") }]
    });
  }

  // на всякий случай отсортируем
  days.sort(
    (a, b) => Number(a.title.split(" ")[1]) - Number(b.title.split(" ")[1])
  );
  return days;
}

// --- parseTripSummary: чуть устойчивее граница Itinerary ---
function parseTripSummary(text = "") {
  const t = text.replace(/\r/g, "");

  const destinationMatch = t.match(/\*\*Destination:\*\*\s*(.+)/i);
  const datesMatch = t.match(/\*\*Dates:\*\*\s*(.+)/i);
  const overviewMatch = t.match(/####\s*Overview\s*([\s\S]*?)(?:\n####|$)/i);

  const highlightsMatch = t.match(/####\s*Highlights\s*([\s\S]*?)(?:\n####|$)/i);
  const highlights = highlightsMatch
    ? highlightsMatch[1]
        .split("\n")
        .map((line) => line.replace(/^[-*]\s*/, "").trim())
        .filter(Boolean)
    : [];

  // Берём всё между "#### Itinerary" и следующим заголовком/концом
  const itineraryMatch = t.match(/####\s*Itinerary\s*([\s\S]*?)(?:\n####|$)/i);
  const itinerary = itineraryMatch ? parseItineraryMarkdown(itineraryMatch[1]) : [];

  return {
    destination: destinationMatch?.[1]?.trim() || null,
    travel_dates: datesMatch?.[1]?.trim() || null,
    overview: overviewMatch?.[1]?.trim() || "",
    highlights,
    itinerary
  };
}

// --- Return Trip extractor (берёт текст между "#### Return Trip" и следующим заголовком/концом)
function extractReturnTrip(markdown = "") {
  const t = (markdown || "").replace(/\r/g, "");
  const m = t.match(/####\s*Return\s*Trip\s*([\s\S]*?)(?=\n####|\n###|$)/i);
  if (!m) return null;
  const body = m[1].trim();

  // попытаемся вытащить from/to из первого предложения "from X to Y"
  const dir = body.match(/from\s+(.+?)\s+to\s+(.+?)([.,\n]|$)/i);
  const fromCity = dir?.[1]?.trim() || null;
  const toCity   = dir?.[2]?.trim() || null;

  return {
    raw: body,                     // полный текст секции
    from: fromCity,
    to: toCity
  };
}


// --- ОЧИСТКА текста для геокодинга ---
function cleanPlaceName(raw) {
  return raw
    .replace(/Day\s*\d+:/i, "")
    .replace(/Arrive|Arrival|Check.?in|Evening|Morning|Walk|Relax|Explore|Visit/gi, "")
    .trim()
    .split("including").pop() // берем часть после including если есть
    .split(",")[0]
    .split(".")[0]
    .split("and")[0]
    .trim();
}

// --- Геокодинг с привязкой к городу ---
async function getCoordinatesForPlace(placeName, cityCoord, destinationCity = "") {
  if (!placeName) return null;

  // Очистка текста
  let cleanName = cleanPlaceName(placeName);

  // Формируем запрос
  let query = cleanName;
  if (destinationCity) query += `, ${destinationCity}`;

  // bounding box 50км вокруг города
  const bbox = cityCoord
    ? [
        cityCoord.lng - 0.5,
        cityCoord.lat - 0.5,
        cityCoord.lng + 0.5,
        cityCoord.lat + 0.5,
      ].join(",")
    : null;

  // proximity — приоритет точек вокруг города
  const proximity = cityCoord
    ? `&proximity=${cityCoord.lng},${cityCoord.lat}`
    : "";

  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
    query
  )}.json?access_token=${MAPBOX_TOKEN}${proximity}${
    bbox ? `&bbox=${bbox}` : ""
  }`;

  console.log("Geocoding query:", query);

  const res = await fetch(url);
  const data = await res.json();

  // Фильтрация — ищем город назначения в контексте
  if (data.features && data.features.length > 0) {
    const feature = data.features.find((f) =>
      f.place_name.includes(destinationCity)
    );

    const selected = feature || data.features[0];
    const [lng, lat] = selected.center;
    return { lat, lng, name: cleanName };
  }

  // fallback — если не нашли точку, возвращаем координаты города
  if (cityCoord) {
    return { ...cityCoord, name: cleanName || destinationCity };
  }

  return null;
}

export default function ChatPanel() {
  const { tripSummary, updateTripSummary } = useTrip();
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : INITIAL_MESSAGES;
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  const [viewState, setViewState] = useState({
    latitude: 45.46,
    longitude: 9.18,
    zoom: 12,
  });

  const [popupInfo, setPopupInfo] = useState(null);

  // Обновляем центр карты при изменении координат
  useEffect(() => {
    if (tripSummary?.coordinates?.length > 0) {
      setViewState({
        latitude: tripSummary.coordinates[0].lat,
        longitude: tripSummary.coordinates[0].lng,
        zoom: 12,
      });
    }
  }, [tripSummary?.coordinates]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        150
      )}px`;
    }
  }, [input]);

  const clearChat = async () => {
    try {
      await fetch("http://localhost:5001/api/chat/reset", { method: "POST" });
      localStorage.removeItem(STORAGE_KEY);
      setMessages(INITIAL_MESSAGES);
      setInput("");
    } catch (err) {
      console.error("Failed to reset chat on server:", err);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now() + Math.random(),
      role: "user",
      content: input.trim(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5001/api/perplexity-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input.trim() }),
      });

      const data = await res.json();
      const reply = data.reply;

      const parsed = parseTripSummary(reply);
      // Return Trip -> transfers[]
      const rt = extractReturnTrip(reply);
      if (rt) {
        parsed.transfers = [{
          route: rt.from && rt.to ? `${rt.from} → ${rt.to}` : "Return Trip",
          details: rt.raw
        }];
        // полезно сохранить и для API:
        parsed.returnFrom = rt.from || null;
        parsed.returnTo   = rt.to   || parsed.destination || null;
}

      // --- Геокодинг: получаем координаты города назначения ---
      let cityCoord = null;
      if (parsed?.destination) {
        cityCoord = await getCoordinatesForPlace(parsed.destination);
      }

      let coords = [];

      // 1. Основной город
      if (cityCoord) coords.push(cityCoord);

      // 2. Места из itinerary
if (parsed?.itinerary?.length > 0) {
  for (const item of parsed.itinerary) {
    if (Array.isArray(item.parts)) {
      for (const part of item.parts) {
        const coord = await getCoordinatesForPlace(
          part.text,
          cityCoord,
          parsed.destination
        );
        if (coord) coords.push(coord);
      }
    }
  }
}


      if (coords.length > 0) {
        parsed.coordinates = coords;
      }

      updateTripSummary(parsed);

      const assistantMessage = {
        id: Date.now() + Math.random(),
        role: "assistant",
        content: reply,
      };

      setMessages([...newMessages, assistantMessage]);
    } catch (err) {
      console.error(err);
      setMessages([
        ...newMessages,
        { id: Date.now() + Math.random(), role: "assistant", content: "❌ Error: could not get reply." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const coordinates = tripSummary?.coordinates || [
    { lat: 45.46, lng: 9.18 }, // fallback Milan
  ];

  const routeGeoJSON = {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: coordinates.map((p) => [p.lng, p.lat]),
    },
  };

 return (
    <div className="chat-container">
      {/* New Chat button */}
      <div className="px-1 px-sm-3 py-2 d-flex justify-content-end">
        <button className="chat-btn d-flex align-items-center gap-2" onClick={clearChat} disabled={loading}>
          <span className="icon-circle"><i className="bi bi-plus-lg"></i></span>
          <span className="d-none d-sm-inline">New Chat</span>
        </button>
      </div>

      {/* Chat messages area */}
      <div className="flex-grow-1 overflow-auto chat-wrapper px-1 px-sm-3" style={{ paddingBottom: '0.5rem' }}>
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            className={`d-flex ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'} mb-2`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div
              className={`p-2 px-3 rounded-4 fw-normal fs-6 lh-base shadow-sm ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-white text-dark border'}`}
              style={{ maxWidth: '80%', whiteSpace: 'pre-wrap', wordBreak: 'break-word', borderRadius: '18px' }}
            >
              {msg.content}
            </div>
          </motion.div>
        ))}

        <AnimatePresence>
          {loading && (
            <motion.div className="d-flex justify-content-start mb-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="p-2 px-3 rounded-4 bg-white text-dark fs-6 d-flex align-items-center border" style={{ maxWidth: '75%' }}>
                <div className="typing-loader"><span></span><span></span><span></span></div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={chatEndRef} />
      </div>

      {/* Chat input */}
      <div className="chat-wrapper px-1 px-sm-3">
        <div className="d-flex align-items-end gap-2 p-2 border rounded-4 bg-white shadow-sm">
          <textarea
            ref={textareaRef}
            className="form-control border-0 px-2 py-1"
            placeholder="Type your message here..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => (e.key === 'Enter' && !e.shiftKey ? (e.preventDefault(), handleSend()) : null)}
            rows={1}
            style={{
              resize: 'none',
              fontSize: '16px',
              boxShadow: 'none',
              outline: 'none',
              overflow: 'hidden',
              maxHeight: '150px',
              lineHeight: '1.5',
              flex: 1
            }}
          />
          <button
            className="btn btn-primary rounded-circle"
            style={{ width: '42px', height: '42px' }}
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            <i className="bi bi-send-fill"></i>
          </button>
        </div>
      </div>
    </div>
  );
}
