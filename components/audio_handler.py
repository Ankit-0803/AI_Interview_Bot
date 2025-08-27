"""
Simplified audio handling without WebRTC
"""
import streamlit as st
import time
from typing import Dict, Any


class AudioRecorder:
    """Simplified audio recorder using Streamlit's audio_recorder"""
    
    def __init__(self):
        pass
    
    def create_recording_interface(self, question_number: int, question_text: str) -> Dict[str, Any]:
        """Create recording interface using streamlit-audiorecorder"""
        
        st.markdown(f"### 🎤 Question {question_number}")
        st.info(question_text)
        
        # Session state keys
        audio_key = f"audio_q{question_number}"
        submitted_key = f"submitted_q{question_number}"
        
        # Initialize session state
        if audio_key not in st.session_state:
            st.session_state[audio_key] = None
        if submitted_key not in st.session_state:
            st.session_state[submitted_key] = False
        
        st.markdown("---")
        st.markdown("### 🎙️ Record Your Answer")
        
        try:
            # Try to use streamlit-audiorecorder
            from audiorecorder import audiorecorder
            
            audio_data = audiorecorder("🎤 Click to record", "⏹️ Recording...")
            
            if audio_data is not None and len(audio_data) > 0:
                st.session_state[audio_key] = audio_data
                
                # Show playback
                st.success("✅ Recording completed!")
                st.audio(audio_data.export().read())
                
                # Submit button
                if not st.session_state[submitted_key]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔄 Re-record", key=f"rerecord_{question_number}"):
                            st.session_state[audio_key] = None
                            st.rerun()
                    
                    with col2:
                        if st.button("✅ Submit Recording", 
                                   key=f"submit_{question_number}", 
                                   type="primary"):
                            st.session_state[submitted_key] = True
                            st.success("🎉 Recording submitted!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                else:
                    st.success("✅ Recording submitted - ready for transcription!")
            
            else:
                st.info("👆 Click the microphone button above to start recording")
        
        except ImportError:
            # Fallback to file uploader
            st.warning("Audio recorder not available. Please upload an audio file instead.")
            
            uploaded_audio = st.file_uploader(
                "Upload your audio response",
                type=['wav', 'mp3', 'm4a'],
                key=f"upload_{question_number}"
            )
            
            if uploaded_audio is not None:
                st.session_state[audio_key] = uploaded_audio
                st.audio(uploaded_audio)
                
                if not st.session_state[submitted_key]:
                    if st.button("✅ Submit Audio", 
                               key=f"submit_upload_{question_number}", 
                               type="primary"):
                        st.session_state[submitted_key] = True
                        st.success("🎉 Audio submitted!")
                        time.sleep(1)
                        st.rerun()
        
        return {
            'has_recording': st.session_state[audio_key] is not None,
            'audio_data': st.session_state[audio_key],
            'is_recording': False,
            'is_submitted': st.session_state[submitted_key],
            'duration': 0
        }
