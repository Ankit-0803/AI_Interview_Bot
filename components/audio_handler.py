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
        self.recording_start_time = None
        self.recording_end_time = None

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
        self.recording_start_time = st.time()
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def stop_and_get(self) -> Optional[np.ndarray]:
        """Stop recording and return concatenated audio or None."""
        self._is_recording = False
        self.recording_end_time = st.time()
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

    def create_recording_interface(self, question_number: int, question_text: str) -> dict:
        """
        Streamlit interface to record audio for a given question.
        Returns a dictionary with:
          - has_recording: bool
          - audio_data: numpy.ndarray or None
          - duration: float (seconds) or 0
        """

        st.markdown(f"### Question {question_number}: {question_text}")

        # Use WebRTC streamer for audio recording
        webrtc_ctx = self.create_streamer(key=f"audio_recorder_{question_number}")

        # Local state for recording management
        if 'is_recording' not in st.session_state:
            st.session_state['is_recording'] = False
        if 'recorded_audio' not in st.session_state:
            st.session_state['recorded_audio'] = None
        if 'recording_start' not in st.session_state:
            st.session_state['recording_start'] = None

        def start_recording():
            st.session_state['is_recording'] = True
            self.start()
            st.session_state['recording_start'] = time.time()

        def stop_recording():
            st.session_state['is_recording'] = False
            audio = self.stop_and_get()
            st.session_state['recorded_audio'] = audio

        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state['is_recording']:
                if st.button("🔴 Start Recording"):
                    start_recording()
            else:
                if st.button("⏹ Stop Recording"):
                    stop_recording()

        with col2:
            duration = 0
            if st.session_state['recording_start'] and st.session_state['is_recording']:
                duration = time.time() - st.session_state['recording_start']
                st.markdown(f"Recording for {duration:.1f} seconds...")

            elif st.session_state['recorded_audio'] is not None:
                duration = st.session_state['recorded_audio'].shape[-1] / 48000  # assuming 48kHz sample rate
                st.markdown(f"Recorded audio length: {duration:.1f} seconds")

        return {
            'has_recording': st.session_state['recorded_audio'] is not None,
            'audio_data': st.session_state['recorded_audio'],
            'duration': duration,
        }
