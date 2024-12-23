from ninja import Router, File, Form
from ninja.files import UploadedFile
from deepface import DeepFace
import cv2
import numpy as np
from database.client import supabase

router = Router()

@router.post("")
def createFaces(request, name: Form[str], image: UploadedFile = File(...)):
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
        supabase.table("avatar_images")
        .insert({
            "name": name,
            "embedding": embedding
        })
        .execute()
    )

    return {"response": response}

@router.post("/recognize")
def recognizeAvatar(request, image: UploadedFile = File(...)):
    # Convert the uploaded file to a numpy array
    file_bytes = np.frombuffer(image.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    embedding_objects = DeepFace.represent(
        img_path = img,
        model_name = "Facenet",
        detector_backend = "mtcnn"
    )
    
    embedding = embedding_objects[0]["embedding"]

    response = supabase.rpc("recognize_face", {
        "query_embedding": embedding,
        "threshold": 0.6,
        "take": 1
    }).execute()

    return {"response": response}