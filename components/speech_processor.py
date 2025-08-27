"""
Speech-to-text processing component - FULLY FIXED WITH DEBUGGING
"""
import streamlit as st
import speech_recognition as sr
import tempfile
import os
import io
import time
from typing import Optional, Any
from pydub import AudioSegment
import requests


class SpeechProcessor:
    """Handle speech-to-text conversion with comprehensive debugging"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Optimized settings for better recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
    
    def create_transcription_interface(self, audio_data: Any, question_number: int) -> str:
        """Create interface for transcription with comprehensive debugging"""
        
        if audio_data is None:
            st.warning("❌ No audio data available")
            return self._manual_entry_interface(question_number)
        
        st.markdown("### 🎯 Speech-to-Text Transcription")
        
        # Session state keys
        transcript_key = f"transcript_q{question_number}"
        debug_key = f"debug_q{question_number}"
        manual_key = f"manual_q{question_number}"
        
        # Initialize session state
        for key in [transcript_key, debug_key, manual_key]:
            if key not in st.session_state:
                st.session_state[key] = "" if "transcript" in key else False
        
        # Audio analysis
        audio_info = self._analyze_audio_data(audio_data)
        
        # Display audio information
        with st.expander("🔍 Audio Analysis", expanded=False):
            for key, value in audio_info.items():
                st.write(f"**{key}:** {value}")
        
        # Method selection
        col1, col2 = st.columns(2)
        
        with col1:
            method = st.selectbox(
                "Choose transcription method:",
                ["auto_transcribe", "manual_entry", "test_connection"],
                index=0,
                key=f"method_{question_number}",
                format_func=lambda x: {
                    "auto_transcribe": "🎤 Auto Transcription",
                    "manual_entry": "✏️ Manual Entry", 
                    "test_connection": "🔗 Test Google API"
                }[x]
            )
        
        with col2:
            if audio_info['status'] == 'good':
                st.success("✅ Audio quality: Good")
            else:
                st.warning(f"⚠️ Audio: {audio_info['status']}")
        
        # Handle different methods
        if method == "manual_entry":
            return self._manual_entry_interface(question_number)
        elif method == "test_connection":
            self._test_google_connection()
            return st.session_state[transcript_key]
        else:
            return self._auto_transcription_interface(audio_data, question_number, audio_info)
    
    def _analyze_audio_data(self, audio_data: Any) -> dict:
        """Comprehensive audio data analysis"""
        
        analysis = {
            'type': str(type(audio_data)),
            'status': 'unknown',
            'duration': 0,
            'format': 'unknown',
            'size': 0
        }
        
        try:
            # Check if it's a pydub AudioSegment (from streamlit-audiorecorder)
            if hasattr(audio_data, 'duration_seconds'):
                analysis['type'] = 'pydub.AudioSegment'
                analysis['duration'] = f"{audio_data.duration_seconds:.2f}s"
                analysis['format'] = f"{audio_data.frame_rate}Hz, {audio_data.channels}ch"
                analysis['size'] = f"{len(audio_data.raw_data)} bytes"
                
                if audio_data.duration_seconds < 0.5:
                    analysis['status'] = 'too_short'
                elif audio_data.duration_seconds > 300:
                    analysis['status'] = 'too_long'
                elif len(audio_data.raw_data) < 1000:
                    analysis['status'] = 'too_small'
                else:
                    analysis['status'] = 'good'
                    
            elif hasattr(audio_data, '__len__'):
                analysis['size'] = f"{len(audio_data)} bytes"
                analysis['status'] = 'good' if len(audio_data) > 1000 else 'too_small'
                
            else:
                analysis['status'] = 'unsupported_format'
                
        except Exception as e:
            analysis['status'] = f'analysis_error: {str(e)}'
        
        return analysis
    
    def _auto_transcription_interface(self, audio_data: Any, question_number: int, audio_info: dict) -> str:
        """Handle automatic transcription with step-by-step debugging"""
        
        transcript_key = f"transcript_q{question_number}"
        debug_key = f"debug_q{question_number}"
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎤 Start Transcription", key=f"start_transcribe_{question_number}"):
                st.session_state[debug_key] = True
                st.rerun()
        
        with col2:
            if st.session_state[transcript_key]:
                if st.button("🔄 Retry", key=f"retry_{question_number}"):
                    st.session_state[transcript_key] = ""
                    st.session_state[debug_key] = True
                    st.rerun()
        
        with col3:
            if st.button("✏️ Switch to Manual", key=f"manual_switch_{question_number}"):
                return self._manual_entry_interface(question_number)
        
        # Perform transcription with debugging
        if st.session_state[debug_key] and not st.session_state[transcript_key]:
            transcript = self._transcribe_with_debugging(audio_data, question_number, audio_info)
            st.session_state[transcript_key] = transcript
            st.session_state[debug_key] = False
            st.rerun()
        
        # Show transcript editor
        if st.session_state[transcript_key]:
            if "ERROR" in st.session_state[transcript_key] or "failed" in st.session_state[transcript_key].lower():
                st.error("❌ Transcription failed")
                st.info("💡 Try manual entry or check your internet connection")
            else:
                st.success("✅ Transcription completed!")
            
            # Editable transcript
            edited_transcript = st.text_area(
                "Review and edit transcript:",
                value=st.session_state[transcript_key],
                height=120,
                key=f"edit_transcript_{question_number}",
                help="Edit the transcript to fix any errors"
            )
            
            return edited_transcript
        
        return ""
    
    def _transcribe_with_debugging(self, audio_data: Any, question_number: int, audio_info: dict) -> str:
        """Transcribe audio with step-by-step debugging output"""
        
        debug_container = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Step 1: Audio data validation
            debug_container.info("🔍 Step 1: Validating audio data...")
            progress_bar.progress(0.1)
            time.sleep(0.5)
            
            if audio_data is None:
                return "ERROR: No audio data provided"
            
            # Step 2: Convert audio format
            debug_container.info("🔄 Step 2: Converting audio format...")
            progress_bar.progress(0.3)
            time.sleep(0.5)
            
            wav_buffer = self._convert_to_wav_buffer(audio_data)
            if wav_buffer is None:
                return "ERROR: Failed to convert audio format"
            
            # Step 3: Test internet connection
            debug_container.info("🌐 Step 3: Testing internet connection...")
            progress_bar.progress(0.5)
            
            if not self._test_internet_connection():
                return "ERROR: No internet connection for Google Speech API"
            
            # Step 4: Create audio file for recognition
            debug_container.info("📁 Step 4: Preparing audio file...")
            progress_bar.progress(0.7)
            time.sleep(0.5)
            
            temp_file_path = self._create_temp_audio_file(wav_buffer)
            if not temp_file_path:
                return "ERROR: Failed to create temporary audio file"
            
            # Step 5: Perform speech recognition
            debug_container.info("🎤 Step 5: Performing speech recognition...")
            progress_bar.progress(0.9)
            
            try:
                with sr.AudioFile(temp_file_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Record the audio
                    audio = self.recognizer.record(source)
                    
                    # Recognize using Google
                    transcript = self.recognizer.recognize_google(
                        audio, 
                        language='en-US',
                        show_all=False
                    )
                    
                    progress_bar.progress(1.0)
                    debug_container.success("✅ Transcription completed successfully!")
                    time.sleep(1)
                    
                    return transcript if transcript else "No speech detected in audio"
            
            except sr.UnknownValueError:
                return "Could not understand audio - please speak more clearly"
            
            except sr.RequestError as e:
                return f"Google Speech Recognition API error: {str(e)}"
            
            finally:
                # Clean up temp file
                try:
                    if temp_file_path and os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except:
                    pass
        
        except Exception as e:
            progress_bar.progress(1.0)
            debug_container.error(f"❌ Transcription failed: {str(e)}")
            return f"ERROR: Transcription failed - {str(e)}"
    
    def _convert_to_wav_buffer(self, audio_data: Any) -> Optional[io.BytesIO]:
        """Convert audio data to WAV format buffer"""
        
        try:
            if hasattr(audio_data, 'export'):
                # pydub AudioSegment from streamlit-audiorecorder
                audio_segment = audio_data
                
                # Ensure optimal format for speech recognition
                audio_segment = audio_segment.set_channels(1)  # Mono
                audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
                
                # Export to BytesIO buffer
                wav_buffer = io.BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                wav_buffer.seek(0)
                
                return wav_buffer
            
            elif isinstance(audio_data, bytes):
                # Raw bytes
                return io.BytesIO(audio_data)
            
            else:
                st.error(f"❌ Unsupported audio format: {type(audio_data)}")
                return None
        
        except Exception as e:
            st.error(f"❌ Audio conversion error: {str(e)}")
            return None
    
    def _create_temp_audio_file(self, wav_buffer: io.BytesIO) -> Optional[str]:
        """Create temporary WAV file from buffer"""
        
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            # Write buffer contents to file
            temp_file.write(wav_buffer.getvalue())
            temp_file.close()
            
            return temp_file.name
        
        except Exception as e:
            st.error(f"❌ Failed to create temp file: {str(e)}")
            return None
    
    def _test_internet_connection(self) -> bool:
        """Test internet connectivity"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _test_google_connection(self):
        """Test Google Speech Recognition API connectivity"""
        st.markdown("### 🔗 Testing Google Speech Recognition API")
        
        with st.spinner("Testing connection..."):
            # Test internet connection
            if not self._test_internet_connection():
                st.error("❌ No internet connection")
                return
            
            st.success("✅ Internet connection: OK")
            
            # Test Google Speech API with a simple request
            try:
                # Create a simple test audio (1 second of silence)
                test_audio = AudioSegment.silent(duration=1000)  # 1 second
                test_buffer = io.BytesIO()
                test_audio.export(test_buffer, format="wav")
                test_buffer.seek(0)
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.write(test_buffer.getvalue())
                temp_file.close()
                
                with sr.AudioFile(temp_file.name) as source:
                    audio = self.recognizer.record(source)
                    # This should fail with UnknownValueError (no speech)
                    self.recognizer.recognize_google(audio)
                
            except sr.UnknownValueError:
                # This is expected for silent audio
                st.success("✅ Google Speech API: Connected and working")
            except sr.RequestError as e:
                st.error(f"❌ Google Speech API error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Test failed: {str(e)}")
            finally:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def _manual_entry_interface(self, question_number: int) -> str:
        """Manual text entry interface"""
        st.info("✏️ Manual text entry mode")
        
        manual_text = st.text_area(
            "Type your answer here:",
            height=150,
            key=f"manual_text_{question_number}",
            placeholder="Type your answer manually...",
            help="Enter your response by typing instead of using speech recognition"
        )
        
        if manual_text:
            word_count = len(manual_text.split())
            char_count = len(manual_text)
            st.success(f"✅ Manual entry: {word_count} words, {char_count} characters")
        
        return manual_text


# Additional utility functions
def test_speech_recognition_setup():
    """Test the complete speech recognition setup"""
    st.markdown("## 🔧 Speech Recognition Setup Test")
    
    if st.button("Run Complete Test"):
        with st.spinner("Testing setup..."):
            
            # Test 1: Import dependencies
            try:
                import speech_recognition as sr
                import pydub
                import requests
                st.success("✅ All required packages imported successfully")
            except ImportError as e:
                st.error(f"❌ Missing package: {e}")
                return
            
            # Test 2: Create recognizer
            try:
                recognizer = sr.Recognizer()
                st.success("✅ Speech recognizer created successfully")
            except Exception as e:
                st.error(f"❌ Failed to create recognizer: {e}")
                return
            
            # Test 3: Internet connectivity
            try:
                response = requests.get("https://www.google.com", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Internet connection: OK")
                else:
                    st.warning("⚠️ Internet connection may be slow")
            except:
                st.error("❌ No internet connection")
                return
            
            # Test 4: Google Speech API
            try:
                test_audio = pydub.AudioSegment.silent(duration=1000)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                test_audio.export(temp_file.name, format="wav")
                
                with sr.AudioFile(temp_file.name) as source:
                    audio = recognizer.record(source)
                    recognizer.recognize_google(audio)
                    
            except sr.UnknownValueError:
                st.success("✅ Google Speech API: Connected and working")
            except sr.RequestError as e:
                st.error(f"❌ Google Speech API error: {e}")
            except Exception as e:
                st.error(f"❌ API test failed: {e}")
            finally:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
            st.success("🎉 Setup test completed!")
