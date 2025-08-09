# run_batch.py
"""
Vertex AI Custom Job 진입점
- GCS에서 입력(음성, 텍스트) 읽기
- TTS 합성
- 결과 GCS 저장
- 결과 URL 출력
"""
import sys
import argparse
import storage
import tts_engine
import config

def main():
    parser = argparse.ArgumentParser(description="Vertex TTS Batch Job")
    parser.add_argument('--user_id', type=str, required=True, help='사용자 ID')
    parser.add_argument('--text', type=str, required=True, help='합성할 텍스트')
    parser.add_argument('--input_voice_gcs', type=str, required=True, help='입력 음성 GCS 경로')
    parser.add_argument('--output_gcs', type=str, required=True, help='결과 저장 GCS 경로')
    args = parser.parse_args()

    # 1. 입력 음성 다운로드
    voice_data = storage.download_from_gcs(args.input_voice_gcs)
    # 2. TTS 합성
    audio_data = tts_engine.synthesize(args.text, voice_data)
    # 3. 결과 업로드
    result_url = storage.upload_to_gcs(args.output_gcs, audio_data, content_type="audio/wav")
    print(f"RESULT_URL={result_url}")

if __name__ == "__main__":
    main()