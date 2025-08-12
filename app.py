"""
Main Streamlit application for AI Audio Interview Bot
"""
import streamlit as st
import json
from pathlib import Path
import time
from datetime import datetime

# Component imports
from components.ai_engine import AIEngine
from components.audio_handler import AudioRecorder
from components.speech_processor import SpeechProcessor
from components.report_generator import ReportGenerator

# Utility imports
from utils.config import Config
from utils.helpers import generate_session_id, load_json, format_duration

# ✅ Ensure default step on first load or after reset
valid_steps = [
    "welcome", "interview_setup", "interview_process",
    "interview_complete", "view_reports"
]
if (
    "current_step" not in st.session_state
    or st.session_state.current_step not in valid_steps
):
    st.session_state.current_step = "welcome"

# Page configuration - set AFTER session state init
st.set_page_config(
    page_title="AI Audio Interview Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path("assets/styles.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


class InterviewBot:
    """Main Interview Bot Application"""
    
    def __init__(self):
        self.config = Config()
        self.ai_engine = AIEngine()
        self.audio_recorder = AudioRecorder()
        self.speech_processor = SpeechProcessor()
        self.report_generator = ReportGenerator()
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        
        defaults = {
            'session_id': generate_session_id(),
            'current_step': 'welcome',
            'selected_role': None,
            'candidate_name': '',
            'interview_introduction': '',
            'interview_questions': [],
            'current_question_index': 0,
            'qa_pairs': [],
            'interview_complete': False,
            'evaluation_results': None,
            'start_time': None
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def run(self):
        """Run the main application"""
        
        # Sidebar
        self._render_sidebar()
        
        # Main content
        if st.session_state.current_step == 'welcome':
            self._render_welcome_page()
        elif st.session_state.current_step == 'interview_setup':
            self._render_interview_setup()
        elif st.session_state.current_step == 'interview_process':
            self._render_interview_process()
        elif st.session_state.current_step == 'interview_complete':
            self._render_interview_complete()
        elif st.session_state.current_step == 'view_reports':
            self._render_reports_dashboard()
    
    def _render_sidebar(self):
        """Render sidebar with navigation and info"""
        
        with st.sidebar:
            st.markdown("# 🤖 AI Interview Bot")
            
            # Session info
            if st.session_state.current_step != 'welcome':
                st.markdown("---")
                st.markdown("### Session Info")
                st.info(f"Session ID: {st.session_state.session_id[:12]}...")
                
                if st.session_state.selected_role:
                    st.info(f"Role: {st.session_state.selected_role['title']}")
                
                if st.session_state.candidate_name:
                    st.info(f"Candidate: {st.session_state.candidate_name}")
            
            # Navigation
            st.markdown("---")
            st.markdown("### Navigation")
            
            # 🚀 Start New Interview (always visible)
            if st.button("👩🏻‍💻 Start New Interview",use_container_width=True):
             for key in list(st.session_state.keys()):
                if key != 'session_id':
                   del st.session_state[key]
                st.session_state.session_id = generate_session_id()
             st.session_state.current_step = 'interview_setup'
             st.rerun()

            
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_step = 'welcome'
                st.rerun()
            
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.current_step = 'view_reports'
                st.rerun()
            
            if st.button("🔄 Reset Session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key not in ['session_id']:  # Keep session_id
                        del st.session_state[key]
                st.session_state.session_id = generate_session_id()
                st.session_state.current_step = 'welcome'
                st.rerun()
            
            # Progress indicator
            if st.session_state.current_step == 'interview_process':
                st.markdown("---")
                st.markdown("### Progress")
                
                current_q = st.session_state.current_question_index
                total_q = len(st.session_state.interview_questions)
                
                progress = (current_q + 1) / total_q if total_q > 0 else 0
                st.progress(progress)
                
                st.markdown(f"Question {current_q + 1} of {total_q}")
    
    def _render_welcome_page(self):
        """Render welcome page"""
        
        st.markdown("# 👩🏻‍💻 Welcome to AI Video Interview Bot")
        
        st.markdown("""
        ### Transform Your Hiring Process with AI
        
        Our AI-powered interview bot helps streamline your recruitment process by:
        
        -  **AI-Generated Questions**: Tailored questions based on role requirements
        -  **Video Recording**: Browser-based video/audio capture
        -  **Speech-to-Text**: Automatic transcription of responses
        -  **AI Evaluation**: Comprehensive candidate assessment
        -  **Detailed Reports**: Structured evaluation reports
        """)
        
        # Features showcase
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🎯 Smart Questioning
            - Role-specific questions
            - Dynamic question generation
            - Multiple difficulty levels
            """)
        
        with col2:
            st.markdown("""
            #### 🎥 Easy Recording
            - Browser-based recording
            - No software installation
            - High-quality audio capture
            """)
        
        with col3:
            st.markdown("""
            #### 📈 Comprehensive Analysis
            - AI-powered evaluation
            - Skill-based scoring
            - Actionable insights
            """)
        
        # Get started button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("👩🏻‍💻 Start New Interview", use_container_width=True):
                st.session_state.current_step = 'interview_setup'
                st.rerun()
    
    def _render_interview_setup(self):
        """Render interview setup page"""
        
        st.markdown("# 📋 Interview Setup")

        # Load available roles
        roles_data = self._load_roles()
        
        if not roles_data:
            st.error("Could not load role data. Please check the data/roles.json file.")
            return
        
        # Candidate information
        st.markdown("## 👤 Candidate Information")
        
        candidate_name = st.text_input(
            "Candidate Name",
            value=st.session_state.candidate_name,
            placeholder="Enter candidate's full name"
        )
        
        st.session_state.candidate_name = candidate_name
        
        # Role selection
        st.markdown("## 🎯 Role Selection")
        
        role_options = {role['title']: role for role in roles_data['roles']}
        selected_role_title = st.selectbox(
            "Select the role for this interview:",
            options=list(role_options.keys()),
            index=0
        )
        
        selected_role = role_options[selected_role_title]
        st.session_state.selected_role = selected_role
        
        # Display role information
        with st.expander("📄 Role Details", expanded=True):
            st.markdown(f"**Department:** {selected_role.get('department', 'N/A')}")
            st.markdown(f"**Experience Level:** {selected_role.get('experience_level', 'N/A')}")
            st.markdown(f"**Description:** {selected_role['description']}")
            
            st.markdown("**Key Skills:**")
            skills_cols = st.columns(min(len(selected_role['key_skills']), 4))
            for i, skill in enumerate(selected_role['key_skills']):
                with skills_cols[i % len(skills_cols)]:
                    st.markdown(f"• {skill}")
        
        # Interview configuration
        st.markdown("## ⚙️ Interview Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            question_count = st.slider(
                "Number of questions",
                min_value=self.config.MIN_QUESTION_COUNT,
                max_value=self.config.MAX_QUESTION_COUNT,
                value=self.config.MAX_QUESTION_COUNT
            )
        
        with col2:
            transcription_method = st.selectbox(
                "Transcription method",
                ["google", "sphinx", "whisper"],
                index=0,
                help="Google: Free, accurate, online | Sphinx: Offline, basic | Whisper: Premium, most accurate"
            )
        
        # Start interview button
        st.markdown("---")
        
        if st.button("🎬 Generate Questions & Start Interview", use_container_width=True):
            if not candidate_name.strip():
                st.warning("Please enter the candidate's name.")
                return
            
            # Generate interview content
            with st.spinner("🤖 Generating personalized interview content..."):
                try:
                    introduction, questions = self.ai_engine.generate_interview_content(selected_role)
                    
                    # Limit questions to selected count
                    questions = questions[:question_count]
                    
                    st.session_state.interview_introduction = introduction
                    st.session_state.interview_questions = questions
                    st.session_state.transcription_method = transcription_method
                    st.session_state.start_time = time.time()
                    
                    st.success(f"✅ Generated {len(questions)} questions successfully!")
                    
                    time.sleep(1)  # Brief pause for user to see success message
                    
                    st.session_state.current_step = 'interview_process'
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Failed to generate interview content: {e}")
    
    def _render_interview_process(self):
        """Render the main interview process"""
        
        st.markdown(f"# 🎤 Interview: {st.session_state.selected_role['title']}")
        
        # Display introduction if first question
        if st.session_state.current_question_index == 0:
            with st.expander("👋 Interview Introduction", expanded=True):
                st.markdown(st.session_state.interview_introduction)
        
        # Current question
        current_index = st.session_state.current_question_index
        questions = st.session_state.interview_questions
        
        if current_index < len(questions):
            current_question = questions[current_index]
            
            # Progress indicator
            progress = (current_index) / len(questions)
            st.progress(progress, text=f"Question {current_index + 1} of {len(questions)}")
            
            st.markdown("---")
            
            # Recording interface
            recording_result = self.audio_recorder.create_recording_interface(
                current_index + 1, current_question
            )
            
            # Transcription interface
            if recording_result['has_recording']:
                st.markdown("---")
                transcript = self.speech_processor.create_transcription_interface(
                    recording_result['audio_data'], 
                    current_index + 1
                )
                
                # Navigation buttons
                if transcript.strip():
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        if current_index > 0:
                            if st.button("⬅️ Previous Question"):
                                # Save current answer if not already saved
                                if current_index < len(st.session_state.qa_pairs):
                                    st.session_state.qa_pairs[current_index] = {
                                        'question': current_question,
                                        'answer': transcript,
                                        'duration': recording_result.get('duration', 0)
                                    }
                                else:
                                    st.session_state.qa_pairs.append({
                                        'question': current_question,
                                        'answer': transcript,
                                        'duration': recording_result.get('duration', 0)
                                    })
                                
                                st.session_state.current_question_index -= 1
                                st.rerun()
                    
                    with col2:
                        st.markdown("**Review your answer and proceed when ready**")
                    
                    with col3:
                        if st.button("➡️ Next Question" if current_index < len(questions) - 1 else "✅ Complete Interview"):
                            # Save current answer
                            qa_pair = {
                                'question': current_question,
                                'answer': transcript,
                                'duration': recording_result.get('duration', 0)
                            }
                            
                            # Update or append QA pair
                            if current_index < len(st.session_state.qa_pairs):
                                st.session_state.qa_pairs[current_index] = qa_pair
                            else:
                                st.session_state.qa_pairs.append(qa_pair)
                            
                            # Move to next question or complete
                            if current_index < len(questions) - 1:
                                st.session_state.current_question_index += 1
                                st.rerun()
                            else:
                                # Complete interview
                                self._complete_interview()
        
        else:
            # All questions completed
            self._complete_interview()
    
    def _complete_interview(self):
        """Complete the interview and generate evaluation"""
        
        st.session_state.interview_complete = True
        
        # Calculate total duration
        if st.session_state.start_time:
            total_duration = (time.time() - st.session_state.start_time) / 60  # Convert to minutes
            st.session_state.total_duration = total_duration
        
        # Generate evaluation
        with st.spinner("🤖 Generating AI evaluation..."):
            try:
                evaluation = self.ai_engine.evaluate_responses(
                    st.session_state.selected_role,
                    st.session_state.qa_pairs
                )
                st.session_state.evaluation_results = evaluation
                
                # Generate and save report
                session_data = {
                    'session_id': st.session_state.session_id,
                    'candidate_name': st.session_state.candidate_name,
                    'total_duration': st.session_state.get('total_duration', 0),
                    'transcription_method': st.session_state.get('transcription_method', 'google'),
                    'ai_model': 'huggingface'  # Track which model was used
                }
                
                report = self.report_generator.generate_comprehensive_report(
                    session_data,
                    st.session_state.selected_role,
                    st.session_state.qa_pairs,
                    evaluation
                )
                
                # Save report
                report_path = self.report_generator.save_report(report)
                st.session_state.report_path = report_path
                
                st.session_state.current_step = 'interview_complete'
                st.rerun()
            
            except Exception as e:
                st.error(f"Failed to generate evaluation: {e}")
                # Still proceed to completion with basic evaluation
                st.session_state.evaluation_results = {
                    'overall_score': 3.0,
                    'summary': 'Evaluation failed. Manual review required.',
                    'skill_ratings': {},
                    'recommendations': ['Manual evaluation needed']
                }
                st.session_state.current_step = 'interview_complete'
                st.rerun()
    
    def _render_interview_complete(self):
        """Render interview completion page"""
        
        st.markdown("# ✅ Interview Complete!")
        
        st.success(f"🎉 Congratulations! You have completed the {st.session_state.selected_role['title']} interview.")
        
        # Interview summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Questions Answered", len(st.session_state.qa_pairs))
        
        with col2:
            total_duration = st.session_state.get('total_duration', 0)
            st.metric("Total Duration", f"{total_duration:.1f} min")
        
        with col3:
            overall_score = st.session_state.evaluation_results.get('overall_score', 0)
            st.metric("Overall Score", f"{overall_score:.1f}/5.0")
        
        # Generate and display report
        if st.session_state.evaluation_results:
            st.markdown("---")
            
            session_data = {
                'session_id': st.session_state.session_id,
                'candidate_name': st.session_state.candidate_name,
                'total_duration': st.session_state.get('total_duration', 0),
                'transcription_method': st.session_state.get('transcription_method', 'google')
            }
            
            report = self.report_generator.generate_comprehensive_report(
                session_data,
                st.session_state.selected_role,
                st.session_state.qa_pairs,
                st.session_state.evaluation_results
            )
            
            # Display report
            self.report_generator.display_report(report)
            
            # Download button
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                report_bytes = self.report_generator.create_downloadable_report(report)
                
                st.download_button(
                    label="📥 Download Full Report (JSON)",
                    data=report_bytes,
                    file_name=f"interview_report_{st.session_state.session_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        # Action buttons
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Start New Interview", use_container_width=True):
                # Reset session for new interview
                for key in list(st.session_state.keys()):
                    if key not in ['session_id']:
                        del st.session_state[key]
                st.session_state.session_id = generate_session_id()
                st.session_state.current_step = 'welcome'
                st.rerun()
        
        with col2:
            if st.button("📊 View All Reports", use_container_width=True):
                st.session_state.current_step = 'view_reports'
                st.rerun()
    
    def _render_reports_dashboard(self):
        """Render reports dashboard"""
        
        st.markdown("# 📊 Reports Dashboard")
        
        # Load all reports
        reports = self._load_all_reports()
        
        if not reports:
            st.info("No reports available yet. Complete some interviews to see reports here.")
            return
        
        # Display dashboard
        self.report_generator.create_summary_dashboard(reports)
        
        # Individual report viewer
        st.markdown("---")
        st.markdown("## 📄 Individual Reports")
        
        report_files = list(self.config.REPORTS_DIR.glob("*.json"))
        
        if report_files:
            selected_file = st.selectbox(
                "Select a report to view:",
                options=report_files,
                format_func=lambda x: x.stem
            )
            
            if st.button("📖 View Selected Report"):
                report_data = load_json(selected_file)
                if report_data:
                    self.report_generator.display_report(report_data)
        
    def _load_roles(self):
        """Load role data from JSON file"""
        roles_file = self.config.DATA_DIR / 'roles.json'
        return load_json(roles_file)
    
    def _load_all_reports(self):
        """Load all saved reports"""
        reports = []
        
        for report_file in self.config.REPORTS_DIR.glob("*.json"):
            try:
                report_data = load_json(report_file)
                if report_data:
                    reports.append(report_data)
            except:
                continue
        
        return sorted(reports, key=lambda x: x['session_info']['interview_date'], reverse=True)

def main():
    """Main application entry point"""
    try:
        app = InterviewBot()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
