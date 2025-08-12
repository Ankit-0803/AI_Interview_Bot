"""
Report generation and visualization component
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import json
from datetime import datetime
from pathlib import Path
from utils.config import Config
from utils.helpers import save_json, generate_session_id

class ReportGenerator:
    """Generate comprehensive interview reports"""
    
    def __init__(self):
        self.config = Config()
    
    def generate_comprehensive_report(self, 
                                    session_data: Dict[str, Any],
                                    role_data: Dict[str, Any],
                                    qa_pairs: List[Dict[str, str]],
                                    evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete interview report"""
        
        report = {
            'session_info': {
                'session_id': session_data.get('session_id', generate_session_id()),
                'role_title': role_data['title'],
                'role_id': role_data['id'],
                'candidate_name': session_data.get('candidate_name', 'Anonymous'),
                'interview_date': datetime.now().isoformat(),
                'total_questions': len(qa_pairs),
                'total_duration': session_data.get('total_duration', 0)
            },
            'role_information': role_data,
            'interview_data': {
                'questions_and_answers': qa_pairs,
                'transcription_method': session_data.get('transcription_method', 'google')
            },
            'evaluation_results': evaluation,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0',
                'ai_model_used': session_data.get('ai_model', 'fallback')
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save report to file"""
        
        session_id = report['session_info']['session_id']
        role_title = report['session_info']['role_title']
        
        filename = f"{session_id}_{role_title.replace(' ', '_').lower()}_report.json"
        filepath = self.config.REPORTS_DIR / filename
        
        success = save_json(report, filepath)
        
        if success:
            return filepath
        else:
            raise Exception("Failed to save report")
    
    def display_report(self, report: Dict[str, Any]):
        """Display comprehensive report in Streamlit"""
        
        # Report header
        st.markdown("# 📊 Interview Evaluation Report")
        
        self._display_session_overview(report['session_info'])
        self._display_role_information(report['role_information'])
        self._display_evaluation_summary(report['evaluation_results'])
        self._display_skill_analysis(report['evaluation_results'])
        self._display_qa_review(report['interview_data']['questions_and_answers'])
        self._display_recommendations(report['evaluation_results'])
    
    def _display_session_overview(self, session_info: Dict[str, Any]):
        """Display session overview"""
        
        st.markdown("## 👤 Session Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Role", session_info['role_title'])
        
        with col2:
            st.metric("Questions", session_info['total_questions'])
        
        with col3:
            duration = session_info.get('total_duration', 0)
            st.metric("Duration", f"{duration:.1f} min" if duration > 0 else "N/A")
        
        with col4:
            interview_date = datetime.fromisoformat(session_info['interview_date'])
            st.metric("Date", interview_date.strftime("%Y-%m-%d"))
    
    def _display_role_information(self, role_data: Dict[str, Any]):
        """Display role information"""
        
        st.markdown("## 🎯 Role Information")
        
        st.markdown(f"**Position:** {role_data['title']}")
        st.markdown(f"**Department:** {role_data.get('department', 'N/A')}")
        st.markdown(f"**Experience Level:** {role_data.get('experience_level', 'N/A')}")
        
        st.markdown("**Description:**")
        st.info(role_data['description'])
        
        st.markdown("**Key Skills Required:**")
        skills_cols = st.columns(min(len(role_data['key_skills']), 4))
        for i, skill in enumerate(role_data['key_skills']):
            with skills_cols[i % len(skills_cols)]:
                st.markdown(f"• {skill}")
    
    def _display_evaluation_summary(self, evaluation: Dict[str, Any]):
        """Display evaluation summary"""
        
        st.markdown("## 📈 Evaluation Summary")
        
        # Overall score with gauge chart
        col1, col2 = st.columns([1, 2])
        
        with col1:
            overall_score = evaluation.get('overall_score', 0)
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=overall_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Score"},
                delta={'reference': 3.0},
                gauge={
                    'axis': {'range': [None, 5]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 3.5], 'color': "yellow"},
                        {'range': [3.5, 5], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 4.0
                    }
                }
            ))
            
            fig.update_layout(height=300, margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recommendation based on score
            if overall_score >= 4.0:
                st.success("🌟 **Excellent Candidate** - Highly Recommended")
            elif overall_score >= 3.0:
                st.info("👍 **Good Candidate** - Recommended with Considerations")
            elif overall_score >= 2.0:
                st.warning("⚠️ **Average Candidate** - Requires Further Evaluation")
            else:
                st.error("❌ **Below Expectations** - Not Recommended")
            
            # Summary text
            summary = evaluation.get('summary', 'No summary available')
            st.markdown("**AI Summary:**")
            st.markdown(summary)
    
    def _display_skill_analysis(self, evaluation: Dict[str, Any]):
        """Display detailed skill analysis"""
        
        st.markdown("## 🔍 Skill Analysis")
        
        skill_ratings = evaluation.get('skill_ratings', {})
        
        if skill_ratings:
            # Create skill ratings chart
            skills_df = pd.DataFrame([
                {'Skill': skill, 'Rating': rating}
                for skill, rating in skill_ratings.items()
            ])
            
            # Horizontal bar chart
            fig = px.bar(
                skills_df,
                x='Rating',
                y='Skill',
                orientation='h',
                title='Skill Ratings (1-5 Scale)',
                color='Rating',
                color_continuous_scale='RdYlGn',
                range_color=[1, 5]
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Rating",
                yaxis_title="Skills",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Skill breakdown table
            st.markdown("### Detailed Skill Breakdown")
            
            skills_table = []
            for skill, rating in skill_ratings.items():
                if rating >= 4.0:
                    status = "🟢 Excellent"
                elif rating >= 3.0:
                    status = "🟡 Good"
                elif rating >= 2.0:
                    status = "🟠 Fair"
                else:
                    status = "🔴 Needs Improvement"
                
                skills_table.append({
                    'Skill': skill,
                    'Rating': f"{rating:.1f}/5.0",
                    'Status': status
                })
            
            skills_df = pd.DataFrame(skills_table)
            st.dataframe(skills_df, use_container_width=True)
    
    def _display_qa_review(self, qa_pairs: List[Dict[str, str]]):
        """Display Q&A review section"""
        
        st.markdown("## 💬 Interview Questions & Responses")
        
        for i, qa in enumerate(qa_pairs, 1):
            with st.expander(f"Question {i}: {qa['question'][:80]}..."):
                st.markdown(f"**Question {i}:**")
                st.info(qa['question'])
                
                st.markdown("**Response:**")
                st.markdown(qa['answer'])
                
                # Response metrics
                word_count = len(qa['answer'].split())
                char_count = len(qa['answer'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Words", word_count)
                with col2:
                    st.metric("Characters", char_count)
    
    def _display_recommendations(self, evaluation: Dict[str, Any]):
        """Display recommendations section"""
        
        st.markdown("## 🎯 Recommendations")
        
        recommendations = evaluation.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"{i}. {rec}")
        else:
            st.info("No specific recommendations generated.")
        
        # Next steps
        st.markdown("### 📋 Suggested Next Steps")
        
        overall_score = evaluation.get('overall_score', 0)
        
        if overall_score >= 4.0:
            next_steps = [
                "Schedule technical round with senior team members",
                "Prepare detailed project discussions",
                "Consider for fast-track process",
                "Check references and background"
            ]
        elif overall_score >= 3.0:
            next_steps = [
                "Schedule follow-up interview focusing on weak areas",
                "Conduct technical assessment if applicable",
                "Get input from other team members",
                "Consider for standard interview process"
            ]
        else:
            next_steps = [
                "Provide detailed feedback to candidate",
                "Consider alternative roles if appropriate",
                "Archive application for future opportunities",
                "Focus on stronger candidates in pipeline"
            ]
        
        for step in next_steps:
            st.markdown(f"• {step}")
    
    def create_downloadable_report(self, report: Dict[str, Any]) -> bytes:
        """Create downloadable report"""
        
        # Convert report to formatted JSON
        report_json = json.dumps(report, indent=2, ensure_ascii=False, default=str)
        
        return report_json.encode('utf-8')
    
    def create_summary_dashboard(self, reports: List[Dict[str, Any]]):
        """Create dashboard showing multiple interview summaries"""
        
        if not reports:
            st.info("No reports available for dashboard view")
            return
        
        st.markdown("# 📊 Interview Dashboard")
        
        # Convert reports to dataframe
        dashboard_data = []
        for report in reports:
            session_info = report['session_info']
            evaluation = report['evaluation_results']
            
            dashboard_data.append({
                'Session ID': session_info['session_id'],
                'Role': session_info['role_title'],
                'Date': session_info['interview_date'],
                'Overall Score': evaluation.get('overall_score', 0),
                'Questions': session_info['total_questions'],
                'Duration (min)': session_info.get('total_duration', 0)
            })
        
        df = pd.DataFrame(dashboard_data)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interviews", len(df))
        
        with col2:
            avg_score = df['Overall Score'].mean()
            st.metric("Average Score", f"{avg_score:.1f}")
        
        with col3:
            high_performers = (df['Overall Score'] >= 4.0).sum()
            st.metric("Strong Candidates", high_performers)
        
        with col4:
            avg_duration = df['Duration (min)'].mean()
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
        
        # Score distribution
        fig = px.histogram(
            df,
            x='Overall Score',
            nbins=10,
            title='Score Distribution',
            color_discrete_sequence=['lightblue']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.markdown("### Interview Summary Table")
        st.dataframe(df, use_container_width=True)
