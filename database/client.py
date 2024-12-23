import os
from supabase import create_client, Client

from dotenv import load_dotenv
load_dotenv()

url: str = os.getenv("DATABASE_URL")
key: str = os.getenv("DATABASE_KEY")
supabase: Client = create_client(url, key)
