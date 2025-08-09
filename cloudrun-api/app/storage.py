# storage.py
"""
Google Cloud Storage 연동 유틸리티
"""
import os
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from datetime import timedelta

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket")
SIGNED_URL_TTL_SECONDS = int(os.getenv("SIGNED_URL_TTL_SECONDS", "3600"))
SIGNED_URL_SA_EMAIL = os.getenv("SIGNED_URL_SERVICE_ACCOUNT_EMAIL")  # optional

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


def exists(blob_name: str) -> bool:
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False


def generate_signed_url(blob_name: str, ttl_seconds: int | None = None) -> str:
    """
    지정한 객체에 대한 V4 서명 URL 생성
    Cloud Run 등에서 프라이빗 키가 없을 경우, IAM Credentials SignBlob을 활용하기 위해
    service_account_email을 전달할 수 있음.
    """
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        expires = timedelta(seconds=ttl_seconds or SIGNED_URL_TTL_SECONDS)
        if SIGNED_URL_SA_EMAIL:
            url = blob.generate_signed_url(
                version="v4",
                expiration=expires,
                method="GET",
                service_account_email=SIGNED_URL_SA_EMAIL,
            )
        else:
            url = blob.generate_signed_url(version="v4", expiration=expires, method="GET")
        return url
    except Exception as e:
        raise RuntimeError(f"Signed URL 생성 실패: {e}")