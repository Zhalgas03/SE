import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Центрируем по Риму
const center = [41.9028, 12.4964];

// Кастомная иконка (по умолчанию в React-Leaflet может не отображаться)
const customIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function MapPreview() {
  return (
    <div style={{ width: '100%', height: '300px' }}>
      <MapContainer center={center} zoom={13} style={{ width: '100%', height: '100%', borderRadius: '10px' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={center} icon={customIcon}>
          <Popup>Rome Center</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}

export default MapPreview;
