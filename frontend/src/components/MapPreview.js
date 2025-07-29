import React, { useMemo, useEffect, useState } from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = "pk.eyJ1IjoidGFpcmFraGF5ZXYiLCJhIjoiY21kbmg5djRpMXNqaTJrczViaTF0c256dCJ9.RUMP-cv_z2UcpzHq_0IraA";

export default function MapPreview({ coordinates }) {
  const validCoords = coordinates?.filter(p => p.lat && p.lng) || [];

  // Центр карты
  const center = useMemo(() => {
    if (validCoords.length === 0) return { lat: 50.1109, lng: 8.6821 };
    const avgLat = validCoords.reduce((sum, p) => sum + p.lat, 0) / validCoords.length;
    const avgLng = validCoords.reduce((sum, p) => sum + p.lng, 0) / validCoords.length;
    return { lat: avgLat, lng: avgLng };
  }, [coordinates]); // пересчитываем только при изменении координат

  const [viewState, setViewState] = useState({
    latitude: center.lat,
    longitude: center.lng,
    zoom: 11
  });

  // Обновляем позицию только если центр реально изменился
  useEffect(() => {
    setViewState(prev => ({
      ...prev,
      latitude: center.lat,
      longitude: center.lng
    }));
  }, [center.lat, center.lng]);

  const routeGeoJSON = useMemo(() => ({
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: validCoords.map(p => [p.lng, p.lat])
    }
  }), [validCoords]);

  if (validCoords.length === 0) {
    return (
      <div style={{ width: '100%', height: '300px', textAlign: 'center', paddingTop: '100px' }}>
        No route data yet
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <Map
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle="mapbox://styles/mapbox/streets-v11"
        mapboxAccessToken={MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
      >
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

        {validCoords.map((point, i) => (
          <Marker key={i} longitude={point.lng} latitude={point.lat} anchor="bottom">
            <div
              style={{
                backgroundColor: '#2563eb',
                color: 'white',
                borderRadius: '50%',
                width: 24,
                height: 24,
                textAlign: 'center',
                lineHeight: '24px',
                fontSize: 12
              }}
              title={point.name}
            >
              {i + 1}
            </div>
          </Marker>
        ))}
      </Map>
    </div>
  );
}
