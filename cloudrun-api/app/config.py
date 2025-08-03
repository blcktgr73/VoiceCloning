# config.py
"""
환경설정 모듈 (Stub)
TODO: 실제 환경변수/설정값 로딩 구현 필요
"""

import os
# from google.cloud import aiplatform  # TODO: 실제 사용 시 주석 해제

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "your-gcp-project")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_JOB_NAME = os.getenv("VERTEX_JOB_NAME", "your-vertex-job")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "gcs-bucket-name")

