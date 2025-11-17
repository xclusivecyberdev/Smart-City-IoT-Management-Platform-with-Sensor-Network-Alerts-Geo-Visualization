import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import {
  Sensors,
  Warning,
  CheckCircle,
  Error
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('/api/v1/analytics/dashboard/summary', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) {
    return <Typography>Loading...</Typography>;
  }

  const statCards = [
    {
      title: 'Total Devices',
      value: summary.devices.total,
      icon: <Sensors fontSize="large" />,
      color: '#1976d2'
    },
    {
      title: 'Active Devices',
      value: summary.devices.active,
      icon: <CheckCircle fontSize="large" />,
      color: '#2e7d32'
    },
    {
      title: 'Offline Devices',
      value: summary.devices.offline,
      icon: <Error fontSize="large" />,
      color: '#d32f2f'
    },
    {
      title: 'Active Alerts',
      value: summary.alerts.active,
      icon: <Warning fontSize="large" />,
      color: '#ed6c02'
    }
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Overview
      </Typography>

      <Grid container spacing={3}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4">
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>
                    {card.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Devices by Type
            </Typography>
            <Box sx={{ mt: 2 }}>
              {Object.entries(summary.devices.by_type).map(([type, count]) => (
                <Box key={type} sx={{ mb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip label={type.replace('_', ' ')} size="small" />
                  <Typography variant="body2">{count} devices</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Alert Status
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Active Alerts
                </Typography>
                <Typography variant="h5" color="warning.main">
                  {summary.alerts.active}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Critical Alerts
                </Typography>
                <Typography variant="h5" color="error.main">
                  {summary.alerts.critical}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Typography variant="body2" color="text.secondary">
              All systems operational. Last updated: {new Date().toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
