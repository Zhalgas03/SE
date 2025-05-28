// src/pages/PlannerPage.js
import React from 'react';
import ChatPanel from '../components/ChatPanel';
import TripVisualizer from '../components/TripVisualizer';

function PlannerPage() {
  return (
    <div className="container-fluid py-5">
      <div className="row">
        <div className="col-md-4 px-4">
          <ChatPanel />
        </div>
        <div className="col-md-8 px-4">
          <TripVisualizer />
        </div>
      </div>
    </div>
  );
}

export default PlannerPage;
