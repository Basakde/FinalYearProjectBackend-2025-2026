# FinalYearProjectBackend-2025-2026
FinalYearProjectBackend-2025/2026

#backend/README.md


# Smart Wardrobe Assistant – Backend (FastAPI)

This is the backend service for the Smart Wardrobe Assistant, built using FastAPI and Python.  
It provides API endpoints for user management, wardrobe items, background removal (U²-Net), image features retrieval, and weather-based outfit suggestions.  
The backend also connects to Supabase (PostgreSQL) for data storage,authentication and table management.


# Project Structure

backend/
│
├── app/
│ ├── api/ # API layer (FastAPI routes)
│ ├── services/ # Business logic and SQL queries
│ ├── models/ # Pydantic models and schemas
│ ├── utils/ # Utility functions
│ ├── helpers/ # Helper functions
│ ├── test/ # Unit tests
│ └── db/ # Database connection logic
│
├── main.py # Entry point – starts FastAPI app
├── requirements.txt # Backend dependencies
└── .env # Environment variables (URLs and API Keys )

# Create virtual environment 

python -m venv venv 

# Activate the virtual environment

Windows: venv\Scripts\activate
Mac/Linux: source venv/bin/activate

# Install dependencies

pip install -r requirement.txt

# Environment Variables (.env)
Create a .env file in your backend/ folder with:

SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL
OPENWEATHER_API_KEY
VERTEX_API_KEY
GOOGLE_CLOUD_PROJECT
GOOGLE_CLOUD_LOCATION
DEFAULT_URL

# API Documentation

Swagger UI: http://127.0.0.1:8000/docs

#  Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload  





