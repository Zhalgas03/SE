import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './ChatPanel.css';
import { useTrip } from '../context/TripContext';

const STORAGE_KEY = 'plannerChatMessages';
const INITIAL_MESSAGES = [
  {
    id:1,
    role: 'assistant',
    content: "\u{1F44B} Hello! I'm your smart travel planner. Let's start step-by-step!\nWhere would you like to go?"
  }
];

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

  const parsed = {
    destination: destinationMatch?.[1]?.trim() || null,
    travel_dates: datesMatch?.[1]?.trim() || null,
    activities: activityMatch?.[1]?.trim() || null,
    style: styleMatch?.[1]?.trim() || null,
    budget: budgetMatch?.[1]?.trim() || null,
    group: groupMatch?.[1]?.trim() || null,
    origin: originMatch?.[1]?.trim() || null,
    overview: overviewMatch?.[1]?.trim() || "",
    highlights: highlights,
    itinerary_intro: null,
    itinerary: itinerary,
    transfers: transferMatch?.[1]?.trim()
      ? [{ route: "Return Trip", details: transferMatch[1].trim() }]
      : []
  };

  return parsed;
}


  

export default function ChatPanel() {
  const {updateTripSummary } = useTrip();
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
      id: Date.now() + Math.random(), // уникальный ключ
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
        console.log("📦 Parsed summary:", parsed);
        updateTripSummary(parsed);
      }
      
  
      const assistantMessage = {
        id: Date.now() + Math.random(), // тоже уникальный ключ
        role: 'assistant',
        content: reply
      };
  
      setMessages([...newMessages, assistantMessage]);
  
      // Попытка распарсить JSON
      const jsonStart = reply.indexOf('{');
      const jsonEnd = reply.lastIndexOf('}');
      if (jsonStart !== -1 && jsonEnd !== -1 && jsonEnd > jsonStart) {
        const jsonText = reply.slice(jsonStart, jsonEnd + 1);
        try {
          const parsed = JSON.parse(jsonText);
          updateTripSummary(parsed);
        } catch (e) {
          console.warn("⚠️ Could not parse trip summary JSON:", e);
        }
      }
  
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
