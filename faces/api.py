from ninja import Router, File, Form
from ninja.files import UploadedFile
from deepface import DeepFace
import cv2
import numpy as np
from database.client import supabase

router = Router()

@router.post("")
def createFaces(request, image: UploadedFile = File(...)):
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
    
    response = (
        supabase.table("faces")
        .insert({
            "user_id": user.id,
            "embedding": embedding
        })
        .execute()
    )

    return {"response": response}

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

    return {"response": response}