from ninja import Router
from database.client import supabase
from .schema import CreateGameSchema
from datetime import timedelta

router = Router()

@router.post("")
def createGame(request, data: CreateGameSchema):
    user = request.auth

    starts_at = data.starts_at
    ends_at = starts_at + timedelta(minutes=60)

    game = (
        supabase.table("games")
        .insert({
            "owner_user_id": user.id,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        })
        .execute()
    )

    return {"game": game}

@router.post("/{game_id}/join")
def createGame(request, game_id: int):
    user = request.auth

    game = supabase.table("games").select("id").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}

    player = supabase.table("players").select("id").eq("game_id", game_id).eq("user_id", user.id).maybe_single().execute()
    if player:
        return {"error": "Player already joined"}
        
    player = (
        supabase.table("players")
        .insert({
            "game_id": game_id,
            "user_id": user.id,
        })
        .execute()
    )

    return {"player": player}