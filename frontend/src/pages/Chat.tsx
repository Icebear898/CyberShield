import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Box, Typography, Paper, TextField, Button, Avatar, 
  List, ListItem, ListItemAvatar, ListItemText, Divider,
  Alert, Snackbar, IconButton, ListItemButton, Chip, Badge
} from '@mui/material';
import { 
  Send as SendIcon, 
  Person as PersonIcon,
  Circle as OnlineIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  full_name: string;
}

interface Message {
  id: number;
  sender_id: number;
  receiver_id: number;
  content: string;
  created_at: string;
  is_abusive: boolean;
  abuse_score: number;
}

interface AlertState {
  type: 'warning' | 'error' | 'info' | 'success';
  message: string;
  open: boolean;
}

const Chat: React.FC = () => {
  const { userId } = useParams<{ userId?: string }>();
  const { user } = useAuth();
  const { incrementUnread, decrementUnread } = useNotifications();
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [alert, setAlert] = useState<AlertState>({ type: 'info', message: '', open: false });
  const [unreadCounts, setUnreadCounts] = useState<{[userId: number]: number}>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!user || !selectedUser) return;

    // Disconnect existing socket first
    if (socket) {
      socket.close();
      setSocket(null);
    }

    setConnectionStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/ws/${user.id}`);
    
    ws.onopen = () => {
      console.log('WebSocket connection established');
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle different message types
        if (data.type === 'alert') {
          setAlert({
            type: data.severity === 'critical' ? 'error' : 'warning',
            message: data.message,
            open: true
          });
          return;
        }
        
        // Handle regular messages
        if (
          (data.sender_id === selectedUser.id && data.receiver_id === user.id) ||
          (data.sender_id === user.id && data.receiver_id === selectedUser.id)
        ) {
          setMessages(prev => [...prev, data]);
          
          // If message is from another user (not current user), show notification
          if (data.sender_id !== user.id) {
            // Show browser notification if permission granted
            if (Notification.permission === 'granted') {
              const senderName = selectedUser.full_name || selectedUser.username;
              new Notification(`New message from ${senderName}`, {
                body: data.content,
                icon: '/favicon.ico'
              });
            }
            
            // Show in-app alert
            setAlert({
              type: 'info',
              message: `New message from ${selectedUser.full_name || selectedUser.username}`,
              open: true
            });
          }
        } else if (data.sender_id !== user.id) {
          // Message from a different conversation - update unread count
          setUnreadCounts(prev => ({
            ...prev,
            [data.sender_id]: (prev[data.sender_id] || 0) + 1
          }));
          
          // Increment global notification count
          incrementUnread();
          
          // Show notification for message from other users
          if (Notification.permission === 'granted') {
            const senderUser = users.find(u => u.id === data.sender_id);
            const senderName = senderUser?.full_name || senderUser?.username || 'Someone';
            new Notification(`New message from ${senderName}`, {
              body: data.content,
              icon: '/favicon.ico'
            });
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Don't set state here to avoid infinite loops
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket connection closed', event.code, event.reason);
      setConnectionStatus('disconnected');
      
      // Only attempt to reconnect if it wasn't a manual close and we haven't exceeded attempts
      if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        
        console.log(`Scheduling reconnection attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          if (user && selectedUser) { // Check if still valid before reconnecting
            connectWebSocket();
          }
        }, delay);
      }
    };
    
    setSocket(ws);
  }, [user, selectedUser, socket, maxReconnectAttempts]);

  const disconnectWebSocket = useCallback(() => {
    if (socket) {
      socket.close();
      setSocket(null);
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, [socket]);

  // Request notification permission
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Fetch friends list (or all users for admin)
  useEffect(() => {
    const fetchContacts = async () => {
      try {
        let response;
        if (user?.is_admin) {
          // Admin can see all users
          response = await axios.get('/api/users');
          // Filter out current user
          const filteredUsers = response.data.filter((u: User) => u.id !== user?.id);
          setUsers(filteredUsers);
        } else {
          // Regular users can only see friends
          response = await axios.get('/api/friends/list');
          setUsers(response.data);
        }
        
        // If userId is provided in URL, select that user
        if (userId) {
          const userToSelect = response.data.find((u: User) => u.id === parseInt(userId));
          if (userToSelect) {
            setSelectedUser(userToSelect);
          }
        }
      } catch (error) {
        console.error('Error fetching contacts:', error);
      }
    };

    fetchContacts();
  }, [userId, user?.id, user?.is_admin]);

  // Connect to WebSocket when user is selected
  useEffect(() => {
    if (selectedUser && user) {
      // Disconnect existing socket
      disconnectWebSocket();
      
      // Fetch conversation history
      const fetchMessages = async () => {
        try {
          const response = await axios.get(`/api/messages/conversation/${selectedUser.id}`);
          setMessages(response.data);
        } catch (error) {
          console.error('Error fetching messages:', error);
        }
      };
      
      fetchMessages();
      
      // Connect WebSocket after a small delay to ensure cleanup is complete
      const timer = setTimeout(() => {
        connectWebSocket();
      }, 100);
      
      // Cleanup function
      return () => {
        clearTimeout(timer);
        disconnectWebSocket();
      };
    }
  }, [selectedUser?.id, user?.id]); // Only depend on IDs to avoid infinite loops

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleUserSelect = (selectedUser: User) => {
    setSelectedUser(selectedUser);
    
    // Get current unread count for this user
    const currentUnread = unreadCounts[selectedUser.id] || 0;
    
    // Clear unread count for this user
    setUnreadCounts(prev => ({
      ...prev,
      [selectedUser.id]: 0
    }));
    
    // Decrement global notification count by the amount we're clearing
    for (let i = 0; i < currentUnread; i++) {
      decrementUnread();
    }
  };

  const handleSendMessage = () => {
    if (!newMessage.trim() || !selectedUser || !socket || !user) return;
    
    const messageData = {
      id: Date.now(), // Temporary ID until we get the real one from server
      sender_id: user.id,
      receiver_id: selectedUser.id,
      content: newMessage,
      created_at: new Date().toISOString(),
      is_abusive: false,
      abuse_score: 0
    };
    
    // Add message to local state immediately for sender
    setMessages(prev => [...prev, messageData]);
    
    // Send via WebSocket
    socket.send(JSON.stringify({
      sender_id: user.id,
      receiver_id: selectedUser.id,
      content: newMessage
    }));
    
    setNewMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  const formatMessageTime = (timestamp: string | undefined) => {
    if (!timestamp) {
      console.warn('No timestamp provided for message');
      return 'Now';
    }
    
    try {
      // Handle different timestamp formats
      let date: Date;
      
      if (typeof timestamp === 'number') {
        date = new Date(timestamp);
      } else if (typeof timestamp === 'string') {
        // Try parsing as ISO string first, then as regular date string
        date = new Date(timestamp);
        
        // If invalid, try parsing as timestamp number
        if (isNaN(date.getTime()) && !isNaN(Number(timestamp))) {
          date = new Date(Number(timestamp));
        }
      } else {
        console.warn('Invalid timestamp type:', typeof timestamp, timestamp);
        return 'Now';
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid date created from timestamp:', timestamp);
        return 'Now';
      }
      
      const now = new Date();
      
      // If message is from today, show time only
      if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        });
      }
      
      // If message is from yesterday
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday ${date.toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        })}`;
      }
      
      // If message is older, show date and time
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
    } catch (error) {
      console.error('Error formatting message time:', error, 'Timestamp:', timestamp);
      return 'Now';
    }
  };

  return (
    <Layout>
      <Typography variant="h4" component="h1" gutterBottom>
        Messages
      </Typography>
      
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: '1fr 2fr',
            lg: '300px 1fr'
          },
          gap: 2,
          height: 'calc(100vh - 180px)'
        }}
      >
        {/* Users List */}
        <Paper 
          elevation={2} 
          sx={{ 
            height: '100%', 
            borderRadius: 2,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            {user?.is_admin ? 'All Users' : 'Friends'}
          </Typography>
          <List sx={{ flexGrow: 1, overflow: 'auto' }}>
            {users.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No friends yet" 
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Add friends to start chatting
                      </Typography>
                      <Button 
                        size="small" 
                        variant="outlined" 
                        sx={{ mt: 1 }}
                        onClick={() => window.location.href = '/friends'}
                      >
                        Add Friends
                      </Button>
                    </Box>
                  }
                />
              </ListItem>
            ) : (
              users.map((u) => (
                <React.Fragment key={u.id}>
                  <ListItemButton
                    selected={selectedUser?.id === u.id}
                    onClick={() => handleUserSelect(u)}
                    sx={{
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(94, 53, 177, 0.1)',
                      },
                    }}
                  >
                    <ListItemAvatar>
                      <Badge 
                        badgeContent={unreadCounts[u.id] || 0} 
                        color="error"
                        invisible={!unreadCounts[u.id]}
                      >
                        <Avatar sx={{ bgcolor: selectedUser?.id === u.id ? 'primary.main' : 'grey.400' }}>
                          {u.username.charAt(0).toUpperCase()}
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>
                    <ListItemText 
                      primary={u.full_name} 
                      secondary={u.username}
                      primaryTypographyProps={{
                        fontWeight: selectedUser?.id === u.id || unreadCounts[u.id] ? 'bold' : 'normal',
                      }}
                    />
                    {unreadCounts[u.id] > 0 && (
                      <NotificationIcon sx={{ color: 'primary.main', ml: 1 }} />
                    )}
                  </ListItemButton>
                  <Divider variant="inset" component="li" />
                </React.Fragment>
              ))
            )}
          </List>
        </Paper>
        
        {/* Chat Area */}
        <Paper 
          elevation={2} 
          sx={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            borderRadius: 2
          }}
        >
          {selectedUser ? (
            <>
              {/* Chat Header */}
              <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    {selectedUser.username.charAt(0).toUpperCase()}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">{selectedUser.full_name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      @{selectedUser.username}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    icon={<OnlineIcon sx={{ fontSize: '12px !important' }} />}
                    label={connectionStatus}
                    size="small"
                    color={connectionStatus === 'connected' ? 'success' : connectionStatus === 'connecting' ? 'warning' : 'error'}
                    variant="outlined"
                  />
                  {connectionStatus === 'disconnected' && (
                    <IconButton
                      size="small"
                      onClick={connectWebSocket}
                      title="Reconnect"
                    >
                      <RefreshIcon />
                    </IconButton>
                  )}
                </Box>
              </Box>
              
              {/* Messages */}
              <Box sx={{ 
                flexGrow: 1, 
                overflow: 'auto', 
                p: 2,
                display: 'flex',
                flexDirection: 'column'
              }}>
                {messages.length === 0 ? (
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center',
                    height: '100%'
                  }}>
                    <Typography color="text.secondary">
                      No messages yet. Start a conversation!
                    </Typography>
                  </Box>
                ) : (
                  messages.map((message) => {
                    const isCurrentUser = message.sender_id === user?.id;
                    return (
                      <Box
                        key={message.id}
                        sx={{
                          display: 'flex',
                          justifyContent: isCurrentUser ? 'flex-end' : 'flex-start',
                          mb: 2,
                        }}
                      >
                        {!isCurrentUser && (
                          <Avatar sx={{ mr: 1, bgcolor: 'grey.400' }}>
                            {selectedUser.username.charAt(0).toUpperCase()}
                          </Avatar>
                        )}
                        <Paper
                          elevation={1}
                          sx={{
                            p: 2,
                            maxWidth: '70%',
                            borderRadius: 2,
                            backgroundColor: isCurrentUser 
                              ? (message.is_abusive ? 'error.main' : 'primary.main')
                              : (message.is_abusive ? 'error.light' : 'grey.100'),
                            color: isCurrentUser ? 'white' : 'text.primary',
                            border: message.is_abusive ? '2px solid' : 'none',
                            borderColor: message.is_abusive ? 'error.dark' : 'transparent',
                          }}
                        >
                          {message.is_abusive && (
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                display: 'block', 
                                mb: 1,
                                color: isCurrentUser ? 'rgba(255, 255, 255, 0.9)' : 'error.dark',
                                fontWeight: 'bold',
                                textTransform: 'uppercase'
                              }}
                            >
                              ⚠️ ABUSIVE CONTENT DETECTED
                            </Typography>
                          )}
                          
                          <Typography 
                            variant="body1" 
                            sx={{ 
                              wordBreak: 'break-word',
                              filter: message.is_abusive ? 'blur(4px)' : 'none',
                              transition: 'filter 0.3s ease',
                              cursor: message.is_abusive ? 'pointer' : 'default',
                              '&:hover': {
                                filter: message.is_abusive ? 'blur(0px)' : 'none'
                              }
                            }}
                            title={message.is_abusive ? 'Hover to reveal content' : ''}
                          >
                            {message.content}
                          </Typography>
                          
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              display: 'block', 
                              mt: 1, 
                              opacity: 0.7,
                              color: isCurrentUser ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary'
                            }}
                          >
                            {new Date(message.created_at).toLocaleTimeString()}
                          </Typography>
                        </Paper>
                      </Box>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </Box>
              
              {/* Message Input */}
              <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex' }}>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  size="small"
                  multiline
                  maxRows={4}
                  sx={{ mr: 1 }}
                />
                <IconButton 
                  color="primary" 
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim()}
                  sx={{ 
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '&.Mui-disabled': {
                      bgcolor: 'action.disabledBackground',
                    }
                  }}
                >
                  <SendIcon />
                </IconButton>
              </Box>
            </>
          ) : (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              justifyContent: 'center', 
              alignItems: 'center',
              height: '100%',
              p: 3
            }}>
              <PersonIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Select a contact to start chatting
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>
      
      <Snackbar 
        open={alert.open} 
        autoHideDuration={6000} 
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseAlert} severity={alert.type} sx={{ width: '100%' }}>
          {alert.message}
        </Alert>
      </Snackbar>
    </Layout>
  );
};

export default Chat;