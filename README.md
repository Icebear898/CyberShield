# CyberShield: AI-Powered Cyberbullying Detection & Auto-Response System

CyberShield is an advanced system designed to protect users from online harassment and cyberbullying through real-time message monitoring, AI-powered abuse detection, and automated response mechanisms.

## Problem Statement

Women and girls on social media often face online harassment and repeated abusive messages or comments. Manual blocking or reporting is reactive and delayed, leaving victims exposed to psychological harm. There is a need for an automated system that detects, alerts, and mitigates online bullying in real time.

## Solution Overview

CyberShield provides a comprehensive solution that:

- **Monitors messages in real-time** using WebSocket connections
- **Detects abusive content** using Groq AI language model and keyword analysis
- **Implements a threshold mechanism**:
  - 1-2 abusive messages → Alert notification to the user
  - Multiple abusive messages → Automatically block the sender
- **Generates evidence reports** for reporting to authorities
- **Offers customizable sensitivity settings** based on user comfort level

## Key Features

✅ **Real-time Detection** of abusive/harassing messages  
✅ **Threshold-based Alerts & Blocking** of offenders  
✅ **Automated Safe Report Generation** for authorities  
✅ **Admin Dashboard** with system-wide analytics (admin-only access)  
✅ **Real-time WebSocket Chat** with reliable connection management  
✅ **Premium UI Design** with modern Material-UI theming  
✅ **Role-based Access Control** (Admin vs Regular Users)  
✅ **Privacy-first approach** (data stays local or encrypted)

## Tech Stack

- **Frontend**: React with TypeScript, Material-UI
- **Backend**: FastAPI (Python)
- **AI Model**: Groq LLM for abuse detection with keyword fallback
- **Database**: SQLite
- **Communication**: WebSockets for real-time messaging

## System Architecture

### Backend Components

1. **FastAPI Application**
   - Main entry point for the application
   - Handles HTTP requests and WebSocket connections
   - Routes for authentication, users, messages, and reports

2. **Database Models**
   - User: Stores user information
   - Message: Records all messages with abuse detection results
   - Report: Tracks generated abuse reports
   - BlockedUser: Manages blocked user relationships

3. **WebSocket Manager**
   - Handles real-time connections
   - Processes incoming messages
   - Implements threshold-based alerts and blocking

4. **AI Abuse Detector**
   - Analyzes message content using Groq LLM
   - Provides fallback keyword-based detection
   - Returns abuse scores and detection details

### Frontend Components

1. **Authentication System**
   - Login and registration pages
   - JWT token management
   - Protected routes

2. **Chat Interface**
   - Real-time messaging with WebSockets
   - Visual indicators for abusive messages
   - Alert notifications for detected abuse

3. **Dashboard**
   - Overview of user statistics
   - Recent activity tracking
   - Quick access to reports and settings

4. **Reports Management**
   - View and download evidence reports
   - Track abuse history
   - Manage blocked users

5. **Settings**
   - Customize sensitivity levels
   - Configure auto-blocking thresholds
   - Manage notification preferences

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Groq API key

### Backend Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd CyberShield
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the backend directory with:
   ```
   GROQ_API_KEY=your_groq_api_key
   SECRET_KEY=your_secret_key_for_jwt
   ```

5. Create admin user and test users:
   ```
   python create_admin.py
   ```

6. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

2. Configure API endpoint:
   Create a `.env` file in the frontend directory with:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

3. Start the frontend development server:
   ```
   npm start
   ```

4. Access the application at `http://localhost:3000`

## Default Credentials

### Admin Access
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@cybershield.com`
- **Access**: Full system dashboard and analytics

### Test Users (for demo)
- **Alice**: Username: `alice`, Password: `alice123`
- **Bob**: Username: `bob`, Password: `bob123`  
- **Charlie**: Username: `charlie`, Password: `charlie123`

⚠️ **Important**: Change the default admin password after first login!

## Usage Guide

### Admin Dashboard Access

1. Log in with admin credentials
2. Access the Dashboard from the sidebar (only visible to admins)
3. View system-wide statistics and user activity
4. Monitor abuse reports and alerts

### Regular User Features

#### Registration and Login

1. Create a new account using the registration page
2. Log in with your credentials
3. Regular users will see Chat, Reports, and Settings in the sidebar

#### Real-Time Chat with Protection

1. Navigate to the Chat page
2. Select a user from the contacts list to start a conversation
3. Send and receive messages in real-time via WebSocket
4. Monitor connection status (connected/connecting/disconnected)
5. Use manual reconnect if connection drops
6. The system will automatically:
   - Detect abusive messages using AI
   - Highlight abusive content in red
   - Send real-time alerts when abuse is detected
   - Block users who repeatedly send abusive content
   - Maintain conversation history

### Managing Reports

1. Go to the Reports page to view detected abuse
2. View evidence details for each report
3. Download reports for sharing with authorities

### Customizing Settings

1. Visit the Settings page
2. Adjust sensitivity levels based on your comfort
3. Configure auto-blocking thresholds
4. Manage notification preferences

## Recent Updates & Improvements

### Version 2.0 Features

✅ **Admin Dashboard**: Comprehensive system analytics and user management (admin-only access)  
✅ **Enhanced WebSocket Chat**: Reliable real-time messaging with auto-reconnection  
✅ **Premium UI Design**: Modern Material-UI theming with improved user experience  
✅ **Role-Based Access Control**: Separate admin and user interfaces  
✅ **Connection Management**: Visual connection status indicators and manual reconnect  
✅ **Improved Layout**: Fixed navbar overlapping issues for better navigation  

### Technical Improvements

- **Backend**: Enhanced SQLAlchemy relationships and Pydantic v2 compatibility
- **Frontend**: TypeScript improvements and better state management
- **Database**: Added admin role support and improved schema design
- **WebSocket**: Exponential backoff reconnection strategy with up to 5 retry attempts
- **UI/UX**: Premium color scheme, improved shadows, and modern component styling

## Security and Privacy

CyberShield prioritizes user privacy and security:

- All message analysis happens locally or through secure encrypted channels
- Message content is only stored when necessary for evidence reports
- Reports are controlled by the user and never shared without permission
- User data is protected with secure authentication

## Future Enhancements

- Multi-language support for global accessibility
- Integration with popular social media platforms
- AI chatbot for mental health support
- Browser plugin for monitoring comments on websites
- Community mode to share patterns of abusers (privacy-preserved)

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact [project maintainer email]