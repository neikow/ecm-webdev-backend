# game.ly

## Overview

`game.ly` is a lightweight multi-player web-based game framework. It provides lobby management and a real-time
multiplayer event system, allowing developers to focus on building engaging game experiences without worrying about the
underlying infrastructure.

## Architecture

The framework is built using a client-server architecture. The server handles lobby management, player connections,
and real-time event broadcasting. The client connects to the server, manages player input, and renders the game state.

**Frontend**: React.js with TypeScript and type generation using OpenAPI. <br>
**Backend**: FastAPI and SQLModel for database interactions.

## Features

- **Lobby Management**: Create, join, and manage game lobbies with ease.
- **Real-time Multiplayer**: Real-time communication between players using WebSockets.
- **Event System**: Broadcast and handle game events efficiently. Supporting targeted events to specific players or
  groups.
- **Scalability**: Designed to handle multiple concurrent lobbies and players.
- **Extensibility**: Easily extend the framework to add custom game logic and features.

## Getting Started

The project uses `FastAPI` (Python) for the backend and `vite` (React + TypeScript) for the frontend.
You'll need to have `python` and `node` installed on your machine.

### Clone the Repository

```bash
git clone git@github.com:neikow/gamely.git
cd gamely
```

### Create a .env File

Create a `.env` file in the root directory based on the provided `.env.example` file:

```bash
cp .env.example .env
```

### Backend Setup

The project uses [`uv`](https://docs.astral.sh/uv/) as package manager.

```bash
uv sync # in the root folder
```

Generate the SSL certificates for local development:

```bash
uv run python scripts/generate_ssl_certificates.py
```

To run the backend server:

```bash
uv run uvicorn backend.server:app --reload --reload --port 8000 --ssl-keyfile certs/localhost-8000.key.pem --ssl-certfile certs/localhost-8000.crt.pem
```

The backend server will be accessible at `https://127.0.0.1:8000`.

### Frontend Setup

Navigate to the `frontend` directory and install dependencies:

```bash
cd frontend
yarn
```

To start the frontend development server:

```bash
yarn dev
```

The frontend will be accessible at `https://127.0.0.1:5173`.

### IntelliJ IDE

If you're using IntelliJ IDE, you can open the project directly and it should recognize both the backend and frontend
modules. Make sure to set up the Python interpreter for the backend module.