
# SYN (Sync Your Network)

## Overview
SYN is employee scheduling and management system built with FastAPI and React. It provides a robust platform for managing employee schedules, shift trades, leave requests, and company announcements.

**Live Demo:** [https://syn-frontend.vercel.app](https://syn-frontend.vercel.app)  
**Demo Credentials:** Any employee email with password: `demo1234` (Employee IDs available in Employee Management section)

## Key Features

### Admin Features
- Schedule Management
  - Create and modify employee schedules
  - Bulk schedule creation
  - Schedule conflict detection(working on it)
- Employee Management
  - Department and position management
- Leave Request Management
  - Review and process leave requests
  - Leave balance tracking(working on it)
- Announcement System
  - Create and manage company announcements


### Employee Features
- Schedule Viewing
  - Personal schedule calendar
  - Weekly/monthly view options
- Shift Trade System
  - Request and accept shift trades
  - Direct employee-to-employee trades
- Leave Management
  - Submit leave requests
  - Track request status
- Notification Center
  - Real-time updates


## Tech Stack

### Frontend
- React.js with Vite
- TypeScript
- Redux Toolkit for state management
- TailwindCSS for styling
- WebSocket for real-time features

### Backend
- Python FastAPI
- PostgreSQL database
- Redis for caching and real-time features
- WebSocket for real-time notifications
- JWT authentication

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL


### Frontend Setup
```bash
# Clone the repository
git clone https://github.com/kimjeffsj/syn-frontend.git

# Install dependencies
cd syn-frontend
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/kimjeffsj/syn-backend.git

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## Project Structure

### Frontend Structure
```
src/
├── app/              # App configuration and store
├── features/         # Feature-based modules
├── services/         # API and WebSocket services
├── shared/          # Shared components and utilities
└── styles/          # Global styles and theme
```

### Features Overview
- `admin-dashboard`: Admin control panel and overview
- `announcement`: Company-wide announcement system
- `auth`: Authentication and authorization
- `employee-dashboard`: Employee dashboard and personal overview
- `schedule`: Schedule management and calendar
- `shift-trade`: Shift trade system
- `leave`: Leave request management

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## Deployment
- Frontend: Vercel deployment
- Backend: Render
- DB: Render PostgreSQL

## License
This project is licensed under the MIT License - see the LICENSE file for details


## Contact

Seongjun Kim
-   LinkedIn:  [https://www.linkedin.com/in/jeffseongjunkim/](https://www.linkedin.com/in/jeffseongjunkim/)
-   Email:  [kim.jeffsj@gmail.com](mailto:kim.jeffsj@gmail.com)

**Project Links:**

-   Frontend: [https://github.com/kimjeffsj/SYN-frontend](https://github.com/kimjeffsj/SYN-frontend)
-   Backend: [https://github.com/kimjeffsj/SYN-backend](https://github.com/kimjeffsj/SYN-backend)

## Acknowledgments
- React.js
- FastAPI
- TailwindCSS
- And all other open source libraries used in this project
