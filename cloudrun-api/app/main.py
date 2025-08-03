from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from . import storage
from . import trigger_job
import uuid

app = FastAPI()

@app.post("/upload-voice")
async def upload_voice(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    사용자의 음성 파일을 업로드하고 GCS에 저장합니다.
    """
    try:
        file_bytes = await file.read()
        # GCS 경로: voices/{user_id}/sample_{uuid}.wav
        file_id = str(uuid.uuid4())
        gcs_path = f"voices/{user_id}/sample_{file_id}.wav"
        gcs_url = storage.upload_to_gcs(gcs_path, file_bytes, content_type=file.content_type or "audio/wav")
        return {"message": "Voice uploaded", "user_id": user_id, "gcs_url": gcs_url}
    except Exception as e:
        # TODO: 로깅 추가
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/synthesize")
async def synthesize(user_id: str, text: str):
    """
    Vertex AI Custom Job을 트리거하여 TTS 합성을 요청합니다.
    """
    try:
        result_url = trigger_job.trigger_vertex_job(user_id, text)
        return {"message": "Synthesis requested", "user_id": user_id, "text": text, "result_url": result_url}
    except Exception as e:
        # TODO: 로깅 추가
        return JSONResponse(status_code=500, content={"error": str(e)})