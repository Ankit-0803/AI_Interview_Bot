"""
Main Streamlit application for AI Interview Bot - SIMPLIFIED VERSION
"""
import streamlit as st
import time
from datetime import datetime
from pathlib import Path

# Component imports
from components.ai_engine import AIEngine
from components.audio_handler import AudioRecorder
from components.speech_processor import SpeechProcessor
from components.report_generator import ReportGenerator

# Utility imports
from utils.config import Config
from utils.helpers import generate_session_id, load_json, save_json

# Page configuration
st.set_page_config(
    page_title="AI Interview Bot",
    page_icon="🤖",
    layout="wide"
)

def load_css():
    css_file = Path("assets/styles.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

class InterviewBot:
    def __init__(self):
        self.config = Config()
        self.ai_engine = AIEngine()
        self.audio_recorder = AudioRecorder()
        self.speech_processor = SpeechProcessor()
        self.report_generator = ReportGenerator()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        defaults = {
            'step': 'welcome',
            'session_id': generate_session_id(),
            'candidate_name': '',
            'selected_role': None,
            'total_questions': 5,
            'current_question_number': 1,
            'interview_introduction': '',
            'current_question': '',
            'previous_questions': [],
            'qa_pairs': [],
            'interview_complete': False,
            'evaluation_results': None,
            'start_time': None
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def run(self):
        self._render_sidebar()
        
        if st.session_state.step == 'welcome':
            self._render_welcome()
        elif st.session_state.step == 'setup':
            self._render_setup()
        elif st.session_state.step == 'interview':
            self._render_interview()
        elif st.session_state.step == 'complete':
            self._render_complete()
    
    def _render_sidebar(self):
        with st.sidebar:
            st.markdown("# 🤖 AI Interview Bot")
            
            if st.session_state.step != 'welcome':
                st.markdown("---")
                st.markdown("### Session Info")
                if st.session_state.candidate_name:
                    st.info(f"Candidate: {st.session_state.candidate_name}")
                if st.session_state.selected_role:
                    st.info(f"Role: {st.session_state.selected_role['title']}")
            
            if st.session_state.step == 'interview':
                st.markdown("---")
                st.markdown("### Progress")
                completed = len(st.session_state.qa_pairs)
                current = st.session_state.current_question_number
                total = st.session_state.total_questions
                progress = completed / total
                st.progress(progress)
                st.markdown(f"Question {current} of {total}")
                st.markdown(f"Completed: {completed}/{total}")
            
            st.markdown("---")
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.step = 'welcome'
                st.rerun()
            
            if st.button("🔄 New Interview", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key != 'session_id':
                        del st.session_state[key]
                self._initialize_session_state()
                st.rerun()
    
    def _render_welcome(self):
        st.markdown("# 👩🏻‍💻 Welcome to AI Interview Bot")
        
        st.markdown("""
        ## Transform Your Hiring Process with AI
        ### Our AI powered interview bot helps streamline your recruitement process by:   
        ##### 1. AI-Generated Questions: Tailored to role requirements
        ##### 2. Audio Recording: Browser-based audio capture
        ##### 3. Speech-to-Text: Automatic transcription of responses  
        ##### 4. AI Evaluation: Comprehensive candidate assessment
        ##### 5. Detailed Reports: Structured evaluation reports  """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("# 👩🏻‍💻 Start New Interview", use_container_width=True, type="primary"):
                st.session_state.step = 'setup'
                st.rerun()
    
    def _render_setup(self):
        st.markdown("# 📋 Interview Setup")
        
        roles_data = self._load_roles()
        if not roles_data:
            st.error("Could not load role data")
            return
        
        st.markdown("## 👤 Candidate Information")
        candidate_name = st.text_input("Candidate Name *", value=st.session_state.candidate_name)
        st.session_state.candidate_name = candidate_name
        
        st.markdown("## 🎯 Role Selection")
        role_options = {role['title']: role for role in roles_data['roles']}
        selected_title = st.selectbox("Select Role *", options=list(role_options.keys()))
        st.session_state.selected_role = role_options[selected_title]
        
        with st.expander("📄 Role Details", expanded=True):
            role = st.session_state.selected_role
            st.markdown(f"**Department:** {role.get('department', 'N/A')}")
            st.markdown(f"**Experience:** {role.get('experience_level', 'N/A')}")
            st.markdown(f"**Description:** {role['description']}")
            st.markdown("**Skills:** " + ", ".join(role['key_skills']))
        
        total_questions = st.slider("Number of Questions", 3, 7, 5)
        st.session_state.total_questions = total_questions
        
        st.markdown("---")
        if st.button("🎬 Start Interview", use_container_width=True, type="primary"):
            if not candidate_name.strip():
                st.warning("Please enter candidate name")
                return
            
            with st.spinner("🤖 Preparing interview..."):
                try:
                    introduction = self.ai_engine.generate_interview_introduction(
                        st.session_state.selected_role, total_questions
                    )
                    st.session_state.interview_introduction = introduction
                    
                    first_question = self.ai_engine.generate_single_question(
                        st.session_state.selected_role, 1, []
                    )
                    st.session_state.current_question = first_question
                    st.session_state.previous_questions = [first_question]
                    st.session_state.start_time = time.time()
                    
                    st.success("✅ Ready!")
                    time.sleep(1)
                    st.session_state.step = 'interview'
                    st.rerun()
                except Exception as e:
                    st.error(f"Setup failed: {e}")
    
    def _render_interview(self):
        st.markdown(f"# 🎤 Interview: {st.session_state.selected_role['title']}")
        
        if st.session_state.current_question_number == 1 and len(st.session_state.qa_pairs) == 0:
            with st.expander("👋 Interview Introduction", expanded=True):
                st.markdown(st.session_state.interview_introduction)
        
        current_q = st.session_state.current_question_number
        total_q = st.session_state.total_questions
        completed = len(st.session_state.qa_pairs)
        
        progress = completed / total_q
        st.progress(progress, text=f"Question {current_q} of {total_q} | Completed: {completed}")
        
        st.markdown("---")
        
        # Check if already answered
        current_qa = None
        for qa in st.session_state.qa_pairs:
            if qa['question_number'] == current_q:
                current_qa = qa
                break
        
        if current_qa:
            # Already answered - show navigation
            st.success(f"✅ Question {current_q} completed!")
            
            with st.expander(f"Your Answer to Question {current_q}"):
                st.markdown(f"**Q:** {current_qa['question']}")
                st.markdown(f"**A:** {current_qa['answer']}")
            
            # Navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if current_q > 1:
                    if st.button("⬅️ Previous", use_container_width=True):
                        st.session_state.current_question_number -= 1
                        st.rerun()
            
            with col2:
                st.info(f"Question {current_q} of {total_q} completed")
            
            with col3:
                if current_q < total_q:
                    if st.button("➡️ Next Question", use_container_width=True, type="primary"):
                        self._proceed_to_next_question()
                else:
                    if st.button("🎯 Complete Interview", use_container_width=True, type="primary"):
                        self._complete_interview()
        
        else:
            # Current question
            self._render_current_question()
    
    def _render_current_question(self):
        current_q = st.session_state.current_question_number
        
        # Step 1: Recording
        st.markdown("### 📝 Current Question")
        st.info(st.session_state.current_question)
        
        st.markdown("### 🎤 Step 1: Record Your Answer")
        recording_result = self.audio_recorder.create_recording_interface(
            current_q, st.session_state.current_question
        )
        
        # Step 2: Transcription
        if recording_result['is_submitted'] and recording_result['has_recording']:
            st.markdown("---")
            st.markdown("### 📝 Step 2: Review Transcription")
            
            transcript = self.speech_processor.create_transcription_interface(
                recording_result['audio_data'], current_q
            )
            
            # Step 3: Final submission
            if transcript and transcript.strip():
                st.markdown("---")
                st.markdown("### ✅ Step 3: Submit & Continue")
                
                with st.container():
                    st.markdown("**Your Final Answer:**")
                    st.info(transcript[:300] + "..." if len(transcript) > 300 else transcript)
                
                # THE MAIN SUBMIT BUTTON
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col2:
                    # This is the button you're looking for!
                    if st.button(
                        f"✅ SUBMIT ANSWER {current_q} & CONTINUE TO NEXT QUESTION", 
                        key=f"FINAL_SUBMIT_{current_q}",
                        use_container_width=True, 
                        type="primary"
                    ):
                        # Save the Q&A
                        qa_pair = {
                            'question_number': current_q,
                            'question': st.session_state.current_question,
                            'answer': transcript,
                            'duration': recording_result.get('duration', 0)
                        }
                        
                        st.session_state.qa_pairs.append(qa_pair)
                        self._save_interview_progress()
                        
                        st.success("🎉 Answer submitted successfully!")
                        st.balloons()
                        
                        # Show next step
                        if current_q < st.session_state.total_questions:
                            st.info(f"Moving to Question {current_q + 1}...")
                        else:
                            st.info("Proceeding to final evaluation...")
                        
                        time.sleep(2)
                        st.rerun()
                
                # Show what's next
                if current_q < st.session_state.total_questions:
                    st.info(f"⏭️ Next: Question {current_q + 1} of {st.session_state.total_questions}")
                else:
                    st.info("⏭️ Next: Final evaluation and results")
    
    def _proceed_to_next_question(self):
        next_q_num = st.session_state.current_question_number + 1
        
        if next_q_num <= len(st.session_state.previous_questions):
            st.session_state.current_question = st.session_state.previous_questions[next_q_num - 1]
            st.session_state.current_question_number = next_q_num
            st.rerun()
        else:
            with st.spinner("🤖 Generating next question..."):
                try:
                    next_question = self.ai_engine.generate_single_question(
                        st.session_state.selected_role, next_q_num, st.session_state.previous_questions
                    )
                    
                    st.session_state.current_question = next_question
                    st.session_state.current_question_number = next_q_num
                    st.session_state.previous_questions.append(next_question)
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    def _complete_interview(self):
        with st.spinner("🤖 Generating evaluation..."):
            try:
                duration = (time.time() - st.session_state.start_time) / 60 if st.session_state.start_time else 0
                
                evaluation = self.ai_engine.evaluate_responses(
                    st.session_state.selected_role, st.session_state.qa_pairs
                )
                
                st.session_state.evaluation_results = evaluation
                
                final_report = {
                    'session_id': st.session_state.session_id,
                    'candidate_name': st.session_state.candidate_name,
                    'role': st.session_state.selected_role,
                    'qa_pairs': st.session_state.qa_pairs,
                    'evaluation': evaluation,
                    'total_duration_minutes': duration,
                    'completed_at': datetime.now().isoformat()
                }
                
                report_file = self.config.REPORTS_DIR / f"report_{st.session_state.session_id}.json"
                save_json(final_report, report_file)
                
                st.session_state.step = 'complete'
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    def _render_complete(self):
        st.markdown("# ✅ Interview Complete!")
        
        st.success(f"🎉 {st.session_state.candidate_name} completed the {st.session_state.selected_role['title']} interview!")
        
        # Show results
        if st.session_state.evaluation_results:
            evaluation = st.session_state.evaluation_results
            score = evaluation['overall_score']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Questions", len(st.session_state.qa_pairs))
            with col2:
                st.metric("Score", f"{score}/5.0")
            with col3:
                duration = (time.time() - st.session_state.start_time) / 60 if st.session_state.start_time else 0
                st.metric("Duration", f"{duration:.1f}min")
            
            st.markdown("---")
            if score >= 4.0:
                st.success(f"🌟 **Excellent Performance** - {score}/5.0")
            elif score >= 3.0:
                st.info(f"👍 **Good Performance** - {score}/5.0")
            else:
                st.warning(f"📈 **Needs Improvement** - {score}/5.0")
            
            st.markdown("### Summary")
            st.write(evaluation['summary'])
            
            if evaluation.get('recommendations'):
                st.markdown("### Recommendations")
                for rec in evaluation['recommendations']:
                    st.markdown(f"• {rec}")
        
        # Q&A Review
        st.markdown("---")
        st.markdown("## Interview Review")
        for qa in st.session_state.qa_pairs:
            with st.expander(f"Q{qa['question_number']}: {qa['question'][:50]}..."):
                st.markdown(f"**Question:** {qa['question']}")
                st.markdown(f"**Answer:** {qa['answer']}")
        
        # Actions
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Interview", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                self._initialize_session_state()
                st.rerun()
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.step = 'welcome'
                st.rerun()
    
    def _load_roles(self):
        try:
            roles_file = self.config.DATA_DIR / 'roles.json'
            return load_json(roles_file)
        except:
            return None
    
    def _save_interview_progress(self):
        try:
            progress_data = {
                'session_id': st.session_state.session_id,
                'candidate_name': st.session_state.candidate_name,
                'role': st.session_state.selected_role,
                'qa_pairs': st.session_state.qa_pairs,
                'last_updated': datetime.now().isoformat()
            }
            
            progress_file = self.config.SESSIONS_DIR / f"session_{st.session_state.session_id}.json"
            save_json(progress_data, progress_file)
        except Exception as e:
            st.error(f"Save failed: {e}")

def main():
    try:
        app = InterviewBot()
        app.run()
    except Exception as e:
        st.error(f"App error: {e}")
        st.info("Please refresh and try again.")

if __name__ == "__main__":
    main()
