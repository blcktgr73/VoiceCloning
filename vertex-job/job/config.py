# config.py
"""
환경설정 모듈 (Stub)
TODO: 실제 환경변수/설정값 로딩 구현 필요
"""
import os

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket")
# TODO: 기타 환경변수 추가