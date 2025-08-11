import React, { useState, useEffect } from 'react';
import ChatPanel from '../components/ChatPanel';
import TripVisualizer from '../components/TripVisualizer';

function PlannerPage() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [activeTab, setActiveTab] = useState('chat');

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mobile version
  if (isMobile) {
    return (
      <div className="container-fluid px-3 py-3">
        <div className="btn-group w-100 mb-3" role="group">
          <button
            className={`btn btn-outline-primary ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button
            className={`btn btn-outline-primary ${activeTab === 'trip' ? 'active' : ''}`}
            onClick={() => setActiveTab('trip')}
          >
            Trip
          </button>
        </div>

        <div
          className="border rounded-4 p-2 shadow-sm"
          style={{
            height: '82vh',
            overflowY: 'auto',
            backgroundColor: 'var(--bg-color)',
            color: 'var(--text-color)',
          }}
        >
          {activeTab === 'chat' ? <ChatPanel /> : <TripVisualizer />}
        </div>
      </div>
    );
  }

  // Desktop version
  return (
    <div className="d-flex main-content" style={{ backgroundColor: 'var(--bg-color)', color: 'var(--text-color)' }}>
      <div className="w-50 border-end p-3 overflow-auto">
        <ChatPanel />
      </div>
      <div className="w-50 p-3 overflow-auto">
        <TripVisualizer />
      </div>
    </div>
  );
}

export default PlannerPage;
