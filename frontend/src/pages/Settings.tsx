import React, { useState } from 'react';
import {
  Box, Typography, Paper, FormControl, FormLabel,
  RadioGroup, FormControlLabel, Radio, Slider, Switch,
  Button, Divider, Alert, Snackbar, Card, CardContent
} from '@mui/material';
import {
  Save as SaveIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Block as BlockIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

const Settings: React.FC = () => {
  const { user } = useAuth();
  
  // Settings state
  const [sensitivityLevel, setSensitivityLevel] = useState<string>('medium');
  const [autoBlockThreshold, setAutoBlockThreshold] = useState<number>(3);
  const [enableNotifications, setEnableNotifications] = useState<boolean>(true);
  const [enableAutoBlock, setEnableAutoBlock] = useState<boolean>(true);
  const [enableReportGeneration, setEnableReportGeneration] = useState<boolean>(true);
  const [alertOpen, setAlertOpen] = useState<boolean>(false);
  
  const handleSensitivityChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSensitivityLevel((event.target as HTMLInputElement).value);
  };
  
  const handleAutoBlockThresholdChange = (event: Event, newValue: number | number[]) => {
    setAutoBlockThreshold(newValue as number);
  };
  
  const handleNotificationsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEnableNotifications(event.target.checked);
  };
  
  const handleAutoBlockChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEnableAutoBlock(event.target.checked);
  };
  
  const handleReportGenerationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEnableReportGeneration(event.target.checked);
  };
  
  const handleSaveSettings = () => {
    // In a real implementation, this would save settings to the backend
    console.log('Saving settings:', {
      sensitivityLevel,
      autoBlockThreshold,
      enableNotifications,
      enableAutoBlock,
      enableReportGeneration
    });
    
    setAlertOpen(true);
  };
  
  const handleCloseAlert = () => {
    setAlertOpen(false);
  };
  
  const getSensitivityDescription = () => {
    switch (sensitivityLevel) {
      case 'low':
        return 'Only detects severe abuse and explicit threats. May miss subtle harassment.';
      case 'medium':
        return 'Balanced detection that catches most abusive content while minimizing false positives.';
      case 'high':
        return 'Highly sensitive detection that catches subtle forms of harassment but may have more false positives.';
      default:
        return '';
    }
  };

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Customize your CyberShield protection preferences.
        </Typography>
      </Box>
      
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
        gap: 3,
        mb: 3
      }}>
        {/* Sensitivity Settings */}
        <Box>
          <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SecurityIcon sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h5" component="h2">
                Protection Settings
              </Typography>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            <FormControl component="fieldset" sx={{ mb: 4 }}>
              <FormLabel component="legend" sx={{ mb: 1, fontWeight: 'bold' }}>
                Abuse Detection Sensitivity
              </FormLabel>
              <RadioGroup
                name="sensitivity-level"
                value={sensitivityLevel}
                onChange={handleSensitivityChange}
              >
                <FormControlLabel value="low" control={<Radio />} label="Low" />
                <FormControlLabel value="medium" control={<Radio />} label="Medium (Recommended)" />
                <FormControlLabel value="high" control={<Radio />} label="High" />
              </RadioGroup>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {getSensitivityDescription()}
              </Typography>
            </FormControl>
            
            <Box sx={{ mb: 4 }}>
              <Typography id="auto-block-threshold-slider" gutterBottom sx={{ fontWeight: 'bold' }}>
                Auto-Block Threshold: {autoBlockThreshold} abusive messages
              </Typography>
              <Slider
                value={autoBlockThreshold}
                onChange={handleAutoBlockThresholdChange}
                aria-labelledby="auto-block-threshold-slider"
                valueLabelDisplay="auto"
                step={1}
                marks
                min={1}
                max={10}
                disabled={!enableAutoBlock}
              />
              <Typography variant="body2" color="text.secondary">
                Number of abusive messages before automatically blocking a user.
              </Typography>
            </Box>
          </Paper>
        </Box>
        
        {/* Notification Settings */}
        <Box>
          <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <NotificationsIcon sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h5" component="h2">
                Notification & Response Settings
              </Typography>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            <FormControl component="fieldset" sx={{ width: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    Enable Abuse Notifications
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Receive alerts when abusive content is detected.
                  </Typography>
                </Box>
                <Switch
                  checked={enableNotifications}
                  onChange={handleNotificationsChange}
                  inputProps={{ 'aria-label': 'enable notifications' }}
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    Enable Auto-Blocking
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Automatically block users who send multiple abusive messages.
                  </Typography>
                </Box>
                <Switch
                  checked={enableAutoBlock}
                  onChange={handleAutoBlockChange}
                  inputProps={{ 'aria-label': 'enable auto-blocking' }}
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    Enable Evidence Report Generation
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Automatically generate reports for abusive conversations.
                  </Typography>
                </Box>
                <Switch
                  checked={enableReportGeneration}
                  onChange={handleReportGenerationChange}
                  inputProps={{ 'aria-label': 'enable report generation' }}
                />
              </Box>
            </FormControl>
          </Paper>
        </Box>
      </Box>
        
      {/* Privacy Information */}
      <Box sx={{ mb: 3 }}>
        <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <BlockIcon sx={{ color: 'error.main', mr: 1 }} />
            <Typography variant="h6">
              Blocked Users
            </Typography>
          </Box>
          <Typography variant="body2" paragraph>
            You currently have 3 blocked users. Blocked users cannot send you messages or see your online status.
          </Typography>
          <Button variant="outlined" size="small">
            Manage Blocked Users
          </Button>
        </Paper>
      </Box>
      
      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
        >
          Save Settings
        </Button>
      </Box>
      
      <Snackbar
        open={alertOpen}
        autoHideDuration={6000}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseAlert} severity="success" sx={{ width: '100%' }}>
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Layout>
  );
};

export default Settings;