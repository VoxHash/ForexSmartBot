# Mobile Companion App

This folder contains the mobile companion app for ForexSmartBot.

## Features

- Real-time monitoring
- Push notifications
- Basic trading controls
- Portfolio overview
- Strategy status

## Platforms

- iOS (Swift)
- Android (Kotlin/Java)
- React Native (Cross-platform)

## API Integration

The mobile app connects to the ForexSmartBot API server:
- REST API: `http://localhost:5000/api`
- WebSocket: `ws://localhost:8765`

## Setup

1. Configure API endpoint in app settings
2. Authenticate using API key
3. Enable push notifications

## Integration

The mobile app is integrated with:
- `forexsmartbot/cloud/mobile_api.py` - Mobile API endpoints
- `forexsmartbot/cloud/api_server.py` - Main API server
- `forexsmartbot/cloud/security.py` - Authentication and security

