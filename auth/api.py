from ninja import Router
from database.client import supabase
from .schema import LoginSchema

router = Router()

@router.post('/login', auth=None)
def login(request, data: LoginSchema):
    response = supabase.auth.sign_in_with_password(
        {"email": data.email, "password": data.password}
    )
    if response.session:
        return {"session": response.session}
    return {"error": "Invalid login credentials"}