from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from . import storage
from . import trigger_job
import uuid
import os
import logging
import io

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("voice-clone-api")

app = FastAPI()

class SynthesizeRequest(BaseModel):
    user_id: str
    text: str
    input_voice_gcs: Optional[str] = None  # voices/{user_id}/sample_xxx.wav

@app.post("/upload-voice")
async def upload_voice(user_id: str = Form(...), file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        file_id = str(uuid.uuid4())
        gcs_path = f"voices/{user_id}/sample_{file_id}.wav"
        gcs_url = storage.upload_to_gcs(gcs_path, file_bytes, content_type=file.content_type or "audio/wav")
        logger.info("uploaded voice user_id=%s blob=%s", user_id, gcs_path)
        return {"message": "Voice uploaded", "user_id": user_id, "gcs_url": gcs_url, "blob": gcs_path}
    except Exception as e:
        logger.exception("/upload-voice failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    try:
        if not req.input_voice_gcs:
            return JSONResponse(status_code=400, content={"error": "input_voice_gcs is required"})
        result_blob = f"results/{req.user_id}/result_{uuid.uuid4().hex}.wav"
        logger.info("triggering job user_id=%s input=%s output=%s", req.user_id, req.input_voice_gcs, result_blob)
        job_name, output_blob = trigger_job.trigger_vertex_job(
            user_id=req.user_id,
            text=req.text,
            input_voice_gcs=req.input_voice_gcs,
            output_gcs=result_blob,
            use_gpu=True,
        )
        try:
            signed_url = storage.generate_signed_url(output_blob)
        except Exception as e:
            logger.warning("signed url failed, will rely on proxy endpoint: %s", e)
            signed_url = None
        logger.info("job submitted name=%s output_blob=%s", job_name, output_blob)
        return {
            "message": "Synthesis requested",
            "job": job_name,
            "result_blob": output_blob,
            "result_gs_url": f"gs://{storage.GCS_BUCKET_NAME}/{output_blob}",
            "result_signed_url": signed_url,
            "proxy_stream_url": f"/results/stream?blob={output_blob}",
            "signed_url_ttl_seconds": storage.SIGNED_URL_TTL_SECONDS if signed_url else None,
        }
    except Exception as e:
        logger.exception("/synthesize failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/results/stream")
async def stream_result(blob: str):
    try:
        if not storage.exists(blob):
            return JSONResponse(status_code=404, content={"error": "result not ready or not found", "blob": blob})
        data = storage.download_from_gcs(blob)
        return StreamingResponse(io.BytesIO(data), media_type="audio/wav", headers={"Content-Disposition": f"inline; filename={os.path.basename(blob)}"})
    except Exception as e:
        logger.exception("/results/stream failed: %s", e)
        return JSONResponse(status_code=404, content={"error": str(e)})