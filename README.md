# LangGraph Voice Travel Agent + LiveKit Outbound Campaign

Voice-enabled travel planning agent built with LangGraph and LiveKit. It orchestrates a conversational workflow (budget → activities → preferences → flight/hotel options → itinerary → summary) and can dial users via LiveKit SIP to run a guided planning session. Includes a modern dark campaign UI to upload leads and visualize each call’s status.

- Author: Amr Elhaweet
- Contact: ellhaweet@gmail.com

## Overview
- LangGraph agent: The `TravelPlanningAgent` runs a structured state graph to collect inputs and produce a trip plan.
- LiveKit voice: Real-time STT/LLM/TTS via plugins and `AgentSession`.
- Outbound call helper: Initiates single outbound calls using your LiveKit SIP trunk.
- Campaign server: FastAPI app to upload CSV leads, run the calling campaign, and visualize per-number status.

Key files:
- Agent: <mcfile name="langgraph_voice_agent.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_voice_agent.py"></mcfile> with entrypoint <mcsymbol name="entrypoint" filename="langgraph_voice_agent.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_voice_agent.py" startline="361" type="function"></mcsymbol> and LLM setup <mcsymbol name="get_llm" filename="langgraph_voice_agent.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_voice_agent.py" startline="30" type="function"></mcsymbol>.
- Campaign UI/API: <mcfile name="campaign_server.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\campaign_server.py"></mcfile> (`/` UI via <mcsymbol name="index" filename="campaign_server.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\campaign_server.py" startline="102" type="function"></mcsymbol>, `/upload`, `/status`).
- Outbound call helper: <mcfile name="langgraph_make_call.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_make_call.py"></mcfile> (<mcsymbol name="make_travel_planning_call" filename="langgraph_make_call.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_make_call.py" startline="11" type="function"></mcsymbol>).
- Dependencies: <mcfile name="pyproject.toml" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\pyproject.toml"></mcfile>.
- Quick commands: <mcfile name="needed.txt" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\needed.txt"></mcfile>.

## Requirements
- Python 3.9–3.10
- `uv` (recommended) or `pip`
- LiveKit account (API key/secret, SIP trunk configured)
- Google API key for Gemini
- Optional: Cartesia account for TTS

## Environment Variables
Create `.env` from `.env.example` and fill values:
- `GOOGLE_API_KEY`: Google Generative AI key.
- `LIVEKIT_URL`: LiveKit API URL (Cloud: `https://api.livekit.cloud`; self-hosted: e.g. `http://localhost:7880`).
- `LIVEKIT_API_KEY`: LiveKit API key.
- `LIVEKIT_API_SECRET`: LiveKit API secret.
- `LIVEKIT_SIP_TRUNK_ID`: SIP trunk ID used for outbound dialing.
- `CARTESIA_API_KEY`: Cartesia TTS key (used by voice `entrypoint`).

Note: SIP trunk and Cartesia voice ID are hardcoded in code today. You can edit them in <mcfile name="langgraph_make_call.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_make_call.py"></mcfile> and <mcfile name="langgraph_voice_agent.py" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\langgraph_voice_agent.py"></mcfile> if you prefer env-driven config.

## Install & Run
Install using `uv` and run components.

```bash
uv run python langgraph_voice_agent.py start
```

```bash
uv run python langgraph_make_call.py
```

```bash
uv run python campaign_server.py
```

Optional console mode (agent):

```bash
uv run python langgraph_voice_agent.py console
```

## Using the Campaign UI
- Open `http://127.0.0.1:8000/`.
- Upload a CSV with header `phone` (also accepts `phone_number`, `number`, or first column).
- Numbers normalize to E.164 (prefixes with `+` if missing).
- UI shows total/completed/failed, progress bar, and per-number status: pending, running, done, failed.

Example CSV:
- <mcfile name="leads.csv" path="c:\Users\AMR\2025's Projects\Langgraph\LiveKit & Langgraph AI Agent__\leads.csv"></mcfile>

## Troubleshooting
- LiveKit credentials: Ensure `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` are set and `.env` is loaded.
- SIP trunk: Verify your `LIVEKIT_SIP_TRUNK_ID` is correct and outbound dialing is permitted.
- Phone format: Use `+<country_code><number>`.
- Windows kill stale python:

```bash
taskkill /IM python.exe /F
```

List Python processes:

```bash
tasklist | findstr python
```

## Notes
- LLM: The agent uses Gemini (`ChatGoogleGenerativeAI`) via `GOOGLE_API_KEY`.
- Plugins: STT (Deepgram), LLM (Google), TTS (Cartesia), noise cancellation via LiveKit plugins.
- Voice IDs: Cartesia voice ID is currently hardcoded in `entrypoint`; adjust as needed.

## Contact
- Maintainer: Amr Elhaweet
- Email: ellhaweet@gmail.com