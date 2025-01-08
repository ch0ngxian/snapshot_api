from datetime import datetime
from ninja import Router, File, Form
from ninja.files import UploadedFile
from deepface import DeepFace
import cv2
import numpy as np
from database.client import supabase

router = Router()

@router.get("")
def listFaces(request):
    user = request.auth

    faces = supabase.table("faces").select("*").eq("user_id", user.id).execute()

    return {"faces": faces.data}


@router.get("/count")
def countFaces(request):
    user = request.auth

    face_count = supabase.table("faces").select("count", count="exact").eq("user_id", user.id).execute()

    return {"count": face_count.count}

@router.post("")
def createFace(request, image: UploadedFile = File(...)):
    user = request.auth

    image_content = image.read()
    # Convert the uploaded file to a numpy array
    file_bytes = np.frombuffer(image_content, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    embedding_objects = DeepFace.represent(
        img_path = img,
        model_name = "Facenet",
        detector_backend = "mtcnn"
    )
    
    embedding = embedding_objects[0]["embedding"]
    
    response = (
        supabase.table("faces")
        .insert({
            "user_id": user.id,
            "embedding": embedding
        })
        .execute()
    )

    storage_response = supabase.storage.from_("snapshot").upload(
        path=f"faces/{image.name}",
        file=image_content,
        file_options={"content-type": image.content_type, "cache-control": "3600", "upsert": "true"},
    )

    avatar_url = supabase.storage.from_("snapshot").get_public_url(
        storage_response.path
    )

    update_avatar_response = supabase.auth.update_user({
        "data": {"avatar_url": avatar_url}
    })

    print(update_avatar_response)
    
    face = response.data[0]

    return {"face": face}

@router.post("speedtest")
def speedTest(request, image: UploadedFile = File(...)):

    current_time1 = datetime.now()
    # Convert the uploaded file to a numpy array
    file_bytes = np.frombuffer(image.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    elapsed_time1 = datetime.now() - current_time1

    current_time2 = datetime.now()
    embedding_objects = DeepFace.represent(
        img_path = img,
        model_name = "Facenet",
        detector_backend = "mtcnn"
    )
    
    embedding = embedding_objects[0]["embedding"]
    elapsed_time2 = datetime.now() - current_time2
    
    return {"elapsed_time1": elapsed_time1.total_seconds(), "elapsed_time2": elapsed_time2.total_seconds()}

@router.post("/recognize")
def recognizeAvatar(request, image: UploadedFile = File(...)):
    user = request.auth

    # Convert the uploaded file to a numpy array
    file_bytes = np.frombuffer(image.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    embedding_objects = DeepFace.represent(
        img_path = img,
        model_name = "Facenet",
        detector_backend = "mtcnn"
    )
    
    embedding = embedding_objects[0]["embedding"]

    response = supabase.rpc("recognize_user_face", {
        "query_user_id": user.id,
        "query_embedding": embedding,
        "threshold": 0.6,
        "take": 1
    }).execute()

    if response.data:
        return {"status": True}
    else:
        return {"error": "No matching face found"}