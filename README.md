# 🔭 RepoLens — GitHub Repo Intelligence Engine
 
> An agentic AI tool that reads any GitHub repository and delivers a structured report covering architecture, code quality, security, dependencies, bugs, and improvement suggestions — powered by **Python**, **Streamlit**, and **Groq AI**.
 
---
 
## What it does
 
RepoLens acts as an autonomous agent. You give it a GitHub URL; it does the rest:
 
1. Fetches repository metadata (stars, forks, topics, license, language breakdown)
2. Recursively maps the entire file tree
3. Intelligently selects and reads the most valuable source files
4. Sends the full context to a Groq-hosted LLaMA model
5. Returns a structured JSON report rendered as a clean tabbed UI
The whole pipeline runs in 10–20 seconds for most repositories.
 
---
 
## Features
 
| Feature | Description |
|---|---|
| 🏗️ **Architecture analysis** | Detects patterns (MVC, microservices, monolith, etc.), lists strengths and concerns |
| 📊 **Code quality score** | 1–10 score with specific observations from the actual source |
| 🔒 **Security scan** | Flags risky patterns, hardcoded secrets, insecure configs with fix suggestions |
| 📦 **Dependency review** | Lists notable packages, flags outdated or risky dependencies |
| 🐛 **Bug detection** | Spots potential bugs and anti-patterns in the code |
| 🚀 **Improvement suggestions** | Prioritised, effort-tagged recommendations (High/Medium/Low) |
| 📝 **Documentation check** | Verifies presence of README, CONTRIBUTING guide, CHANGELOG |
| ⬇️ **JSON export** | Download the complete structured report |
 
---
 
## Quick start
 
### 1. Get the code
 
```bash
git clone https://github.com/your-username/repolens.git
cd repolens
```
 
Or unzip the downloaded archive:
 
```bash
unzip github-analyser.zip
cd github-analyser
```
 
### 2. Create a virtual environment
 
```bash
python -m venv .venv
 
# macOS / Linux
source .venv/bin/activate
 
# Windows
.venv\Scripts\activate
```
 
### 3. Install dependencies
 
```bash
pip install -r requirements.txt
```
 
### 4. Run the app
 
```bash
streamlit run app.py
```
 
The app opens at `http://localhost:8501` in your browser.
 
---
 
## API keys
 
You will be prompted for these in the sidebar when the app opens.
 
### Groq API key (required)
 
Groq provides free, ultra-fast LLM inference.
 
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in (free)
3. Navigate to **API Keys → Create API Key**
4. Copy the key (starts with `gsk_`)
### GitHub Personal Access Token (optional)
 
Without a token, the GitHub API allows 60 requests/hour. A token raises this to 5,000/hour and is required for private repositories.
 
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select the `repo` scope (or just `public_repo` for public repos only)
4. Copy the token (starts with `ghp_`)
---
 
## Supported models
 
Select your model in the sidebar. Larger models produce richer analysis; smaller models are faster.
 
| Model | Best for | Context |
|---|---|---|
| `llama-3.3-70b-versatile` | Best quality, recommended | 7,000 tokens |
| `llama-3.1-8b-instant` | Speed, larger repos | 14,000 tokens |
| `mixtral-8x7b-32768` | Very large codebases | 28,000 tokens |
 
> **Note on token limits:** RepoLens automatically trims file content to fit within each model's limit. If you hit a 413 error, switch to `mixtral-8x7b-32768` or reduce the "Files to read" slider.
 
---
 
## Project structure
 
```
github-analyser/
│
├── app.py                        # Streamlit UI — layout, sidebar, search bar, progress steps
│
├── .streamlit/
│   └── config.toml               # Theme config (light mode, brand colours)
│
├── agents/
│   ├── __init__.py
│   └── github_agent.py           # Groq LLM agent, prompt engineering, token budgeting
│
├── utils/
│   ├── __init__.py
│   ├── github_client.py          # GitHub REST API client (metadata, tree, file content)
│   └── display.py                # All Streamlit rendering (tabs, cards, charts, pills)
│
├── requirements.txt
└── README.md
```
 
### Key files explained
 
**`agents/github_agent.py`** — The brain of the app. Builds a structured prompt from the repo context, calls the Groq API, and parses the JSON response. Includes automatic token budgeting with three fallback tiers (100% → 50% → 30% of limit) so it never hits a 413 error.
 
**`utils/github_client.py`** — Handles all GitHub REST API calls. Intelligently prioritises which files to read (config files, READMEs, and short dependency files first, then source code by path depth).
 
**`utils/display.py`** — Pure rendering logic, fully decoupled from data fetching. Takes the parsed JSON report and renders each analysis tab.
 
---
 
## Configuration
 
All settings are available in the sidebar:
 
| Setting | Default | Description |
|---|---|---|
| Groq API Key | — | Required. Your Groq API key |
| GitHub Token | — | Optional. For private repos and higher rate limits |
| Model | `llama-3.3-70b-versatile` | LLM used for analysis |
| Analysis scope | 6 of 8 modules | Which sections to include in the report |
| Files to read | 15 | How many source files the agent reads (5–40) |
 
---
 
## Example repositories to try
 
```
https://github.com/tiangolo/fastapi
https://github.com/streamlit/streamlit
https://github.com/psf/requests
https://github.com/django/django
https://github.com/pallets/flask
https://github.com/huggingface/transformers
```
 
---
 
## Troubleshooting
 
**413 Request too large**
The repo has too many large files. Reduce the "Files to read" slider to 10 or less, or switch to the `mixtral-8x7b-32768` model which has a larger token budget.
 
**404 Not found**
The repository is private and you haven't provided a GitHub token with `repo` access, or the URL is incorrect.
 
**GitHub rate limit exceeded**
You've hit the 60 req/hour unauthenticated limit. Add a GitHub Personal Access Token in the sidebar to increase this to 5,000/hour.
 
**Analysis takes too long**
Switch to `llama-3.1-8b-instant` for faster (though less detailed) results.
 
---
 
## Requirements
 
```
streamlit>=1.35.0
groq>=0.9.0
requests>=2.31.0
```
 
Python 3.9 or higher is recommended.
 
---
 
## License
 
MIT — free to use, modify, and distribute.