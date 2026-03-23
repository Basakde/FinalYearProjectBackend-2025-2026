import os
from supabase import create_client

# Read environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing Supabase env vars")

# Create Supabase backend client
# This uses the service role key so it must only run on backend
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)