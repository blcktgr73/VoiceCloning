# storage.py
"""
Google Cloud Storage 연동 유틸리티
"""
import os
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket")

# TODO: 서비스 계정 키 파일 경로 환경변수로 지정 필요 (로컬 테스트 시)


def upload_to_gcs(destination_blob_name: str, file_data: bytes, content_type: str = "audio/wav") -> str:
    """
    GCS에 파일 업로드
    Args:
        destination_blob_name (str): GCS 내 저장 경로 (예: voices/user_id/sample.wav)
        file_data (bytes): 업로드할 파일 데이터
        content_type (str): 파일 Content-Type
    Returns:
        str: 업로드된 GCS 파일의 public URL
    """
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_data, content_type=content_type)
        # TODO: 필요시 blob.make_public() 호출
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except GoogleAPIError as e:
        # TODO: 로깅 추가
        raise RuntimeError(f"GCS 업로드 실패: {e}")

def download_from_gcs(blob_name: str) -> bytes:
    """
    GCS에서 파일 다운로드
    Args:
        blob_name (str): GCS 내 파일 경로
    Returns:
        bytes: 파일 데이터
    """
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    except GoogleAPIError as e:
        # TODO: 로깅 추가
        raise RuntimeError(f"GCS 다운로드 실패: {e}")