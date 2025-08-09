# 🎙️ Voice Cloning TTS API

Google Cloud 기반의 **사용자 음성 클로닝 및 TTS(텍스트-투-스피치)** 서비스입니다.
사용자 음성을 업로드하면, 해당 목소리로 텍스트를 합성하여 오디오를 생성합니다.

---

## ✨ 주요 기능

* **FastAPI + Cloud Run**: 음성 업로드(`/upload-voice`) 및 합성 요청(`/synthesize`) API 제공
* **Google Cloud Storage(GCS)**: 원본 음성 및 합성 결과 저장
* **Vertex AI Custom Job**: GPU 환경에서 XTTS 기반 음성 합성 실행
* **스트리밍/다운로드 지원**: 결과 오디오를 브라우저로 재생하거나 파일로 다운로드 가능
* **확장 가능 구조**: 인증(Firebase Auth/IAM), 모니터링, CI/CD 적용 가능

---

## 🛠 아키텍처

1. **Cloud Run (FastAPI)**

   * 음성 업로드 → GCS 저장
   * 합성 요청 → Vertex AI Job 트리거
2. **Vertex AI Custom Job**

   * XTTS 모델로 음성 합성
   * 결과 오디오를 GCS에 저장
3. **GCS**

   * `/voices/{user_id}/…` : 업로드 음성
   * `/results/{user_id}/…` : 합성 결과

---

## 🚀 배포 가이드

### 1. GCP 리소스 준비

* **필수 API 활성화**: Cloud Run, Cloud Storage, Artifact Registry, Vertex AI, Cloud Logging
* **서비스 계정 권한 부여**:

  * Cloud Run SA → `roles/aiplatform.user`
  * Vertex AI Job SA → GCS `objectViewer` + `objectCreator`

### 2. GCS 버킷 생성

```sh
gsutil mb -l asia-northeast3 gs://voice-storage-asia3-<id>
```

### 3. 이미지 빌드 & 푸시

* **Cloud Run API**

```sh
gcloud builds submit --config=cloudbuild.yaml . --project=<PROJECT_ID>
```

* **Vertex Job**

```sh
gcloud builds submit vertex-job \
  --tag=asia-northeast3-docker.pkg.dev/<PROJECT_ID>/vertex-job/vertex-job:latest \
  --project=<PROJECT_ID>
```

### 4. Cloud Run 배포

```sh
gcloud run deploy voice-clone-api \
  --image=asia-northeast3-docker.pkg.dev/<PROJECT_ID>/voice-clone-api/voice-clone-api:latest \
  --region=asia-northeast3 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=cloud-run-sa@<PROJECT_ID>.iam.gserviceaccount.com \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=<PROJECT_ID>,BUCKET_NAME=<BUCKET_NAME>
```

---

## 📡 API 사용 예시

### 1. 음성 업로드

```sh
curl -X POST "https://<CLOUD_RUN_URL>/upload-voice" \
  -F "user_id=testuser" \
  -F "file=@sample.wav"
```

응답:

```json
{
  "message": "Voice uploaded",
  "user_id": "testuser",
  "blob": "voices/testuser/sample_xxx.wav",
  "gcs_url": "gs://bucket/voices/testuser/sample_xxx.wav"
}
```

### 2. 음성 합성

```sh
curl -X POST "https://<CLOUD_RUN_URL>/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"testuser","text":"안녕하세요","input_voice_gcs":"voices/testuser/sample_xxx.wav"}'
```

응답:

```json
{
  "message": "Synthesis requested",
  "job": "projects/.../customJobs/...",
  "result_blob": "results/testuser/result_xxx.wav",
  "result_gs_url": "gs://bucket/results/testuser/result_xxx.wav",
  "proxy_stream_url": "/results/stream?blob=results/testuser/result_xxx.wav"
}
```

### 3. 결과 재생/다운로드

* 브라우저: `https://<CLOUD_RUN_URL>/results/stream?blob=results/testuser/result_xxx.wav`
* CLI:

```sh
curl -L "https://<CLOUD_RUN_URL>/results/stream?blob=..." -o result.wav
```

---

## 🔒 보안 & 확장

* **인증**: Firebase Auth, IAM, API Key 등 선택 적용
* **모니터링**: Cloud Logging & Error Reporting
* **CI/CD**: Cloud Build + GitHub Actions

---

## 📌 참고

* Vertex AI Job 실행 시 `COQUI_TOS_AGREED=1` 환경변수 필요
* 결과 파일명은 UUID 기반으로 생성되어 충돌 방지
* PyTorch 2.6+ 사용 시 `weights_only` 관련 호환성 주의
