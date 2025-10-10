# Zephy Jr. Bot Control Panel 🤖

A full-stack Nightbot-style control system for the YouTube Live Chat bot "Zephy Jr." Built with FastAPI + Next.js and featuring a cyberpunk-themed dashboard.

![Zephy Jr. Logo](https://img.shields.io/badge/Zephy%20Jr.-Control%20Panel-00C8FF?style=for-the-badge&logo=robot&logoColor=white)

## ✨ Features

- **🤖 Bot Control**: Start, stop, and monitor bot instances
- **💬 Real-time Chat**: Live chat monitoring and message management
- **🧠 AI Integration**: OpenRouter/Gemini AI with configurable personality
- **📚 Study Tracking**: Focus sessions, goals, and leaderboards
- **🎯 Quiz System**: Interactive quizzes with points and rankings
- **🏆 Points System**: User engagement tracking and rewards
- **⚙️ System Config**: Comprehensive settings and API management
- **🎨 Cyberpunk UI**: Modern, futuristic dashboard design

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite by default)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd zephy-jr-control-panel
cp .env.example .env
# Edit .env with your configuration
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker Setup (Alternative)

```bash
docker-compose up -d
```

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── models/             # Database models
│   └── utils/              # Utilities
├── frontend/               # Next.js frontend
│   ├── src/app/           # App router pages
│   ├── src/components/    # React components
│   └── public/            # Static assets
├── Chatbot_old.py         # Original bot logic
└── docker-compose.yml     # Docker configuration
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./zephyjr.db` |
| `JWT_SECRET` | JWT signing secret | Required |
| `ADMIN_EMAIL` | Admin user email | Required |
| `ADMIN_PASSWORD` | Admin user password | Required |
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Optional |
| `OPENWEATHER_API_KEY` | OpenWeather API key | Required |

### API Keys Setup

1. **YouTube API**: Create OAuth2 credentials in Google Cloud Console
2. **OpenRouter**: Get API key from [OpenRouter](https://openrouter.ai/)
3. **Gemini**: Get API key from [Google AI Studio](https://aistudio.google.com/)
4. **OpenWeather**: Get API key from [OpenWeatherMap](https://openweathermap.org/)

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login
- `GET /api/auth/me` - Get current user

### Bot Control
- `POST /api/bot/start` - Start bot instance
- `POST /api/bot/stop` - Stop bot instance
- `GET /api/bot/status` - Get bot status
- `POST /api/bot/restart` - Restart bot

### Chat Management
- `POST /api/chat/send` - Send manual message
- `GET /api/chat/logs` - Get chat logs
- `GET /api/chat/stats` - Get chat statistics

### AI Services
- `POST /api/ai/reply` - Generate AI reply
- `GET /api/ai/models` - Get available models
- `POST /api/ai/test` - Test AI connection

### Study Tracking
- `POST /api/study/start` - Start study session
- `POST /api/study/stop` - Stop study session
- `GET /api/study/leaderboard` - Get leaderboard
- `POST /api/study/goal` - Set study goal

### Quiz System
- `POST /api/quiz/start` - Start quiz
- `POST /api/quiz/answer` - Answer quiz
- `GET /api/quiz/leaderboard` - Get quiz leaderboard

### Points System
- `GET /api/points/leaderboard` - Get points leaderboard
- `POST /api/points/add` - Add points
- `GET /api/points/user/{user_id}` - Get user points

### System Settings
- `GET /api/system/settings` - Get system settings
- `POST /api/system/settings` - Update settings
- `GET /api/system/health` - System health check

## 🎨 UI Components

### Cyberpunk Theme
- **Colors**: Electric blue (#00C8FF), magenta (#FF00CC), neon green (#00FF88)
- **Fonts**: Orbitron (headings), Inter (body)
- **Effects**: Glow, pulse, typing animations
- **Grid**: Subtle cyberpunk grid background

### Key Components
- `CyberCard` - Main content containers
- `CyberButton` - Primary action buttons
- `CyberInput` - Form inputs with glow effects
- `StatusIndicator` - Online/offline status
- `AnimatedCounter` - Number animations

## 🚀 Deployment

### Local Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Azure Deployment
1. Push backend to Azure App Service
2. Deploy frontend to Vercel/Azure Static Web Apps
3. Configure environment variables
4. Set up custom domain

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Input validation
- SQL injection prevention
- Rate limiting

## 📊 Monitoring

- Real-time bot status
- Message count tracking
- Error monitoring
- Performance metrics
- Health checks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original Zephy Jr. bot implementation
- FastAPI and Next.js communities
- Cyberpunk design inspiration
- Open source contributors

---

**Zephy Jr. — Your Stream's Smartest, Sassiest Sidekick 🤖**

*Built with ❤️ and lots of caffeine*