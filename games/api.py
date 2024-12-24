from ninja import Router
from database.client import supabase
from datetime import datetime, timedelta

router = Router()

@router.post("")
def createGame(request):
    user = request.auth

    game = (
        supabase.table("games")
        .insert({
            "owner_user_id": user.id
        })
        .execute()
    )

    game = game.data

    player = (
        supabase.table("players")
        .insert({
            "game_id": game['id'],
            "user_id": user.id,
        })
        .execute()
    )

    return {"game": game}

@router.post("/{game_id}/join")
def joinGame(request, game_id: int):
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

    return {"player": player.data}

@router.post("/{game_id}/start")
def startGame(request, game_id: int):
    game = supabase.table("games").select("*").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}

    game = game.data

    if game['starts_at']:
        return {"error": "Game already started"}
    
    response = supabase.rpc("list_staged_player_faces", {
        "query_game_id": game_id,
    }).execute()
    
    staged_player_faces = response.data
    supabase.table("player_faces").insert(staged_player_faces).execute()

    starts_at = datetime.now()
    ends_at = datetime.now() + timedelta(minutes=60)

    game = (
        supabase.table("games")
        .update({
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        })
        .eq("id", game_id)
        .execute()
    )

    return {"game": game.data}