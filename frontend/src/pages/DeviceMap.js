import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import { Paper, Box, Typography, Chip, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon issue with React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const DeviceMap = () => {
  const [devices, setDevices] = useState([]);
  const [deviceType, setDeviceType] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevicesMap();
  }, [deviceType, status]);

  const fetchDevicesMap = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const params = {};
      if (deviceType) params.device_type = deviceType;
      if (status) params.status = status;

      const response = await axios.get('/api/v1/analytics/devices/map', {
        headers: { Authorization: `Bearer ${token}` },
        params
      });

      setDevices(response.data.features || []);
    } catch (error) {
      console.error('Error fetching devices map:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMarkerColor = (status) => {
    switch (status) {
      case 'active':
        return '#4caf50';
      case 'offline':
        return '#f44336';
      case 'maintenance':
        return '#ff9800';
      default:
        return '#9e9e9e';
    }
  };

  const center = devices.length > 0
    ? [devices[0].geometry.coordinates[1], devices[0].geometry.coordinates[0]]
    : [40.7128, -74.0060]; // Default to New York

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Device Map
      </Typography>

      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Device Type</InputLabel>
          <Select
            value={deviceType}
            label="Device Type"
            onChange={(e) => setDeviceType(e.target.value)}
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="traffic_sensor">Traffic Sensor</MenuItem>
            <MenuItem value="pollution_monitor">Pollution Monitor</MenuItem>
            <MenuItem value="parking_meter">Parking Meter</MenuItem>
            <MenuItem value="water_level_sensor">Water Level Sensor</MenuItem>
            <MenuItem value="garbage_bin_sensor">Garbage Bin Sensor</MenuItem>
            <MenuItem value="energy_meter">Energy Meter</MenuItem>
            <MenuItem value="weather_station">Weather Station</MenuItem>
          </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={status}
            label="Status"
            onChange={(e) => setStatus(e.target.value)}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="offline">Offline</MenuItem>
            <MenuItem value="maintenance">Maintenance</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Paper sx={{ height: 600, overflow: 'hidden' }}>
        {!loading && (
          <MapContainer
            center={center}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {devices.map((device, index) => {
              const { coordinates } = device.geometry;
              const { id, name, device_type, status, zone, battery_level, last_seen } = device.properties;

              return (
                <CircleMarker
                  key={index}
                  center={[coordinates[1], coordinates[0]]}
                  radius={8}
                  fillColor={getMarkerColor(status)}
                  fillOpacity={0.8}
                  color="#fff"
                  weight={2}
                >
                  <Popup>
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ID: {id}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip label={device_type} size="small" sx={{ mr: 1 }} />
                        <Chip label={status} size="small" color={status === 'active' ? 'success' : 'error'} />
                      </Box>
                      {zone && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Zone: {zone}
                        </Typography>
                      )}
                      {battery_level && (
                        <Typography variant="body2">
                          Battery: {battery_level}%
                        </Typography>
                      )}
                      {last_seen && (
                        <Typography variant="body2" color="text.secondary">
                          Last seen: {new Date(last_seen).toLocaleString()}
                        </Typography>
                      )}
                    </Box>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        )}
      </Paper>

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Showing {devices.length} devices on the map
        </Typography>
      </Box>
    </Box>
  );
};

export default DeviceMap;
