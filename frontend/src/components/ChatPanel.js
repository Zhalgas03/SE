// frontend/src/components/ChatPanel.jsx
import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const STORAGE_KEY = 'plannerChatMessages';
const INITIAL_MESSAGES = [
  {
    role: 'assistant',
    content: "👋 Hello! I'm your smart travel planner. Let's start step-by-step!\nWhere would you like to go?"
  }
];

export default function ChatPanel() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : INITIAL_MESSAGES;
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const last = messages[messages.length - 1];
    if (!last || last.role !== 'assistant') return;

    const triggers = ["trip summary", "here is your travel plan", "enjoy your relaxed business trip", "detailed travel plan", "full itinerary"];
    const contentLower = last.content.toLowerCase();
    const matched = triggers.some(trigger => contentLower.includes(trigger));

    if (matched) {
      try {
        const parsed = extractTripFromReply(last.content);
        saveTripToDB(parsed);
      } catch (e) {
        console.error("❌ Failed to parse/save trip:", e);
      }
    }
  }, [messages]);

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
    const newMessages = [...messages, { role: 'user', content: input.trim() }];
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

      const extractSuggestions = (text) => {
        const hintPatterns = [
          /e\.g\.,?\s*((\*\*[^*]+\*\*,?\s*)+)/i,
          /Suggestions?:\s*((\*\*[^*]+\*\*,?\s*)+)/i,
          /consider:\s*((\*\*[^*]+\*\*,?\s*)+)/i,
          /popular (?:cities|options):\s*((\*\*[^*]+\*\*,?\s*)+)/i
        ];
        for (let pattern of hintPatterns) {
          const match = text.match(pattern);
          if (match) {
            return [...match[1].matchAll(/\*\*([^*]+)\*\*/g)].map(m => m[1]);
          }
        }
        return [];
      };

      const suggestedItems = extractSuggestions(reply);
      setSuggestions(suggestedItems.length > 0 ? suggestedItems : []);
      setMessages([...newMessages, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error(err);
      setMessages([...newMessages, { role: 'assistant', content: '❌ Error: could not get reply.' }]);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };


const extractTripFromReply = (text) => {
  const clean = text.replace(/\*\*/g, '');

  const nameMatch = clean.match(/Destination:\s*([^\n]+)/i);

  // Гибкий поиск даты
  const iso = clean.match(/(\d{4}-\d{2}-\d{2})\s*to\s*(\d{4}-\d{2}-\d{2})/);
  const textual = clean.match(/(\d{1,2} \w+|\w+ \d{1,2})\s*to\s*(\d{1,2} \w+|\w+ \d{1,2})/);

  let start = null, end = null;

  if (iso) {
    [start, end] = iso.slice(1, 3);
  } else if (textual) {
    [start, end] = textual.slice(1, 3).map(formatDateSmart);
  }

  const name = nameMatch ? `Trip to ${nameMatch[1].trim()}` : 'Untitled Trip';

  console.log("📋 Parsed Trip:", { name, date_start: start, date_end: end });

  return { name, date_start: start, date_end: end };
};





  const formatDateSmart = (str) => {
  const months = {
    January: '01', February: '02', March: '03', April: '04', May: '05', June: '06',
    July: '07', August: '08', September: '09', October: '10', November: '11', December: '12'
  };

  const parts = str.trim().split(' ');
  if (parts.length !== 2) return null;

  const [a, b] = parts;
  const day = /\d{1,2}/.test(a) ? a : b;
  const month = months[/\d{1,2}/.test(a) ? b : a];

  return `2025-${month}-${day.padStart(2, '0')}`;
};


  const saveTripToDB = async ({ name, date_start, date_end }) => {
  const token = localStorage.getItem("token");
  try {
    const res = await fetch("http://localhost:5001/api/trips", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ name, date_start, date_end })
    });

    const data = await res.json();
    console.log("🛰 Trip create response:", data);

    if (data.success) {
      localStorage.setItem("tripId", data.trip_id);
    } else {
      console.warn("Trip save failed:", data.message);
    }
  } catch (err) {
    console.error("Trip save error:", err);
  }
};



  return (
    <div className="d-flex flex-column h-100 bg-white px-3 py-4">
      <div className="d-flex align-items-center gap-2 mb-3">
        <button className="btn new-chat-btn d-flex align-items-center gap-2" onClick={clearChat} disabled={loading}>
          <i className="bi bi-plus-circle-fill fs-5"></i>
          <span className="fw-medium">New Chat</span>
        </button>
      </div>

      <div className="flex-grow-1 border rounded-4 p-3 bg-white shadow-sm overflow-auto mb-3">
        {messages.map((msg, idx) => (
          <motion.div key={idx} className={`mb-2 d-flex ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            <div className={`p-3 rounded-4 shadow-sm fw-normal fs-6 lh-base ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-light text-dark'}`} style={{ maxWidth: '75%', whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          </motion.div>
        ))}

        <AnimatePresence>
          {loading && (
            <motion.div className="d-flex justify-content-start mb-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="p-3 rounded-4 shadow-sm bg-light text-dark fs-6 d-flex align-items-center" style={{ maxWidth: '75%' }}>
                <div className="typing-loader"><span></span><span></span><span></span></div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={chatEndRef} />
      </div>

      {suggestions.length > 0 && (
        <div className="mb-2 d-flex flex-wrap gap-2">
          {suggestions.map((item, idx) => (
            <button key={idx} className="btn btn-outline-secondary btn-sm" onClick={() => setInput(item)}>{item}</button>
          ))}
        </div>
      )}

      <div className="d-flex align-items-center justify-content-between rounded-4 px-4 py-3 shadow-sm border bg-white" style={{ gap: '1rem' }}>
        <input
          className="form-control border-0 bg-white fs-6"
          type="text"
          placeholder="Type your message here..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading}
          style={{ flexGrow: 1 }}
        />
        <button className="btn btn-primary px-4 py-2 rounded-3" onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>

      <style>{`
        .typing-loader {
          display: flex;
          gap: 6px;
          align-items: center;
        }
        .typing-loader span {
          width: 8px;
          height: 8px;
          background-color: #888;
          border-radius: 50%;
          display: inline-block;
          animation: typing 1s infinite ease-in-out;
        }
        .typing-loader span:nth-child(2) { animation-delay: 0.2s; }
        .typing-loader span:nth-child(3) { animation-delay: 0.4s; }

        .new-chat-btn {
          background-color: #ffffff;
          border: 1px solid #dee2e6;
          border-radius: 12px;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
          padding: 0.5rem 1rem;
          transition: all 0.2s ease;
          font-size: 0.95rem;
        }

        .new-chat-btn:hover {
          background-color: #f8f9fa;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
}
