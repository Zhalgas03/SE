import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './ChatPanel.css';
import { useTrip } from '../context/TripContext';

const STORAGE_KEY = 'plannerChatMessages';
const MAPBOX_TOKEN = "pk.eyJ1IjoidGFpcmFraGF5ZXYiLCJhIjoiY21kbmg5djRpMXNqaTJrczViaTF0c256dCJ9.RUMP-cv_z2UcpzHq_0IraA";
const INITIAL_MESSAGES = [
  {
    id: 1,
    role: 'assistant',
    content: "\u{1F44B} Hello! I'm your smart travel planner. Let's start step-by-step!\nWhere would you like to go?"
  }
];

// Функция для расчёта расстояния между координатами (в км)
function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (x) => (x * Math.PI) / 180;
  const R = 6371; // радиус Земли в км

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Очистка названий мест
function cleanPlaceName(description) {
  return description
    .replace(/^Day\s*\d+[:\-]?\s*/i, '')
    .replace(/\b(arrive|arrival|spree|walk|walking|tour|explore|exploring|visit|final|relaxed|shopping|shops?|boutiques?|focused|day|begin|local|cafes?|stores?|nearby|any missed sites|ventures|district)\b/gi, '')
    .replace(/\b(in|on|to|of|for|with|around|and|along)\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Получение координат города
async function geocodeCity(destination) {
  const response = await fetch(
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(destination)}.json?` +
    `access_token=${MAPBOX_TOKEN}&limit=1&types=place`
  );
  const data = await response.json();

  if (data.features && data.features.length > 0) {
    const f = data.features[0];
    return { lat: f.center[1], lng: f.center[0] };
  }
  // fallback на центр Европы
  return { lat: 50.1109, lng: 8.6821 };
}

// Геокодинг точек маршрута
async function geocodePlaces(places, destination = "") {
  const cityCoords = await geocodeCity(destination);
  const results = [];

  for (const place of places) {
    try {
      const query = `${cleanPlaceName(place)} ${destination}`.trim();
      console.log("Geocoding with Mapbox:", query);

      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?` +
        `access_token=${MAPBOX_TOKEN}&limit=1&types=poi,place,neighborhood`
      );

      const data = await response.json();

      if (data.features && data.features.length > 0) {
        const f = data.features[0];
        const lat = f.center[1];
        const lng = f.center[0];

        // Проверяем — точка в пределах 50 км
        const distance = haversineDistance(cityCoords.lat, cityCoords.lng, lat, lng);
        if (distance <= 50) {
          results.push({ name: place, lat, lng, isFallback: false });
        } else {
          results.push({ name: place, ...cityCoords, isFallback: true });
        }
      } else {
        results.push({ name: place, ...cityCoords, isFallback: true });
      }
    } catch (err) {
      console.error(`Geocoding failed for: ${place}`, err);
      results.push({ name: place, ...cityCoords, isFallback: true });
    }
  }

  return results;
}

// Парсер ответа AI
function parseTripSummary(text) {
  const destinationMatch = text.match(/\*\*Destination:\*\*\s*(.+)/i);
  const datesMatch = text.match(/\*\*Dates:\*\*\s*(.+)/i);
  const activityMatch = text.match(/\*\*Activity:\*\*\s*(.+)/i);
  const styleMatch = text.match(/\*\*Travel Style:\*\*\s*(.+)/i);
  const budgetMatch = text.match(/\*\*Budget:\*\*\s*(.+)/i);
  const groupMatch = text.match(/\*\*Travel Group:\*\*\s*(.+)/i);
  const originMatch = text.match(/\*\*Departure City:\*\*\s*(.+)/i);

  const overviewMatch = text.match(/#### Overview\s*([\s\S]*?)####/i);
  const highlightsMatch = text.match(/#### Highlights\s*([\s\S]*?)####/i);
  const itineraryMatch = text.match(/#### Itinerary\s*([\s\S]*?)####/i);
  const transferMatch = text.match(/#### Return Trip\s*([\s\S]*?)$/i);

  const highlights = highlightsMatch
    ? highlightsMatch[1].split(/[-*]\s+/).filter(Boolean).map(h => h.trim())
    : [];

  const itineraryLines = itineraryMatch
    ? itineraryMatch[1].split(/[-*]\s+/).filter(Boolean)
    : [];

  const itinerary = itineraryLines.map((line, i) => ({
    title: `Day ${i + 1}`,
    description: line.trim()
  }));

  return {
    destination: destinationMatch?.[1]?.trim() || null,
    travel_dates: datesMatch?.[1]?.trim() || null,
    activities: activityMatch?.[1]?.trim() || null,
    style: styleMatch?.[1]?.trim() || null,
    budget: budgetMatch?.[1]?.trim() || null,
    group: groupMatch?.[1]?.trim() || null,
    origin: originMatch?.[1]?.trim() || null,
    overview: overviewMatch?.[1]?.trim() || "",
    highlights,
    itinerary_intro: null,
    itinerary,
    transfers: transferMatch?.[1]?.trim()
      ? [{ route: "Return Trip", details: transferMatch[1].trim() }]
      : [],
    placesForGeocoding: itinerary.map(item => item.description)
  };
}

export default function ChatPanel() {
  const { updateTripSummary } = useTrip();
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : INITIAL_MESSAGES;
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const clearChat = async () => {
    try {
      await fetch('http://localhost:5001/api/chat/reset', { method: 'POST' });
      localStorage.removeItem(STORAGE_KEY);
      setMessages(INITIAL_MESSAGES);
      setInput('');
    } catch (err) {
      console.error("Failed to reset chat on server:", err);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now() + Math.random(),
      role: 'user',
      content: input.trim()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:5001/api/perplexity-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.trim() })
      });

      const data = await res.json();
      const reply = data.reply;

      console.log("AI reply:", reply);
      const parsed = parseTripSummary(reply);

      if (parsed?.destination) {
        const geoPoints = await geocodePlaces(parsed.placesForGeocoding, parsed.destination);
        parsed.coordinates = geoPoints;
      
        console.log("📦 Parsed with coordinates:", parsed);
        updateTripSummary(parsed);
      }

      const assistantMessage = {
        id: Date.now() + Math.random(),
        role: 'assistant',
        content: reply
      };

      setMessages([...newMessages, assistantMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage = {
        id: Date.now() + Math.random(),
        role: 'assistant',
        content: '❌ Error: could not get reply.'
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
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