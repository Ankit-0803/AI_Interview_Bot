"""
Speech-to-text processing component
"""
import streamlit as st
import speech_recognition as sr
import numpy as np
import tempfile
import os
from typing import Optional, Union, Any
from pydub import AudioSegment
import io
from utils.config import Config

class SpeechProcessor:
    """Handle speech-to-text conversion"""
    
    def __init__(self):
        self.config = Config()
        self.recognizer = sr.Recognizer()
        # Configure recognizer settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
    
    def transcribe_audio(self, audio_data: Any, method: str = "google") -> str:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Audio data from recorder
            method: Recognition method ("google", "sphinx", "whisper")
            
        Returns:
            Transcribed text
        """
        
        try:
            # Convert audio data to the format expected by speech_recognition
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
            if 'audio_file' in locals() and audio_file:
                try:
                    os.unlink(audio_file)
                except:
                    pass
    
    def _prepare_audio_for_transcription(self, audio_data: Any) -> Optional[str]:
        """Prepare audio data for transcription"""
        
        try:
            # Handle different types of audio data
            if hasattr(audio_data, 'export'):
                # Streamlit audiorecorder AudioSegment
                audio_segment = audio_data
            
            elif isinstance(audio_data, np.ndarray):
                # Raw numpy array from WebRTC
                # Convert to AudioSegment
                # Assuming 16kHz sample rate, 16-bit samples
                audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                audio_segment = AudioSegment(
                    data=audio_bytes,
                    sample_width=2,
                    frame_rate=16000,
                    channels=1
                )
            
            elif isinstance(audio_data, bytes):
                # Raw audio bytes
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            
            else:
                st.error(f"Unsupported audio data type: {type(audio_data)}")
                return None
            
            # Convert to WAV format for speech recognition
            # Ensure it's mono and at 16kHz (standard for speech recognition)
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
            
            # Export to temporary file
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
            elif method == "whisper":
                return self._transcribe_whisper(audio_segment)
            else:
                # Default to Google
                return self._transcribe_google(audio_segment)
        
        except Exception as e:
            # Try fallback methods
            fallback_methods = ["google", "sphinx"]
            for fallback in fallback_methods:
                if fallback != method:
                    try:
                        return self._transcribe_with_method(audio_segment, fallback)
                    except:
                        continue
            
            raise e
    
    def _transcribe_google(self, audio_segment: sr.AudioData) -> str:
        """Transcribe using Google Speech Recognition (free tier)"""
        try:
            return self.recognizer.recognize_google(audio_segment)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            raise Exception(f"Google Speech Recognition error: {e}")
    
    def _transcribe_sphinx(self, audio_segment: sr.AudioData) -> str:
        """Transcribe using offline Sphinx (requires pocketsphinx)"""
        try:
            return self.recognizer.recognize_sphinx(audio_segment)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            raise Exception(f"Sphinx error: {e}")
        except Exception:
            raise Exception("Sphinx not available. Install pocketsphinx: pip install pocketsphinx")
    
    def _transcribe_whisper(self, audio_segment: sr.AudioData) -> str:
        """Transcribe using OpenAI Whisper API"""
        
        if not self.config.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        try:
            import openai
            openai.api_key = self.config.OPENAI_API_KEY
            
            # Save audio to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with open(tmp_file.name, "wb") as f:
                    f.write(audio_segment.get_wav_data())
                
                # Transcribe with Whisper
                with open(tmp_file.name, "rb") as audio_file:
                    transcript = openai.Audio.transcribe("whisper-1", audio_file)
                
                os.unlink(tmp_file.name)
                return transcript["text"]
        
        except ImportError:
            raise Exception("OpenAI package not installed: pip install openai")
        except Exception as e:
            raise Exception(f"Whisper API error: {e}")
    
    def create_transcription_interface(self, audio_data: Any, question_number: int) -> str:
        """Create interface for transcription with method selection"""
        
        if audio_data is None:
            return ""
        
        st.subheader("🎯 Speech-to-Text Transcription")
        
        # Method selection
        method = st.selectbox(
            "Choose transcription method:",
            ["google", "sphinx", "whisper"],
            index=0,
            key=f"transcribe_method_{question_number}",
            help="""
            - Google: Free, accurate, requires internet
            - Sphinx: Offline, less accurate
            - Whisper: Most accurate, requires OpenAI API key
            """
        )
        
        # Transcription button
        if st.button(f"🎤 Transcribe Audio", key=f"transcribe_{question_number}"):
            with st.spinner("Transcribing audio..."):
                transcript = self.transcribe_audio(audio_data, method)
                st.session_state[f'transcript_{question_number}'] = transcript
        
        # Display transcript
        transcript = st.session_state.get(f'transcript_{question_number}', '')
        
        if transcript:
            st.success("✅ Transcription completed!")
            
            # Editable transcript
            edited_transcript = st.text_area(
                "Review and edit transcript:",
                value=transcript,
                height=100,
                key=f"edit_transcript_{question_number}",
                help="You can edit the transcript to correct any errors"
            )
            
            return edited_transcript
        
        return ""
    
    def batch_transcribe(self, audio_recordings: list, method: str = "google") -> list:
        """Transcribe multiple audio recordings"""
        
        transcripts = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, audio_data in enumerate(audio_recordings):
            status_text.text(f"Transcribing recording {i+1} of {len(audio_recordings)}")
            
            try:
                transcript = self.transcribe_audio(audio_data, method)
                transcripts.append(transcript)
            except Exception as e:
                st.error(f"Error transcribing recording {i+1}: {e}")
                transcripts.append(f"Transcription failed: {str(e)}")
            
            progress_bar.progress((i + 1) / len(audio_recordings))
        
        status_text.text("✅ All transcriptions completed!")
        
        return transcripts
    
    def get_audio_quality_metrics(self, audio_data: Any) -> dict:
        """Analyze audio quality for transcription"""
        
        try:
            if hasattr(audio_data, 'duration_seconds'):
                duration = audio_data.duration_seconds
                if duration < 1:
                    return {'quality': 'poor', 'reason': 'Too short (less than 1 second)'}
                elif duration > 300:
                    return {'quality': 'warning', 'reason': 'Very long (over 5 minutes)'}
                else:
                    return {'quality': 'good', 'duration': duration}
            
            return {'quality': 'unknown', 'reason': 'Could not analyze audio'}
        
        except Exception as e:
            return {'quality': 'error', 'reason': f'Analysis failed: {str(e)}'}
