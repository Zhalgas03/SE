import React from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = "pk.eyJ1IjoidGFpcmFraGF5ZXYiLCJhIjoiY21kbmg5djRpMXNqaTJrczViaTF0c256dCJ9.RUMP-cv_z2UcpzHq_0IraA";

export default function MapPreview({ coordinates }) {
  if (!coordinates || coordinates.length === 0) {
    return (
      <div style={{ width: '100%', height: '300px', textAlign: 'center', paddingTop: '100px' }}>
        No route data yet
      </div>
    );
  }

  const routeGeoJSON = {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: coordinates.map(p => [p.lng, p.lat]) // [lng, lat]
    }
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <Map
        initialViewState={{
          latitude: coordinates[0].lat,
          longitude: coordinates[0].lng,
          zoom: 12
        }}
        style={{ width: '100%', height: '300px' }}
        mapStyle="mapbox://styles/mapbox/streets-v11"
        mapboxAccessToken={MAPBOX_TOKEN}
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
      </Map>
    </div>
  );
}
