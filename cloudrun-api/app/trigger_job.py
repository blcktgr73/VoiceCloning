# trigger_job.py
"""
Vertex AI Custom Job 트리거 유틸리티
"""
import os
# from google.cloud import aiplatform  # TODO: 실제 사용 시 주석 해제

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "your-gcp-project")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_JOB_NAME = os.getenv("VERTEX_JOB_NAME", "your-vertex-job")


def trigger_vertex_job(user_id: str, text: str) -> str:
    """
    Vertex AI Custom Job을 트리거하여 TTS 합성 요청
    Args:
        user_id (str): 사용자 ID
        text (str): 합성할 텍스트
    Returns:
        str: 결과 오디오 파일의 GCS URL (또는 Job ID)
    """
    try:
        # TODO: google-cloud-aiplatform 사용하여 Custom Job 실행
        # aiplatform.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
        # job = aiplatform.CustomJob(...)
        # job.run(...)
        # 결과 GCS URL 또는 Job ID 반환
        return "https://dummy-result-url/"  # 임시 반환값
    except Exception as e:
        # TODO: 로깅 추가
        raise RuntimeError(f"Vertex AI Job 트리거 실패: {e}")