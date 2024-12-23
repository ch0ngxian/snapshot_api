from ninja import NinjaAPI
from ninja.security import APIKeyHeader
from database.client import supabase

class Auth(APIKeyHeader):
    param_name = "SS-Access-Token"

    def authenticate(self, request, key):
        response = supabase.auth.get_user(key)
        if response and response.user:
            return response.user
        
api = NinjaAPI()

try:
    print('Trying to add router...')
    api.add_router("/auth/", "auth.api.router", auth=Auth())
    api.add_router("/faces/", "faces.api.router", auth=Auth())
    api.add_router("/games/", "games.api.router", auth=Auth())
except Exception as e:
    print('Error in router..')
    print(e)