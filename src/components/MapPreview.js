import React, { useState } from 'react';
import ReactMapGL, { Marker, Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = "pk.eyJ1IjoidGFpcmFraGF5ZXYiLCJhIjoiY21kbmg5djRpMXNqaTJrczViaTF0c256dCJ9.RUMP-cv_z2UcpzHq_0IraA";

export default function MapPreview({ coordinates }) {
  // Дефолтные настройки карты
  const [viewport, setViewport] = useState({
    latitude: coordinates && coordinates.length > 0 ? coordinates[0].lat : 45.46,
    longitude: coordinates && coordinates.length > 0 ? coordinates[0].lng : 9.18,
    zoom: 12,
    width: '100%',
    height: '300px'
  });

  if (!coordinates || coordinates.length === 0) {
    return (
      <div style={{ width: '100%', height: '300px', textAlign: 'center', paddingTop: '100px' }}>
        No route data yet
      </div>
    );
  }

  // Формируем маршрут для линии
  const routeGeoJSON = {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: coordinates.map(p => [p.lng, p.lat]) // Mapbox ожидает [lng, lat]
    }
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ReactMapGL
        {...viewport}
        mapStyle="mapbox://styles/mapbox/streets-v11"
        mapboxApiAccessToken={MAPBOX_TOKEN}
        onViewportChange={setViewport}
      >
        {/* Линия маршрута */}
        <Source id="route" type="geojson" data={routeGeoJSON}>
          <Layer
            id="route-line"
            type="line"
            paint={{
              'line-color': '#3b82f6',
              'line-width': 4
            }}
          />
        </Source>

        {/* Маркеры */}
        {coordinates.map((point, i) => (
          <Marker key={i} longitude={point.lng} latitude={point.lat}>
            <div
              style={{
                backgroundColor: 'blue',
                color: 'white',
                borderRadius: '50%',
                width: 24,
                height: 24,
                textAlign: 'center',
                lineHeight: '24px',
                fontSize: 12
              }}
            >
              {i + 1}
            </div>
          </Marker>
        ))}
      </ReactMapGL>
    </div>
  );
}
