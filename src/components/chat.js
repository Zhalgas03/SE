import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
<<<<<<< HEAD
      const res = await fetch('http://localhost:5001/api/perplexity-chat', {
=======
      const res = await fetch('http://localhost:5000/api/ollama-chat', {
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });

      const data = await res.json();
      setMessages([...newMessages, { role: 'model', content: data.reply }]);
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages([...newMessages, { role: 'model', content: 'Error: could not get reply.' }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
<<<<<<< HEAD
    fetch('http://localhost:5001/api/chat/reset', {
=======
    fetch('http://localhost:5000/api/ollama-reset', {
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    setMessages([{
      role: 'model',
      content: "👋 Hello! I'm your smart travel planner. Let's start step-by-step!\nWhere would you like to go?"
    }]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="d-flex flex-column h-100 bg-white px-3 py-4">
      <div className="flex-grow-1 border rounded-4 p-3 bg-white shadow-sm overflow-auto mb-3">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            className={`mb-2 d-flex ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div
              className={`p-3 rounded-4 shadow-sm fw-normal fs-6 lh-base ${
                msg.role === 'user' ? 'bg-primary text-white' : 'bg-light text-dark'
              }`}
              style={{ maxWidth: '75%', whiteSpace: 'pre-wrap' }}
            >
              {msg.content}
            </div>
          </motion.div>
        ))}
        <AnimatePresence>
          {loading && (
            <motion.div
              className="d-flex justify-content-start mb-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="p-3 rounded-4 shadow-sm bg-light text-dark fs-6 d-flex align-items-center" style={{ maxWidth: '75%' }}>
                <div className="typing-loader">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={chatEndRef} />
      </div>

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
        <button
          className="btn btn-primary px-4 py-2 rounded-3"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>

      {/* Dot animation styles */}
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
        .typing-loader span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-loader span:nth-child(3) {
          animation-delay: 0.4s;
        }
        @keyframes typing {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
          40% { transform: scale(1.2); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default ChatPanel;
