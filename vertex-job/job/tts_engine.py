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
import librosa  # type: ignore

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

# 리퍼런스 전처리 파라미터
_REF_SR = int(os.getenv("TTS_REF_SR", "16000"))
_REF_TRIM = os.getenv("TTS_REF_TRIM", "1") == "1"
_REF_NORM = os.getenv("TTS_REF_NORM", "1") == "1"

# 모델 전역 로드 (첫 호출 시 로드)
_tts_model: Optional[TTS] = None

def _load_model_once() -> TTS:
    global _tts_model
    if _tts_model is None:
        _tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(_DEVICE)
    return _tts_model


def _preprocess_reference(in_path: str) -> None:
    """Resample to mono 16kHz, trim silence, normalize, overwrite in place."""
    wav, sr = librosa.load(in_path, sr=_REF_SR, mono=True)
    orig_duration = wav.shape[0] / float(_REF_SR)
    if _REF_TRIM:
        wav, _ = librosa.effects.trim(wav, top_db=25)
    if _REF_NORM and np.max(np.abs(wav)) > 0:
        wav = 0.97 * wav / np.max(np.abs(wav))
    sf.write(in_path, wav, _REF_SR)
    print(f"[XTTS] Ref preprocessed: sr={_REF_SR}, duration={orig_duration:.2f}s -> {wav.shape[0]/_REF_SR:.2f}s")


def synthesize(text: str, voice_data: bytes, language: Optional[str] = None) -> bytes:
    lang = language or _DEFAULT_LANGUAGE
    tts = _load_model_once()

    with tempfile.TemporaryDirectory() as tmpdir:
        ref_wav_path = os.path.join(tmpdir, "ref.wav")
        out_wav_path = os.path.join(tmpdir, "out.wav")

        with open(ref_wav_path, "wb") as f:
            f.write(voice_data)

        # 참고 음성 전처리(모노/16k/트림/정규화)
        _preprocess_reference(ref_wav_path)

        # 합성 수행 (파일 출력)
        tts.tts_to_file(
            text=text,
            file_path=out_wav_path,
            speaker_wav=ref_wav_path,
            language=lang,
        )

        with open(out_wav_path, "rb") as f:
            return f.read()