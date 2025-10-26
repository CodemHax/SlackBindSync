# BindSync Backend

A powerful bridge system that synchronizes messages between Telegram and Discord with a RESTful API.

## Features

- 🔄 **Bidirectional Message Sync**: Messages flow seamlessly between Telegram and Discord
- 🔐 **Secure API**: Token-based authentication with admin management
- 📝 **Message History**: MongoDB-powered message storage and retrieval
- 💬 **Reply Threading**: Maintains reply context across platforms
- 🌐 **REST API**: Full-featured API for external integrations
- 🎛️ **Admin Dashboard**: Web interface for token management

## Architecture

```
├── main.py                 # Application entry point
├── src/
│   ├── api/               # FastAPI REST endpoints
│   │   ├── server.py      # Main API routes
│   │   └── admin_routes.py # Admin & token management
│   ├── auth/              # Authentication system
│   │   └── auth_manager.py # Token & admin management
│   ├── bot/               # Bot implementations
│   │   ├── tg_bot.py      # Telegram bot
│   │   └── dc_bot.py      # Discord bot
│   ├── core/              # Core functionality
│   │   ├── forward.py     # Main application logic
│   │   └── models.py      # Pydantic models
│   ├── database/          # Database layer
│   │   ├── database.py    # MongoDB connection
│   │   └── store_functions.py # Data operations
│   └── utils/             # Utilities
│       ├── bridge.py      # Message forwarding
│       └── misc.py        # Helper functions
└── test_api.py            # Comprehensive test suite

```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
MONGO_URI=your_mongodb_connection_string
MONGO_DB=your_database_name
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Run the Application

```bash
python main.py
```

## Testing

The `test_api.py` script provides comprehensive testing capabilities.

### Quick System Check

```bash
python test_api.py system
```

Verifies:
- ✅ Health endpoint
- ✅ Admin status
- ✅ Bot connectivity
- ✅ Database connection
- ✅ API protection

### Initial Setup

First time setup - register admin account:

```bash
python test_api.py setup
```

### Authentication Test

Test admin login and token creation:

```bash
python test_api.py auth <username> <password>
```

This will:
1. Login as admin
2. Create an API token
3. Test API with the token
4. Test token revocation
5. Verify revoked token is rejected

### API Tests

**Quick Test** - Fast API status check:
```bash
python test_api.py quick
```

**Message Test** - Test message sending:
```bash
python test_api.py message
```

**Token Test** - Test with existing token:
```bash
python test_api.py token <your_api_token>
```

**Full Test** - Comprehensive test suite:
```bash
python test_api.py full
```

### Help

```bash
python test_api.py help
```

## API Endpoints

### Public Endpoints

- `GET /` - Landing page
- `GET /health` - System health check
- `GET /admin` - Admin login page
- `GET /admin/status` - Check if admin exists
- `POST /admin/register` - Register admin (first time only)
- `POST /admin/login` - Admin login

### Protected Endpoints (Require X-API-Token header)

- `GET /messages` - List messages
- `GET /messages/{id}` - Get specific message
- `POST /messages` - Send new message
- `POST /messages/{id}/reply` - Reply to message

### Admin Endpoints (Require X-Admin-Token header)

- `GET /admin/tokens` - List API tokens
- `POST /admin/tokens` - Create new API token
- `PATCH /admin/tokens/{name}/revoke` - Revoke token
- `DELETE /admin/tokens/{name}` - Delete token
- `POST /admin/logout` - Logout

## Usage Examples

### Get Messages

```bash
curl -H "X-API-Token: your_token" http://localhost:8000/messages?limit=10
```

### Send Message

```bash
curl -X POST -H "X-API-Token: your_token" \
  -H "Content-Type: application/json" \
  -d '{"username":"API","text":"Hello from API!"}' \
  http://localhost:8000/messages
```

### Reply to Message

```bash
curl -X POST -H "X-API-Token: your_token" \
  -H "Content-Type: application/json" \
  -d '{"username":"API","text":"This is a reply"}' \
  http://localhost:8000/messages/{message_id}/reply
```

## Health Check Response

```json
{
  "status": "healthy",
  "version": "4.0.0",
  "runtime": {
    "telegram_bot": true,
    "discord_bot": true,
    "api_configured": true,
    "message_mapping": true
  },
  "services": {
    "database": "connected",
    "telegram": "running",
    "discord": "running"
  }
}
```

## Development

### Running in Development

```bash
python main.py
```

### Docker Deployment

```bash
docker build -t bindsync .
docker run -d --env-file .env -p 8000:8000 bindsync
```

## Security Notes

- API tokens are required for all message operations
- Admin sessions are managed separately from API tokens
- Tokens can have expiration dates
- Tokens can be revoked at any time
- All authentication uses secure token generation

## Troubleshooting

### Bots Not Running

Check the health endpoint to verify bot status:
```bash
curl http://localhost:8000/health
```

### Authentication Issues

1. Check if admin exists: `python test_api.py system`
2. Register admin: `python test_api.py setup`
3. Test authentication: `python test_api.py auth <user> <pass>`

### Database Connection

Verify MongoDB connection in the health check response.

## License

MIT License

## Version

4.0.0


