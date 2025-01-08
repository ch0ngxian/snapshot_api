import random
from ninja import Router, File, Form
from ninja.files import UploadedFile
from deepface import DeepFace
import cv2
import numpy as np
from database.client import supabase
from datetime import datetime, timedelta
from .schema import JoinGameSchema

router = Router()

@router.post("")
def createGame(request):
    user = request.auth

    while True:
        code = random.randrange(111111, 999999, 6)
        game = supabase.table("games").select("id").eq("code", code).maybe_single().execute()

        if not game:
            break

    game = (
        supabase.table("games")
        .insert({
            "owner_user_id": user.id,
            "code": code
        })
        .execute()
    )

    game = game.data[0]

    player_name = user.user_metadata.get('nickname') or user.user_metadata.get('full_name') or user.email

    player = (
        supabase.table("players")
        .insert({
            "game_id": game['id'],
            "user_id": user.id,
            "name": player_name,
        })
        .execute()
    )

    return {"game": game}

@router.post("/join")
def joinGame(request, data: JoinGameSchema):
    user = request.auth
    code = data.code

    game = supabase.table("games").select("id, is_started").eq("code", code).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}

    game = game.data
    game_id = game['id']

    player = supabase.table("players").select("id").eq("game_id", game_id).eq("user_id", user.id).maybe_single().execute()
    if player:
        # Player already joined
        return {"game": game}
        
    player_name = user.user_metadata.get('nickname') or user.user_metadata.get('full_name') or user.email

    player = (
        supabase.table("players")
        .insert({
            "game_id": game_id,
            "user_id": user.id,
            "name": player_name,
        })
        .execute()
    )

    return {"game": game}

@router.get("/{game_id}")
def retrieveGame(request, game_id: int):
    game = supabase.table("games").select("*").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}

    return {"game": game.data}

@router.get("/{game_id}/current_player")
def retrieveCurrentPlayer(request, game_id: int):
    user = request.auth

    game = supabase.table("games").select("*").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}

    player = supabase.table("players").select("*").eq("game_id", game_id).eq("user_id", user.id).maybe_single().execute()

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
    
    # Check for empty embeddings
    for face in staged_player_faces:
        if not face.get('embedding'):
            return {"error": "Cannot start game, some players not setup faces yet"}

    supabase.table("player_faces").insert(staged_player_faces).execute()

    starts_at = datetime.now()
    ends_at = datetime.now() + timedelta(minutes=60)

    game = (
        supabase.table("games")
        .update({
            "is_started": True,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        })
        .eq("id", game_id)
        .execute()
    )

    return {"game": game.data}

@router.get("/{game_id}/players")
def listPlayer(request, game_id: int):
    game = supabase.table("games").select("*").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}
    
    players = supabase.table("players").select("*").eq("game_id", game_id).execute()

    return {"players": players.data}

@router.post("/{game_id}/shoot")
def shootPlayer(request, game_id: int, image: UploadedFile = File(...)):
    user = request.auth

    game = supabase.table("games").select("*").eq("id", game_id).maybe_single().execute()
    if not game:
        return {"error": "Game not found"}
    
    action_player = supabase.table("players").select("*").eq("game_id", game_id).eq("user_id", user.id).maybe_single().execute()
    if not action_player:
        return {"error": "Player not in game"}

    # Convert the uploaded file to a numpy array
    file_bytes = np.frombuffer(image.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    try:
        embedding_objects = DeepFace.represent(
            img_path = img,
            model_name = "Facenet",
            detector_backend = "mtcnn"
        )
    except Exception as e:
        return {"message": "No face detected", "error": str(e)}
    
    embedding = embedding_objects[0]["embedding"]

    response = supabase.rpc("recognize_players_face", {
        "query_game_id": game_id,
        "query_embedding": embedding,
        "threshold": 0.6,
        "take": 1
    }).maybe_single().execute()

    live = 1
    score = 100

    player_face = response.data
    if not player_face:
        return {"error": "No player shooted"}
    
    target_player = supabase.table("players").select("*").eq("id", player_face['player_id']).maybe_single().execute()

    # Reduce live
    if target_player:
        target_player = target_player.data

        target_player = (
            supabase.table("players")
            .update({
                "total_lives": target_player['total_lives'] - live
            })
            .eq("id", target_player['id'])
            .execute()
        )

        target_player = target_player.data[0]

    # Increase score
    if action_player:
        action_player = action_player.data
        
        action_player = (
            supabase.table("players")
            .update({
                "total_scores": action_player['total_scores'] + score
            })
            .eq("id", action_player['id'])
            .execute()
        )

        action_player = action_player.data[0]

    # Insert score events
    score_event = (
        supabase.table("game_score_events")
        .insert({
            "game_id": game_id,
            "action_player_id": action_player['id'],
            "target_player_id": target_player['id'],
            "lives_reduced": live,
            "scores_awarded": score
        })
        .execute()
    )

    return {"score_event": score_event.data[0]}
