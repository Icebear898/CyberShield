import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, List, ListItem, ListItemAvatar, ListItemText,
  Avatar, Button, TextField, Dialog, DialogTitle, DialogContent,
  DialogActions, Chip, Tab, Tabs, Badge, Alert, Snackbar,
  IconButton, Divider, Card, CardContent
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Search as SearchIcon,
  People as PeopleIcon,
  PersonRemove as PersonRemoveIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  full_name: string;
  friendship_since?: string;
  can_send_request?: boolean;
}

interface FriendRequest {
  id: number;
  sender?: {
    id: number;
    username: string;
    full_name: string;
  };
  receiver?: {
    id: number;
    username: string;
    full_name: string;
  };
  created_at: string;
  status?: string;
}

interface AlertState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

const Friends: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [friends, setFriends] = useState<User[]>([]);
  const [receivedRequests, setReceivedRequests] = useState<FriendRequest[]>([]);
  const [sentRequests, setSentRequests] = useState<FriendRequest[]>([]);
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [addFriendOpen, setAddFriendOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState<AlertState>({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    fetchFriends();
    fetchReceivedRequests();
    fetchSentRequests();
  }, []);

  const fetchFriends = async () => {
    try {
      const response = await axios.get('/api/friends/list');
      setFriends(response.data);
    } catch (error) {
      console.error('Error fetching friends:', error);
    }
  };

  const fetchReceivedRequests = async () => {
    try {
      const response = await axios.get('/api/friends/requests/received');
      setReceivedRequests(response.data);
    } catch (error) {
      console.error('Error fetching received requests:', error);
    }
  };

  const fetchSentRequests = async () => {
    try {
      const response = await axios.get('/api/friends/requests/sent');
      setSentRequests(response.data);
    } catch (error) {
      console.error('Error fetching sent requests:', error);
    }
  };

  const searchUsers = async () => {
    if (searchQuery.length < 2) {
      setAlert({ open: true, message: 'Search query must be at least 2 characters', severity: 'warning' });
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`/api/friends/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Error searching users:', error);
      setAlert({ open: true, message: 'Error searching users', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const sendFriendRequest = async (userId: number) => {
    try {
      await axios.post('/api/friends/request', { receiver_id: userId });
      setAlert({ open: true, message: 'Friend request sent!', severity: 'success' });
      setSearchResults(prev => prev.filter(u => u.id !== userId));
      fetchSentRequests();
    } catch (error: any) {
      setAlert({ 
        open: true, 
        message: error.response?.data?.detail || 'Error sending friend request', 
        severity: 'error' 
      });
    }
  };

  const respondToRequest = async (requestId: number, action: 'accept' | 'reject') => {
    try {
      await axios.post(`/api/friends/requests/${requestId}/respond`, { action });
      setAlert({ 
        open: true, 
        message: `Friend request ${action}ed!`, 
        severity: 'success' 
      });
      fetchReceivedRequests();
      if (action === 'accept') {
        fetchFriends();
      }
    } catch (error: any) {
      setAlert({ 
        open: true, 
        message: error.response?.data?.detail || 'Error responding to request', 
        severity: 'error' 
      });
    }
  };

  const removeFriend = async (friendId: number) => {
    if (!window.confirm('Are you sure you want to remove this friend?')) {
      return;
    }

    try {
      await axios.delete(`/api/friends/remove/${friendId}`);
      setAlert({ open: true, message: 'Friend removed', severity: 'info' });
      fetchFriends();
    } catch (error: any) {
      setAlert({ 
        open: true, 
        message: error.response?.data?.detail || 'Error removing friend', 
        severity: 'error' 
      });
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  return (
    <Layout>
      <Typography variant="h4" component="h1" gutterBottom>
        Friends
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage your friends and friend requests. Only friends can send messages to each other.
      </Typography>

      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 3 }}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Friends</Typography>
            </Box>
            <Typography variant="h4" color="primary.main">{friends.length}</Typography>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <PersonAddIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6">Pending Requests</Typography>
            </Box>
            <Typography variant="h4" color="warning.main">{receivedRequests.length}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Add Friend Button */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => setAddFriendOpen(true)}
        >
          Add Friend
        </Button>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label={
              <Badge badgeContent={friends.length} color="primary">
                Friends
              </Badge>
            } 
          />
          <Tab 
            label={
              <Badge badgeContent={receivedRequests.length} color="error">
                Requests
              </Badge>
            } 
          />
          <Tab label="Sent Requests" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Paper>
          <List>
            {friends.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No friends yet" 
                  secondary="Add friends to start chatting!" 
                />
              </ListItem>
            ) : (
              friends.map((friend) => (
                <React.Fragment key={friend.id}>
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar>{friend.full_name.charAt(0).toUpperCase()}</Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={friend.full_name}
                      secondary={`@${friend.username} • Friends since ${new Date(friend.friendship_since!).toLocaleDateString()}`}
                    />
                    <IconButton 
                      color="error" 
                      onClick={() => removeFriend(friend.id)}
                      title="Remove friend"
                    >
                      <PersonRemoveIcon />
                    </IconButton>
                  </ListItem>
                  <Divider variant="inset" component="li" />
                </React.Fragment>
              ))
            )}
          </List>
        </Paper>
      )}

      {tabValue === 1 && (
        <Paper>
          <List>
            {receivedRequests.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No pending requests" 
                  secondary="You'll see friend requests here" 
                />
              </ListItem>
            ) : (
              receivedRequests.map((request) => (
                <React.Fragment key={request.id}>
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar>{request.sender!.full_name.charAt(0).toUpperCase()}</Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={request.sender!.full_name}
                      secondary={`@${request.sender!.username} • ${new Date(request.created_at).toLocaleDateString()}`}
                    />
                    <Button
                      variant="contained"
                      color="success"
                      size="small"
                      startIcon={<CheckIcon />}
                      onClick={() => respondToRequest(request.id, 'accept')}
                      sx={{ mr: 1 }}
                    >
                      Accept
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      startIcon={<CloseIcon />}
                      onClick={() => respondToRequest(request.id, 'reject')}
                    >
                      Reject
                    </Button>
                  </ListItem>
                  <Divider variant="inset" component="li" />
                </React.Fragment>
              ))
            )}
          </List>
        </Paper>
      )}

      {tabValue === 2 && (
        <Paper>
          <List>
            {sentRequests.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No sent requests" 
                  secondary="Requests you send will appear here" 
                />
              </ListItem>
            ) : (
              sentRequests.map((request) => (
                <React.Fragment key={request.id}>
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar>{request.receiver!.full_name.charAt(0).toUpperCase()}</Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={request.receiver!.full_name}
                      secondary={`@${request.receiver!.username} • Sent ${new Date(request.created_at).toLocaleDateString()}`}
                    />
                    <Chip label="Pending" color="warning" size="small" />
                  </ListItem>
                  <Divider variant="inset" component="li" />
                </React.Fragment>
              ))
            )}
          </List>
        </Paper>
      )}

      {/* Add Friend Dialog */}
      <Dialog open={addFriendOpen} onClose={() => setAddFriendOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Friend</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              fullWidth
              placeholder="Search by username or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchUsers()}
            />
            <Button 
              variant="contained" 
              onClick={searchUsers}
              disabled={loading}
              startIcon={<SearchIcon />}
            >
              Search
            </Button>
          </Box>

          <List>
            {searchResults.map((user) => (
              <ListItem key={user.id}>
                <ListItemAvatar>
                  <Avatar>{user.full_name.charAt(0).toUpperCase()}</Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={user.full_name}
                  secondary={`@${user.username}`}
                />
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<PersonAddIcon />}
                  onClick={() => sendFriendRequest(user.id)}
                >
                  Add Friend
                </Button>
              </ListItem>
            ))}
          </List>

          {searchQuery && searchResults.length === 0 && !loading && (
            <Typography color="text.secondary" align="center" sx={{ py: 2 }}>
              No users found
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddFriendOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Alert Snackbar */}
      <Snackbar
        open={alert.open}
        autoHideDuration={4000}
        onClose={handleCloseAlert}
      >
        <Alert onClose={handleCloseAlert} severity={alert.severity}>
          {alert.message}
        </Alert>
      </Snackbar>
    </Layout>
  );
};

export default Friends;
