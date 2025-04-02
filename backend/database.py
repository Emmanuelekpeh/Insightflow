import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY: str = os.environ.get("SUPABASE_ANON_KEY")

# Check if environment variables are loaded
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and Key must be set in the environment variables (.env file)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_db_client() -> Client:
    """Dependency function to get the Supabase client."""
    return supabase

print("Supabase client initialized successfully.")
# You can add a simple test query here if needed, e.g.:
# try:
#     response = supabase.table('your_table_name').select('*', count='exact').execute()
#     print("Supabase connection test successful:", response)
# except Exception as e:
#     print(f"Supabase connection test failed: {e}") 