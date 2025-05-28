import React, { useState } from 'react';
import { sendToDeepSeek } from '../api/deepseek';

function ChatPanel() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const botReply = await sendToDeepSeek(input);
      setMessages((prev) => [...prev, { role: 'assistant', content: botReply }]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: 'assistant', content: "⚠️ Failed to get response from DeepSeek." }]);
    }

    setInput('');
  };

  return (
    <div className="d-flex flex-column h-100">
      <div className="mb-3 border rounded p-3 bg-white shadow-sm overflow-auto" style={{ height: '400px' }}>
        {messages.map((msg, i) => (
          <div key={i} className={`mb-2 ${msg.role === 'user' ? 'text-end' : 'text-start'}`}>
            <span className={`badge bg-${msg.role === 'user' ? 'primary' : 'secondary'}`}>
              {msg.content}
            </span>
          </div>
        ))}
      </div>
      <div className="input-group">
        <input
          className="form-control"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your trip idea..."
        />
        <button className="btn btn-outline-success" onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatPanel;
