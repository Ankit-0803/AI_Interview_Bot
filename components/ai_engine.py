"""
AI Engine for question generation and candidate evaluation
"""
import requests
import time
from typing import Dict, List, Tuple, Any
import streamlit as st
from utils.config import Config


class AIEngine:
    """AI Engine for generating interview questions and evaluations"""
    
    def __init__(self):
        self.config = Config()
        self.headers = self.config.HF_HEADERS if hasattr(self.config, 'HF_HEADERS') else {}
    
    def generate_single_question(self, role_data: Dict[str, Any], question_number: int, previous_questions: List[str] = None) -> str:
        """
        Generate a single interview question based on role and question number
        """
        if previous_questions is None:
            previous_questions = []
            
        try:
            prompt = f"""
Generate 1 interview question for a {role_data['title']} position.

Role Description: {role_data['description']}
Key Skills: {', '.join(role_data['key_skills'])}
Experience Level: {role_data['experience_level']}
Question Number: {question_number}

Previously asked questions:
{chr(10).join(previous_questions) if previous_questions else 'None'}

Generate a unique question that:
- Assesses {role_data['title']} skills
- Is appropriate for question #{question_number}
- Doesn't repeat previous questions
- Encourages detailed responses

Format: Just return the question without "Q:" prefix.
"""
            
            generated_text = self._query_huggingface_api(prompt, max_tokens=150)
            question = self._extract_question_from_text(generated_text)
            
            if not question or len(question) < 10:
                return self._get_fallback_question(role_data, question_number)
                
            return question
            
        except Exception as e:
            st.warning(f"Using fallback question due to API error: {e}")
            return self._get_fallback_question(role_data, question_number)
    
    def generate_interview_introduction(self, role_data: Dict[str, Any], total_questions: int) -> str:
        """Generate personalized introduction"""
        return f"""
Hello and welcome to your {role_data['title']} interview!

I'm an AI interviewer designed to help evaluate your skills and experience for this position. 
This interview will consist of {total_questions} questions tailored specifically to the {role_data['title']} role.

Please take your time with each response, speak clearly, and feel free to provide detailed examples 
from your experience. Each question will be presented one at a time, and you'll have the opportunity 
to record your audio response.

Let's begin when you're ready!
"""
    
    def _query_huggingface_api(self, prompt: str, max_tokens: int = 150) -> str:
        """Query Hugging Face API with retry logic"""
        
        if not self.config.HF_API_TOKEN:
            raise ValueError("Hugging Face API token not configured")
        
        api_url = f"https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        for attempt in range(3):
            try:
                response = requests.post(
                    api_url, 
                    headers=self.headers, 
                    json=payload, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get('generated_text', '')
                    return result.get('generated_text', '')
                
                elif response.status_code == 503:
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    response.raise_for_status()
                    
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def _extract_question_from_text(self, generated_text: str) -> str:
        """Extract clean question from generated text"""
        lines = generated_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if '?' in line and len(line) > 15:
                # Clean up the question
                if line.startswith('Q:'):
                    line = line[2:].strip()
                return line
        
        # If no good question found, return the first substantial line
        for line in lines:
            line = line.strip()
            if len(line) > 15:
                return line + "?"
        
        return ""
    
    def _get_fallback_question(self, role_data: Dict[str, Any], question_number: int) -> str:
        """Generate fallback questions when API fails"""
        
        role_title = role_data['title'].lower()
        
        # General questions that work for any role
        general_questions = [
            f"Tell me about your experience in {role_data['title']} roles and what attracted you to this field.",
            "Can you describe a challenging project you've worked on recently and how you approached it?",
            "How do you stay updated with the latest trends and technologies in your field?",
            "Tell me about a time when you had to work under pressure or tight deadlines. How did you manage it?",
            "Describe a situation where you had to collaborate with team members who had different opinions. How did you handle it?",
            "What do you consider your greatest professional achievement so far, and why?",
            "How do you approach problem-solving when faced with a complex technical challenge?"
        ]
        
        # Role-specific questions
        role_specific = []
        
        if 'developer' in role_title or 'engineer' in role_title:
            role_specific = [
                "Walk me through your development process from requirement analysis to deployment.",
                "How do you ensure code quality and maintainability in your projects?",
                "Describe a time when you had to debug a particularly difficult issue.",
                "What programming languages and frameworks do you prefer and why?"
            ]
        
        elif 'data' in role_title or 'scientist' in role_title:
            role_specific = [
                "How do you approach data analysis for solving business problems?",
                "Describe a data project that had significant business impact.",
                "What tools and technologies do you use for data analysis and visualization?",
                "How do you handle missing or inconsistent data in your analysis?"
            ]
        
        elif 'product' in role_title or 'manager' in role_title:
            role_specific = [
                "How do you prioritize features and make product decisions?",
                "Describe your experience with stakeholder management and communication.",
                "Tell me about a successful product launch you've managed.",
                "How do you gather and incorporate user feedback into product development?"
            ]
        
        elif 'marketing' in role_title:
            role_specific = [
                "How do you measure the success of your marketing campaigns?",
                "Describe a marketing campaign you created that exceeded expectations.",
                "How do you stay current with digital marketing trends and best practices?",
                "What's your approach to understanding and targeting different customer segments?"
            ]
        
        # Combine questions
        all_questions = general_questions + role_specific
        
        # Return question based on question number
        if question_number <= len(all_questions):
            return all_questions[question_number - 1]
        
        return "Tell me more about your experience and what makes you a good fit for this role."
    
    def evaluate_responses(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate candidate responses and generate comprehensive report
        """
        try:
            return self._generate_evaluation_report(role_data, qa_pairs)
        except Exception as e:
            st.error(f"Error generating evaluation: {e}")
            return self._get_fallback_evaluation(role_data, qa_pairs)
    
    def _generate_evaluation_report(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate detailed evaluation using simple heuristics"""
        
        # Calculate overall score based on response quality
        total_score = 0
        skill_ratings = {}
        
        for qa in qa_pairs:
            response_length = len(qa['answer'])
            word_count = len(qa['answer'].split())
            
            # Score based on response quality indicators
            if response_length > 200 and word_count > 30:
                score = 4.5
            elif response_length > 100 and word_count > 20:
                score = 3.5
            elif response_length > 50 and word_count > 10:
                score = 2.5
            else:
                score = 1.5
            
            total_score += score
        
        overall_score = total_score / len(qa_pairs) if qa_pairs else 0
        
        # Generate skill ratings
        for skill in role_data['key_skills']:
            # Simple skill rating based on keyword presence and overall performance
            skill_score = overall_score + (0.5 if any(skill.lower() in qa['answer'].lower() for qa in qa_pairs) else -0.5)
            skill_ratings[skill] = max(1.0, min(5.0, skill_score))
        
        # Generate summary
        if overall_score >= 4.0:
            summary = "Excellent candidate with strong communication skills and relevant experience. Provided detailed, thoughtful responses that demonstrate deep understanding of the role requirements."
        elif overall_score >= 3.0:
            summary = "Good candidate with solid experience and communication skills. Responses show understanding of key concepts with room for some improvement in detail and depth."
        elif overall_score >= 2.0:
            summary = "Average candidate with basic understanding of the role. Responses were adequate but lacked depth and detail in some areas."
        else:
            summary = "Candidate may need additional development. Responses were brief and didn't fully demonstrate the required level of expertise for this role."
        
        recommendations = self._generate_recommendations(overall_score, skill_ratings)
        
        return {
            'overall_score': round(overall_score, 1),
            'summary': summary,
            'skill_ratings': skill_ratings,
            'recommendations': recommendations,
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_questions': len(qa_pairs)
        }
    
    def _generate_recommendations(self, overall_score: float, skill_ratings: Dict[str, float]) -> List[str]:
        """Generate recommendations based on evaluation"""
        recommendations = []
        
        if overall_score >= 4.0:
            recommendations.append("Strong candidate - Highly recommend for next interview round")
            recommendations.append("Consider for expedited hiring process")
        elif overall_score >= 3.0:
            recommendations.append("Good candidate - Recommend for next round with standard process")
            recommendations.append("May benefit from additional technical assessment")
        elif overall_score >= 2.0:
            recommendations.append("Average candidate - Consider additional evaluation")
            recommendations.append("May need skills development in key areas")
        else:
            recommendations.append("Below expectations - May not be suitable for current role")
            recommendations.append("Consider for junior positions or provide additional training")
        
        # Identify strengths and weaknesses
        strengths = [skill for skill, rating in skill_ratings.items() if rating >= 4.0]
        weaknesses = [skill for skill, rating in skill_ratings.items() if rating < 2.5]
        
        if strengths:
            recommendations.append(f"Key strengths demonstrated: {', '.join(strengths[:3])}")
        
        if weaknesses:
            recommendations.append(f"Areas needing improvement: {', '.join(weaknesses[:3])}")
        
        return recommendations
    
    def _get_fallback_evaluation(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate fallback evaluation when AI fails"""
        return {
            'overall_score': 3.0,
            'summary': 'Basic evaluation completed. Recommend manual review for detailed assessment.',
            'skill_ratings': {skill: 3.0 for skill in role_data['key_skills']},
            'recommendations': ['Manual evaluation required', 'Schedule follow-up interview'],
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_questions': len(qa_pairs)
        }
