"""
Audio handling component using Streamlit-WebRTC (audio only)
"""
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import numpy as np
import queue
from typing import Any, Optional

# WebRTC ICE servers configuration
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)


class AudioRecorder:
    """Handle audio recording via WebRTC"""

    def __init__(self):
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._is_recording = False

    def audio_frame_callback(self, frame: av.AudioFrame) -> av.AudioFrame:
        """Callback to collect audio frames when recording."""
        if self._is_recording:
            arr = frame.to_ndarray()  # shape: (channels, samples)
            self._audio_queue.put(arr)
        return frame

    def create_streamer(self, key: str):
        """Instantiate the WebRTC audio-only streamer."""
        return webrtc_streamer(
            key=key,
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"audio": True, "video": False},
            audio_frame_callback=self.audio_frame_callback,
            async_processing=True,
        )

    def start(self):
        """Begin recording: clear queue and flag recording on."""
        self._is_recording = True
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def stop_and_get(self) -> Optional[np.ndarray]:
        """Stop recording and return concatenated audio or None."""
        self._is_recording = False
        frames = []
        while not self._audio_queue.empty():
            try:
                frames.append(self._audio_queue.get_nowait())
            except queue.Empty:
                break

        if not frames:
            return None

        # Concatenate along the samples axis
        return np.concatenate(frames, axis=-1)


def create_playback(audio_data: Any):
    """
    Utility to play back audio_data (numpy array).
    Returns True if playback was rendered, False otherwise.
    """
    if audio_data is None:
        return False

    try:
        import io
        import soundfile as sf

        buf = io.BytesIO()
        arr = audio_data.T if audio_data.ndim == 2 else audio_data
        sf.write(buf, arr, samplerate=48000, format="WAV")
        st.audio(buf.getvalue(), format="audio/wav")
        return True

    except Exception as e:
        st.error(f"Playback error: {e}")
        return False
