# Character-AI Backend (FastAPI)

This repository contains a production-ready FastAPI backend for the Character-AI multi-agent system.

**Notebook source (RAG / agent prototyping):** `/mnt/data/character-ai.ipynb`

## Quickstart

1. Create a virtualenv and activate it.
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - `GOOGLE_API_KEY` (Gemini API key)
   - `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`
   - `JWT_SECRET`
4. Run: `uvicorn main:app --reload`
5. Open docs: `http://127.0.0.1:8000/docs`

## What is included
- `main.py` - API endpoints
- `agents.py` - Multi-agent pipeline using Gemini
- `database.py` - MySQL connector
- `models.py` - Pydantic models
- `utils.py` - Auth helpers (JWT, hashing)

## Notes
- **Do not include API keys or secrets in the repo.**
- The notebook at `/mnt/data/character-ai.ipynb` contains the original prototypes and tests.