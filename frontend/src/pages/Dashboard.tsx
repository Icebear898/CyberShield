import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Grid, Paper, Card, CardContent, 
  LinearProgress, Chip, List, ListItem, ListItemText,
  ListItemIcon, Divider, CircularProgress, Alert, ListItemButton, ListItemAvatar, Avatar, Button
} from '@mui/material';
import { 
  TrendingUp, Warning, Block, Report,
  Person, Message, Shield, Analytics
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface DashboardStats {
  overview: {
    total_users: number;
    total_messages: number;
    total_reports: number;
    total_blocked_users: number;
    abusive_messages: number;
    abusive_percentage: number;
  };
  recent_activity: {
    messages_24h: number;
    reports_24h: number;
    blocks_24h: number;
  };
  alerts: {
    high_severity_reports: number;
    pending_reports: number;
    escalated_reports: number;
  };
  activity_timeline: Array<{
    type: string;
    timestamp: string;
    description: string;
    severity: string;
  }>;
}

interface RecentActivity {
  id: number;
  type: 'message' | 'block' | 'report' | 'alert';
  description: string;
  timestamp: string;
  related_user_id?: number;
  related_user_name?: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await axios.get('/api/dashboard/stats');
        setStats(response.data);
        setRecentActivity(response.data.activity_timeline || []);
        
        // Simulated recent activity
        const activityData: RecentActivity[] = [
          {
            id: 1,
            type: 'alert',
            description: 'Abusive content detected from user JohnDoe',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            related_user_id: 2,
            related_user_name: 'John Doe'
          },
          {
            id: 2,
            type: 'block',
            description: 'User MaliciousUser was automatically blocked due to repeated abuse',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            related_user_id: 3,
            related_user_name: 'Malicious User'
          },
          {
            id: 3,
            type: 'report',
            description: 'Report generated for abusive messages from TrollAccount',
            timestamp: new Date(Date.now() - 172800000).toISOString(),
            related_user_id: 4,
            related_user_name: 'Troll Account'
          },
          {
            id: 4,
            type: 'message',
            description: 'New conversation started with SarahJones',
            timestamp: new Date(Date.now() - 259200000).toISOString(),
            related_user_id: 5,
            related_user_name: 'Sarah Jones'
          }
        ];
        
        setRecentActivity(activityData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'message':
        return <Message sx={{ color: 'primary.main' }} />;
      case 'block':
        return <Block sx={{ color: 'error.main' }} />;
      case 'report':
        return <Report sx={{ color: 'warning.main' }} />;
      case 'alert':
        return <Warning sx={{ color: 'orange' }} />;
      default:
        return <Person />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const navigateToChat = (userId: number | undefined) => {
    if (userId) {
      navigate(`/chat/${userId}`);
    }
  };

  const navigateToReports = () => {
    navigate('/reports');
  };

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Welcome back, {user?.full_name}! Here's your CyberShield overview.
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)'
          },
          gap: 3,
          mb: 4
        }}
      >
        <Card 
          elevation={2} 
          sx={{ 
            borderRadius: 2,
            height: '100%',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'translateY(-5px)',
            }
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Message sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h6" component="div">
                Messages
              </Typography>
            </Box>
            <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
              {stats?.overview.total_messages}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total messages exchanged
            </Typography>
          </CardContent>
        </Card>
        
        <Card 
          elevation={2} 
          sx={{ 
            borderRadius: 2,
            height: '100%',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'translateY(-5px)',
            }
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Warning sx={{ color: 'orange', mr: 1 }} />
              <Typography variant="h6" component="div">
                Alerts
              </Typography>
            </Box>
            <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
              {stats?.alerts.high_severity_reports}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Abuse alerts triggered
            </Typography>
          </CardContent>
        </Card>
        
        <Card 
          elevation={2} 
          sx={{ 
            borderRadius: 2,
            height: '100%',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'translateY(-5px)',
            }
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Block sx={{ color: 'error.main', mr: 1 }} />
              <Typography variant="h6" component="div">
                Blocked
              </Typography>
            </Box>
            <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
              {stats?.overview.total_blocked_users}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Users blocked for abuse
            </Typography>
          </CardContent>
        </Card>
        
        <Card 
          elevation={2} 
          sx={{ 
            borderRadius: 2,
            height: '100%',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'translateY(-5px)',
            }
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Report sx={{ color: 'warning.main', mr: 1 }} />
              <Typography variant="h6" component="div">
                Reports
              </Typography>
            </Box>
            <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
              {stats?.overview.total_reports}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Evidence reports generated
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Recent Alerts */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: '2fr 1fr'
          },
          gap: 3
        }}
      >
        <Paper 
          elevation={2} 
          sx={{ 
            p: 3, 
            borderRadius: 2,
            height: '100%'
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" component="h2">
              Recent Activity
            </Typography>
            <Button 
              variant="outlined" 
              color="primary" 
              size="small"
              onClick={navigateToReports}
            >
              View All Reports
            </Button>
          </Box>
          <List>
            {recentActivity.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                No recent activity to display.
              </Typography>
            ) : (
              recentActivity.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem 
                    alignItems="flex-start"
                    component="div"
                    onClick={() => navigateToChat(activity.related_user_id)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <ListItemAvatar>
                      <Avatar>
                        {getActivityIcon(activity.type)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={activity.description}
                      secondary={formatDate(activity.timestamp)}
                    />
                  </ListItem>
                  {index < recentActivity.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))
            )}
          </List>
        </Paper>
        
        <Paper 
          elevation={2} 
          sx={{ 
            p: 3, 
            borderRadius: 2,
            height: '100%'
          }}
        >
          <Typography variant="h5" component="h2" gutterBottom>
            Safety Tips
          </Typography>
          <List>
            <ListItem>
              <ListItemText 
                primary="Set Your Comfort Level" 
                secondary="Adjust your sensitivity settings based on your comfort level with different types of content."
              />
            </ListItem>
            <Divider component="li" />
            <ListItem>
              <ListItemText 
                primary="Review Reports Regularly" 
                secondary="Check your generated reports to keep track of any patterns of harassment."
              />
            </ListItem>
            <Divider component="li" />
            <ListItem>
              <ListItemText 
                primary="Save Evidence" 
                secondary="Download evidence reports for serious cases of harassment to share with authorities if needed."
              />
            </ListItem>
            <Divider component="li" />
            <ListItem>
              <ListItemText 
                primary="Update Blocked List" 
                secondary="Regularly review your blocked users list and adjust as needed."
              />
            </ListItem>
          </List>
        </Paper>
      </Box>
    </Layout>
  );
};

export default Dashboard;