#!/usr/bin/env python3
"""
Configuration module for Micro SDLC Agent
Central location for application-wide settings and constants
"""

from pathlib import Path

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Get the backend directory (config.py is now in backend/modules/)
BACKEND_DIR = Path(__file__).parent.parent.resolve()

# Default codebase path for agents to work within
# Points to the micro SDLC application root (apps/custom_7_micro_sdlc_agent/)
# This allows agents to work on both frontend and backend code
DEFAULT_CODEBASE_PATH = str(BACKEND_DIR.parent)

# Explanation:
# - From backend/, we go up one level (..) to reach apps/custom_7_micro_sdlc_agent/
# - This gives agents access to:
#   - frontend/ (Vue.js application)
#   - backend/ (FastAPI server, database, agents)
#   - Any other app-level directories
# - Users can override this when creating tickets from the frontend
# - Using absolute path for consistency across different working directories

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Directory names for agent outputs (relative to agent's codebase_path)
# These will be created inside the codebase the agent is working on
PLAN_DIRECTORY = "specs"
REVIEW_DIRECTORY = "reviews"

# Default model for agents
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Available models
AVAILABLE_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-1-20250805"
]

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database file location
DATABASE_NAME = "sdlc.db"