# Instagram Persona Bot

An autonomous Instagram DM AI Agent that mirrors your personality.

## Components

- `trainer.py`: Scrapes your sent messages and uses OpenAI to generate a `persona.json` that captures your style and tone.
- `agent.py`: The core bot that polls for unread DMs and responds using your persona.
- `memory.py`: Manages conversation history using SQLite.
- `persona.json`: Stores your synthesized personality profile.

## Setup

### Option 1: Desktop (PC/Mac/Linux)
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and fill in your credentials.

### Option 2: Mobile (Android via Termux)
Recommended for absolute beginners and to avoid credit card requirements.

1. **Install Termux**: Download from [F-Droid](https://f-droid.org/en/packages/com.termux/) (the Google Play version is outdated).
2. **Setup Environment**: Open Termux and run:
   ```bash
   pkg update && pkg upgrade
   pkg install git python python-dev clang libjpeg-turbo
   ```
3. **Clone & Install**:
   ```bash
   git clone <your-repo-url>
   cd ig-persona-bot
   pip install -r requirements.txt
   ```
4. **Configure**: Create your `.env` file:
   ```bash
   nano .env
   ```
   (Paste your credentials, then press `Ctrl+O`, `Enter`, `Ctrl+X`)
5. **Keep Alive**: Run `termux-wake-lock` to prevent Android from killing the process.

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

### Hugging Face Spaces (Free Cloud Hosting)
1. Create a new **Space** on [Hugging Face](https://huggingface.co/new-space).
2. Select **Docker** as the SDK.
3. Upload all project files or connect your GitHub repository.
4. Go to **Settings** > **Variables and secrets** and add:
   - `IG_USERNAME`
   - `IG_PASSWORD`
   - `OPENAI_API_KEY`
5. The bot will start automatically using `start.sh`.

*Note: Free Spaces go to sleep after 48h of inactivity. Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your Space's URL and keep it awake.*

### Render
This project includes a `render.yaml` for easy deployment as a Background Worker on Render.

## Important Notes

- **Persistence**: Free hosting like Hugging Face and Render have ephemeral storage. Your `memory.db` and `persona.json` will be lost if the container restarts. For long-term use, Termux (on a phone) is better as it keeps files locally.
- **Instagram Challenges**: If Instagram asks for a security code, Termux is easier because you can handle the challenge directly in the terminal.
- **Safety**: Instagram may flag automated accounts. Use with caution. The bot includes random sleep intervals to minimize risk.
