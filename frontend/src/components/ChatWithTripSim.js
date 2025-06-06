import React, { useState } from 'react';
import TripVisualizer from './TripVisualizer';

const sampleItinerary = [
  { day:1, title:"Arrival in Almaty", activity:"Explore Almaty, enjoy local food", hotel:"Almaty Comfort Hostel", weather:"☀️ Sunny, 22°C" },
  { day:2, title:"Local Market & Museums", activity:"Visit Green Market and museums", hotel:"Hotel Kazakhstan", weather:"⛅ Partly cloudy, 20°C" },
  { day:3, title:"Mountain Adventure", activity:"Hiking in the Tian Shan mountains", hotel:"Mountain Eco Lodge", weather:"🌄 Clear, 18°C" }
];

export default function ChatWithTripSim() {
  const [messages, setMessages] = useState([
    { id:1, from:'bot', text:"👋 Hello! I'm your smart travel planner. Let's start step-by-step! Where would you like to go?" }
  ]);
  const [itinerary, setItinerary] = useState([]);

  const sendMessage = text => {
    setMessages(m => [...m, { id:m.length+1, from:'user', text }]);
    setTimeout(() => {
      const l = text.toLowerCase();
      if (l.includes('almaty')) {
        setMessages(m => [...m, { id:m.length+1, from:'bot', text:"Great! When are you planning to travel?" }]);
      } else if (l.match(/june|july|august/)) {
        setMessages(m => [...m, { id:m.length+1, from:'bot', text:"What do you want to do there?" }]);
      } else if (l.includes('explore')) {
        setMessages(m => [...m, { id:m.length+1, from:'bot', text:"Noted. Your itinerary is ready!" }]);
        setItinerary(sampleItinerary);
      } else {
        setMessages(m => [...m, { id:m.length+1, from:'bot', text:"Please specify your destination city." }]);
      }
    }, 800);
  };

  return (
    <div style={{ display:'flex', gap:20 }}>
      <div style={{ flex:1, border:'1px solid #ccc', borderRadius:8, padding:12, maxHeight:600, overflowY:'auto' }}>
        {messages.map(m => (
          <div key={m.id} style={{ textAlign: m.from==='bot'?'left':'right', margin:'8px 0' }}>
            <b>{m.from==='bot'?'Bot':'You'}:</b> {m.text}
          </div>
        ))}
        <SendMessageForm onSend={sendMessage}/>
      </div>
      <div style={{ flex:1 }}>
        <TripVisualizer itinerary={itinerary} />
      </div>
    </div>
  );
}

function SendMessageForm({ onSend }) {
  const [input, setInput] = useState('');
  const handle = e => { e.preventDefault(); if(!input.trim())return; onSend(input); setInput(''); };
  return (
    <form onSubmit={handle} style={{ marginTop:12, display:'flex', gap:8 }}>
      <input value={input} onChange={e=>setInput(e.target.value)} placeholder="Type your message..." style={{ flex:1, padding:8 }}/>
      <button type="submit" style={{ padding:'8px 12px' }}>Send</button>
    </form>
  );
}
