import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const SmartRedirect: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Redirect based on user role
  if (user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  } else {
    return <Navigate to="/chat" replace />;
  }
};

export default SmartRedirect;
