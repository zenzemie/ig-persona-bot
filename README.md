# Instagram Persona Bot

An autonomous Instagram DM AI Agent that mirrors your personality.

## Components

- `trainer.py`: Scrapes your sent messages and uses OpenAI to generate a `persona.json` that captures your style and tone.
- `agent.py`: The core bot that polls for unread DMs and responds using your persona.
- `memory.py`: Manages conversation history using SQLite.
- `persona.json`: Stores your synthesized personality profile.

## Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and fill in your credentials:
   ```
   IG_USERNAME=your_username
   IG_PASSWORD=your_password
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

### 1. Generate your persona
Run the trainer to analyze your past interactions and create your `persona.json`.
```bash
python trainer.py
```

### 2. Start the agent
Run the agent to start responding to DMs.
```bash
python agent.py
```

## Deployment

This project is ready for deployment on **Render** or any platform supporting **Docker**.

- `Dockerfile`: Container configuration.
- `render.yaml`: Configuration for Render worker.
- `start.sh`: Entrypoint script.

## Caution

- Instagram may flag automated accounts. Use with caution and at your own risk.
- The bot includes random sleep intervals to minimize the risk of being banned.
- Initial login might require manual intervention if 2FA is enabled.
