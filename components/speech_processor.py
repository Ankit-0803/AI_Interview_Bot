"""
Speech-to-text processing component
"""
import streamlit as st
import speech_recognition as sr
import numpy as np
import tempfile
import os
from typing import Optional, Any
from pydub import AudioSegment
import io


class SpeechProcessor:
    """Handle speech-to-text conversion"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Configure recognizer settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
    
    def transcribe_audio(self, audio_data: Any, method: str = "google") -> str:
        """
        Transcribe audio data to text
        """
        if audio_data is None:
            return "No audio data provided"
        
        try:
            # Prepare audio for transcription
            audio_file = self._prepare_audio_for_transcription(audio_data)
            
            if audio_file is None:
                return "Error: Could not prepare audio for transcription"
            
            # Perform transcription
            with sr.AudioFile(audio_file) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Record the audio
                audio_segment = self.recognizer.record(source)
                
                # Transcribe using selected method
                transcript = self._transcribe_with_method(audio_segment, method)
                
                return transcript if transcript else "Could not transcribe audio clearly"
        
        except Exception as e:
            st.error(f"Transcription error: {e}")
            return f"Transcription failed: {str(e)}"
        
        finally:
            # Cleanup temporary file
            if 'audio_file' in locals() and audio_file and os.path.exists(audio_file):
                try:
                    os.unlink(audio_file)
                except:
                    pass
    
    def _prepare_audio_for_transcription(self, audio_data: Any) -> Optional[str]:
        """Prepare audio data for transcription"""
        
        try:
            if isinstance(audio_data, np.ndarray):
                # Handle numpy array from WebRTC
                audio_data = audio_data.flatten() if audio_data.ndim > 1 else audio_data
                
                # Convert to proper format for AudioSegment
                if audio_data.dtype != np.int16:
                    # Normalize and convert to int16
                    if np.max(np.abs(audio_data)) > 0:
                        audio_data = audio_data / np.max(np.abs(audio_data))
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # Create AudioSegment from raw audio
                audio_segment = AudioSegment(
                    data=audio_data.tobytes(),
                    sample_width=2,  # 16-bit
                    frame_rate=16000,  # 16kHz
                    channels=1  # Mono
                )
                
            elif isinstance(audio_data, bytes):
                # Handle raw audio bytes
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                
            elif hasattr(audio_data, 'export'):
                # Already an AudioSegment
                audio_segment = audio_data
                
            else:
                st.error(f"Unsupported audio data type: {type(audio_data)}")
                return None
            
            # Ensure proper format for speech recognition
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
            
            # Export to temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            audio_segment.export(temp_file.name, format="wav")
            
            return temp_file.name
        
        except Exception as e:
            st.error(f"Audio preparation error: {e}")
            return None
    
    def _transcribe_with_method(self, audio_segment: sr.AudioData, method: str) -> str:
        """Transcribe using specified method"""
        
        try:
            if method == "google":
                return self._transcribe_google(audio_segment)
            elif method == "sphinx":
                return self._transcribe_sphinx(audio_segment)
            else:
                # Default to Google
                return self._transcribe_google(audio_segment)
        
        except Exception as e:
            # Try fallback method
            if method != "google":
                try:
                    return self._transcribe_google(audio_segment)
                except:
                    pass
            
            raise e
    
    def _transcribe_google(self, audio_segment: sr.AudioData) -> str:
        """Transcribe using Google Speech Recognition (free tier)"""
        try:
            result = self.recognizer.recognize_google(audio_segment)
            return result if result else "Could not understand audio"
        except sr.UnknownValueError:
            return "Could not understand the audio clearly"
        except sr.RequestError as e:
            raise Exception(f"Google Speech Recognition service error: {e}")
    
    def _transcribe_sphinx(self, audio_segment: sr.AudioData) -> str:
        """Transcribe using offline Sphinx (requires pocketsphinx)"""
        try:
            result = self.recognizer.recognize_sphinx(audio_segment)
            return result if result else "Could not understand audio"
        except sr.UnknownValueError:
            return "Could not understand the audio clearly"
        except sr.RequestError as e:
            raise Exception(f"Sphinx recognition error: {e}")
        except Exception:
            raise Exception("Sphinx not available. Install with: pip install pocketsphinx")
    
    def create_transcription_interface(self, audio_data: Any, question_number: int) -> str:
        """
        Create interface for transcription with automatic processing
        """
        if audio_data is None:
            st.warning("No audio data available for transcription")
            return ""
        
        st.markdown("### 🎯 Speech-to-Text Transcription")
        
        # Auto-transcribe if not already done
        transcript_key = f"transcript_q{question_number}"
        transcribing_key = f"transcribing_q{question_number}"
        
        if transcript_key not in st.session_state:
            st.session_state[transcript_key] = ""
        
        if transcribing_key not in st.session_state:
            st.session_state[transcribing_key] = False
        
        # Method selection
        method = st.selectbox(
            "Transcription method:",
            ["google", "sphinx"],
            index=0,
            key=f"method_q{question_number}",
            help="Google: Accurate, requires internet | Sphinx: Offline, basic accuracy"
        )
        
        # Auto-transcribe button or show existing transcript
        if not st.session_state[transcript_key] and not st.session_state[transcribing_key]:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎤 Transcribe Audio", key=f"transcribe_btn_{question_number}", use_container_width=True):
                    st.session_state[transcribing_key] = True
                    st.rerun()
            
            with col2:
                if st.button("⚡ Auto-Transcribe", key=f"auto_transcribe_btn_{question_number}", use_container_width=True, type="primary"):
                    st.session_state[transcribing_key] = True
                    st.rerun()
        
        # Perform transcription
        if st.session_state[transcribing_key] and not st.session_state[transcript_key]:
            with st.spinner("🎤 Transcribing your audio response..."):
                try:
                    transcript = self.transcribe_audio(audio_data, method)
                    st.session_state[transcript_key] = transcript
                    st.session_state[transcribing_key] = False
                    st.success("✅ Transcription completed!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
                    st.session_state[transcribing_key] = False
                    st.session_state[transcript_key] = "Transcription failed. Please try again or speak more clearly."
                    st.rerun()
        
        # Display and edit transcript
        if st.session_state[transcript_key]:
            st.success("✅ Transcription completed!")
            
            # Show original transcript
            with st.expander("📝 Original Transcript", expanded=False):
                st.write(st.session_state[transcript_key])
            
            # Editable transcript
            edited_transcript = st.text_area(
                "Review and edit your transcript:",
                value=st.session_state[transcript_key],
                height=120,
                key=f"edit_transcript_{question_number}",
                help="You can edit this transcript to correct any errors before submitting"
            )
            
            # Update session state with edited version
            st.session_state[transcript_key] = edited_transcript
            
            return edited_transcript
        
        return ""
    
    def get_audio_quality_info(self, audio_data: Any) -> dict:
        """Get basic audio quality information"""
        try:
            if isinstance(audio_data, np.ndarray):
                duration = len(audio_data) / 16000  # Assuming 16kHz sample rate
                max_amplitude = np.max(np.abs(audio_data))
                
                if duration < 1:
                    return {'quality': 'poor', 'reason': 'Recording too short (less than 1 second)'}
                elif max_amplitude < 0.01:
                    return {'quality': 'poor', 'reason': 'Audio level very low, please speak louder'}
                elif duration > 300:
                    return {'quality': 'warning', 'reason': 'Very long recording (over 5 minutes)'}
                else:
                    return {'quality': 'good', 'duration': f"{duration:.1f}s", 'level': 'normal'}
            
            return {'quality': 'unknown', 'reason': 'Could not analyze audio'}
        
        except Exception as e:
            return {'quality': 'error', 'reason': f'Analysis failed: {str(e)}'}
