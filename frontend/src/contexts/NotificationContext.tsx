import React, { createContext, useState, useContext, ReactNode } from 'react';

interface NotificationContextType {
  unreadCount: number;
  incrementUnread: () => void;
  decrementUnread: () => void;
  setUnreadCount: (count: number) => void;
  clearUnread: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [unreadCount, setUnreadCountState] = useState(0);

  const incrementUnread = () => {
    setUnreadCountState(prev => prev + 1);
  };

  const decrementUnread = () => {
    setUnreadCountState(prev => Math.max(0, prev - 1));
  };

  const setUnreadCount = (count: number) => {
    setUnreadCountState(Math.max(0, count));
  };

  const clearUnread = () => {
    setUnreadCountState(0);
  };

  const value = {
    unreadCount,
    incrementUnread,
    decrementUnread,
    setUnreadCount,
    clearUnread
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
