# trigger_job.py
"""
Vertex AI Custom Job 트리거 유틸리티
"""
import os
from typing import Tuple
from google.cloud import aiplatform
from google.cloud import aiplatform_v1
from google.api_core.client_options import ClientOptions

VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "your-gcp-project")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "asia-northeast3")
VERTEX_JOB_NAME = os.getenv("VERTEX_JOB_NAME", "xtts-job-v1")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "your-gcs-bucket")

# Vertex Job 컨테이너 이미지 (Artifact Registry)
VERTEX_JOB_IMAGE_URI = os.getenv(
    "VERTEX_JOB_IMAGE_URI",
    f"asia-northeast3-docker.pkg.dev/{VERTEX_PROJECT}/vertex-job/vertex-job:latest",
)

# Staging bucket (옵션)
VERTEX_STAGING_BUCKET = os.getenv("VERTEX_STAGING_BUCKET", f"gs://{GCS_BUCKET_NAME}")


def trigger_vertex_job(
    user_id: str,
    text: str,
    input_voice_gcs: str,
    output_gcs: str,
    use_gpu: bool = True,
) -> Tuple[str, str]:
    """
    Vertex AI Custom Job을 트리거하여 TTS 합성 요청
    Returns:
        (job_resource_name, output_gcs)
    """
    # aiplatform init (옵션적으로 staging bucket 지정)
    aiplatform.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION, staging_bucket=VERTEX_STAGING_BUCKET)

    machine_spec = {"machine_type": "n1-standard-4"}
    if use_gpu:
        machine_spec.update(
            {
                "accelerator_type": "NVIDIA_TESLA_T4",
                "accelerator_count": 1,
            }
        )

    worker_pool_specs = [
        {
            "machine_spec": machine_spec,
            "replica_count": 1,
            "container_spec": {
                "image_uri": VERTEX_JOB_IMAGE_URI,
                "command": ["python3", "job/run_batch.py"],
                "args": [
                    f"--user_id={user_id}",
                    f"--text={text}",
                    f"--input_voice_gcs={input_voice_gcs}",
                    f"--output_gcs={output_gcs}",
                ],
                "env": [
                    {"name": "GCS_BUCKET_NAME", "value": GCS_BUCKET_NAME},
                    {"name": "VERTEX_PROJECT", "value": VERTEX_PROJECT},
                    {"name": "VERTEX_JOB_NAME", "value": VERTEX_JOB_NAME},
                    {"name": "COQUI_TOS_AGREED", "value": "1"},
                ],
            },
        }
    ]

    # 지역 엔드포인트 사용 설정 (예: asia-northeast3-aiplatform.googleapis.com)
    api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
    client = aiplatform_v1.JobServiceClient(client_options=ClientOptions(api_endpoint=api_endpoint))
    parent = f"projects/{VERTEX_PROJECT}/locations/{VERTEX_LOCATION}"
    custom_job = {
        "display_name": VERTEX_JOB_NAME,
        "job_spec": {
            "worker_pool_specs": worker_pool_specs,
        },
    }
    response = client.create_custom_job(parent=parent, custom_job=custom_job)
    return response.name, output_gcs