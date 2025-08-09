# storage.py
"""
Google Cloud Storage 입출력 유틸리티 (Stub)
TODO: 실제 GCS 연동 코드 구현 필요
"""
import os
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket")

def upload_to_gcs(destination_blob_name: str, file_data: bytes, content_type: str = "audio/wav") -> str:
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_data, content_type=content_type)
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except GoogleAPIError as e:
        raise RuntimeError(f"GCS 업로드 실패: {e}")

def download_from_gcs(blob_name: str) -> bytes:
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    except GoogleAPIError as e:
        raise RuntimeError(f"GCS 다운로드 실패: {e}")