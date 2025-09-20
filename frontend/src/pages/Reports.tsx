import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Chip, Button,
  IconButton, Pagination, Dialog, DialogTitle, DialogContent,
  DialogActions, CircularProgress, Alert, Card, CardContent, Divider,
  TablePagination
} from '@mui/material';
import { 
  Visibility as ViewIcon, 
  Download as DownloadIcon,
  Warning as WarningIcon,
  Person as PersonIcon,
  Report as ReportIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

interface Report {
  id: number;
  user_id: number;
  abuser_id: number;
  abuser_name: string;
  created_at: string;
  status: 'pending' | 'reviewed' | 'escalated';
  severity: 'low' | 'medium' | 'high';
  evidence_count: number;
}

interface Evidence {
  id: number;
  message_content: string;
  timestamp: string;
  abuse_score: number;
}

const Reports: React.FC = () => {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [alert, setAlert] = useState<{open: boolean, message: string, severity: 'success' | 'error'}>({
    open: false,
    message: '',
    severity: 'success'
  });

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await axios.get('/api/reports');
        const reportsData = response.data.map((report: any) => ({
          id: report.id,
          user_id: report.reporter.id,
          abuser_id: report.reported_user.id,
          abuser_name: report.reported_user.full_name,
          created_at: report.created_at,
          status: report.status,
          severity: report.severity.toLowerCase(),
          evidence_count: report.total_abusive_messages
        }));
        
        setReports(reportsData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching reports:', error);
        // Fallback to mock data if API fails
        const mockReports: Report[] = [
          {
            id: 1,
            user_id: user?.id || 1,
            abuser_id: 2,
            abuser_name: 'John Doe',
            created_at: new Date(Date.now() - 3600000).toISOString(),
            status: 'pending',
            severity: 'high',
            evidence_count: 5
          }
        ];
        setReports(mockReports);
        setLoading(false);
      }
    };

    fetchReports();
  }, [user?.id]);

  const handleViewEvidence = async (report: Report) => {
    setSelectedReport(report);
    setLoading(true);
    
    try {
      // In a real implementation, this would be an actual API call
      // For now, we'll simulate the data
      
      // Simulated evidence data
      const evidenceData: Evidence[] = [
        {
          id: 1,
          message_content: "You're such a worthless person, nobody likes you",
          timestamp: new Date(Date.now() - 3700000).toISOString(),
          abuse_score: 0.92
        },
        {
          id: 2,
          message_content: "I hope something bad happens to you tomorrow",
          timestamp: new Date(Date.now() - 3800000).toISOString(),
          abuse_score: 0.85
        },
        {
          id: 3,
          message_content: "You should delete your account, everyone hates you",
          timestamp: new Date(Date.now() - 3900000).toISOString(),
          abuse_score: 0.89
        },
        {
          id: 4,
          message_content: "I'm going to make sure you regret ever talking to me",
          timestamp: new Date(Date.now() - 4000000).toISOString(),
          abuse_score: 0.94
        },
        {
          id: 5,
          message_content: "You're pathetic and should be ashamed of yourself",
          timestamp: new Date(Date.now() - 4100000).toISOString(),
          abuse_score: 0.88
        }
      ];
      
      setEvidence(evidenceData);
      setDialogOpen(true);
    } catch (error) {
      console.error('Error fetching evidence:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedReport(null);
    setEvidence([]);
  };

  const downloadReport = async (reportId: number) => {
    try {
      const response = await axios.get(`/api/reports/${reportId}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cybershield_report_${reportId}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setAlert({ open: true, message: 'Evidence package downloaded successfully! Contains JSON data and screenshots.', severity: 'success' });
    } catch (error) {
      console.error('Error downloading report:', error);
      setAlert({ open: true, message: 'Error downloading evidence package', severity: 'error' });
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'reviewed':
        return 'primary';
      case 'escalated':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && !dialogOpen) {
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
          Abuse Reports
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          View and manage reports of abusive behavior detected by CyberShield.
        </Typography>
      </Box>

      {alert.open && (
        <Alert 
          severity={alert.severity} 
          onClose={() => setAlert({...alert, open: false})}
          sx={{ mb: 2 }}
        >
          {alert.message}
        </Alert>
      )}

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '1fr 2fr' },
        gap: 3,
        mb: 4 
      }}>
        <Box>
          <Card elevation={2} sx={{ borderRadius: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ReportIcon sx={{ color: 'error.main', mr: 1 }} />
                <Typography variant="h6">Report Summary</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Total Reports:</Typography>
                <Typography variant="body1" fontWeight="bold">{reports.length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">High Severity:</Typography>
                <Typography variant="body1" fontWeight="bold" color="error.main">
                  {reports.filter(r => r.severity === 'high').length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Medium Severity:</Typography>
                <Typography variant="body1" fontWeight="bold" color="warning.main">
                  {reports.filter(r => r.severity === 'medium').length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Low Severity:</Typography>
                <Typography variant="body1" fontWeight="bold" color="success.main">
                  {reports.filter(r => r.severity === 'low').length}
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Pending Review:</Typography>
                <Typography variant="body1" fontWeight="bold">
                  {reports.filter(r => r.status === 'pending').length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1">Escalated:</Typography>
                <Typography variant="body1" fontWeight="bold" color="error.main">
                  {reports.filter(r => r.status === 'escalated').length}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Paper elevation={2} sx={{ borderRadius: 2 }}>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Abuser</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Evidence</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reports.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <Typography variant="body1" sx={{ py: 2 }}>
                          No reports found.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    reports
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map((report) => (
                        <TableRow key={report.id}>
                          <TableCell>{report.id}</TableCell>
                          <TableCell>{report.abuser_name}</TableCell>
                          <TableCell>{formatDate(report.created_at)}</TableCell>
                          <TableCell>
                            <Chip 
                              label={report.severity.toUpperCase()} 
                              color={getSeverityColor(report.severity) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={report.status.charAt(0).toUpperCase() + report.status.slice(1)} 
                              color={getStatusColor(report.status) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{report.evidence_count}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<ViewIcon />}
                                onClick={() => handleViewEvidence(report)}
                              >
                                View
                              </Button>
                              <Button
                                variant="contained"
                                size="small"
                                startIcon={<DownloadIcon />}
                                onClick={() => downloadReport(report.id)}
                              >
                                Download
                              </Button>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                  )}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={reports.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
              />
            </TableContainer>
          </Paper>
        </Box>
      </Box>

      {/* Evidence Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Evidence for Report #{selectedReport?.id} - {selectedReport?.abuser_name}
        </DialogTitle>
        <DialogContent dividers>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Message Content</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Abuse Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {evidence.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell 
                        sx={{ 
                          color: 'error.main',
                          fontWeight: item.abuse_score > 0.9 ? 'bold' : 'normal'
                        }}
                      >
                        {item.message_content}
                      </TableCell>
                      <TableCell>{formatDate(item.timestamp)}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box
                            sx={{
                              width: 60,
                              height: 10,
                              bgcolor: 'grey.300',
                              borderRadius: 5,
                              mr: 1
                            }}
                          >
                            <Box
                              sx={{
                                width: `${item.abuse_score * 100}%`,
                                height: '100%',
                                bgcolor: item.abuse_score > 0.9 
                                  ? 'error.main' 
                                  : item.abuse_score > 0.7 
                                    ? 'warning.main' 
                                    : 'success.main',
                                borderRadius: 5
                              }}
                            />
                          </Box>
                          <Typography variant="body2">
                            {(item.abuse_score * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<DownloadIcon />}
            onClick={() => selectedReport && downloadReport(selectedReport.id)}
          >
            Download Report
          </Button>
        </DialogActions>
      </Dialog>
    </Layout>
  );
};

export default Reports;