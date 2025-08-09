# tts_engine.py
"""
TTS 합성 엔진 (XTTS v2)
- 참고 음성(voice_data)와 텍스트를 이용해 합성 오디오(wav bytes) 생성
- Vertex AI Job 1회 실행을 가정하여 모델을 모듈 전역에서 1회 로드
"""
import os
import tempfile
from typing import Optional

import soundfile as sf  # type: ignore
import numpy as np  # type: ignore

# Coqui TTS
from TTS.api import TTS  # type: ignore

# PyTorch safe globals (PyTorch 2.6+ weights_only behavior)
import torch  # type: ignore
try:
    from torch.serialization import add_safe_globals  # type: ignore

    # XTTS config classes
    for _mod, _name in [
        ("TTS.tts.configs.xtts_config", "XttsConfig"),
        ("TTS.tts.models.xtts", "XttsAudioConfig"),
        ("TTS.tts.models.xtts", "XttsTokenizerConfig"),
        ("TTS.tts.models.xtts", "XttsSpeakerEncoderConfig"),
        ("TTS.tts.models.xtts", "XttsVocoderConfig"),
        ("TTS.tts.models.xtts", "XttsArgs"),
    ]:
        try:
            _cls = __import__(_mod, fromlist=[_name]).__dict__.get(_name)
            if _cls is not None:
                add_safe_globals([_cls])
        except Exception:
            pass

    # Shared configs commonly referenced by checkpoints
    for _mod, _name in [
        ("TTS.config.shared_configs", "BaseDatasetConfig"),
        ("TTS.config.shared_configs", "AudioConfig"),
        ("TTS.config.shared_configs", "CharactersConfig"),
    ]:
        try:
            _cls = __import__(_mod, fromlist=[_name]).__dict__.get(_name)
            if _cls is not None:
                add_safe_globals([_cls])
        except Exception:
            pass

except Exception:
    pass

# GPU 사용 여부 자동 결정
_USE_CUDA = os.getenv("USE_CUDA", "1") == "1"
_DEVICE = "cuda" if _USE_CUDA else "cpu"

# 언어 기본값 (ko)
_DEFAULT_LANGUAGE = os.getenv("TTS_LANGUAGE", "ko")

# 모델 전역 로드 (첫 호출 시 로드)
_tts_model: Optional[TTS] = None

def _load_model_once() -> TTS:
    global _tts_model
    if _tts_model is None:
        # 멀티링구얼 XTTS v2 모델
        _tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(_DEVICE)
    return _tts_model


def synthesize(text: str, voice_data: bytes, language: Optional[str] = None) -> bytes:
    """
    텍스트와 참고 음성으로 합성 오디오(wav bytes)를 생성
    Args:
        text (str): 합성할 문장
        voice_data (bytes): 참고 음성 wav bytes
        language (str, optional): 언어 코드. 기본은 환경변수 TTS_LANGUAGE 또는 'ko'
    Returns:
        bytes: 합성된 wav 파일 바이너리
    """
    lang = language or _DEFAULT_LANGUAGE
    tts = _load_model_once()

    # 참고 음성 및 출력 임시 파일 경로
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_wav_path = os.path.join(tmpdir, "ref.wav")
        out_wav_path = os.path.join(tmpdir, "out.wav")

        # 참고 음성 저장
        with open(ref_wav_path, "wb") as f:
            f.write(voice_data)

        # 합성 수행 (파일 출력)
        # 참고: XTTS v2는 speaker_wav 인자로 참조 음성 파일 경로를 받음
        tts.tts_to_file(
            text=text,
            file_path=out_wav_path,
            speaker_wav=ref_wav_path,
            language=lang,
        )

        # 결과 wav를 bytes로 읽어 반환
        with open(out_wav_path, "rb") as f:
            return f.read()