// frontend/src/pages/PlannerPage.jsx
import React from 'react';
import ChatPanel from '../components/ChatPanel';
import TripVisualizer from '../components/TripVisualizer';

function PlannerPage() {
  return (
    <div className="d-flex main-content">
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
