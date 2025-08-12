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
        self.headers = self.config.HF_HEADERS
    
    def generate_interview_content(self, role_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Generate personalized introduction and interview questions
        
        Args:
            role_data: Dictionary containing role information
            
        Returns:
            Tuple of (introduction, list of questions)
        """
        try:
            # Generate introduction
            introduction = self._generate_introduction(role_data)
            
            # Generate questions
            questions = self._generate_questions(role_data)
            
            return introduction, questions
            
        except Exception as e:
            st.error(f"Error generating interview content: {e}")
            return self._get_fallback_content(role_data)
    
    def _generate_introduction(self, role_data: Dict[str, Any]) -> str:
        """Generate personalized introduction"""
        return self.config.GREETING_TEMPLATE.format(
            role_title=role_data['title'],
            question_count=self.config.MAX_QUESTION_COUNT
        )
    
    def _generate_questions(self, role_data: Dict[str, Any]) -> List[str]:
        """Generate interview questions using Hugging Face API"""
        
        prompt = f"""
        Generate {self.config.MAX_QUESTION_COUNT} interview questions for a {role_data['title']} position.
        
        Role Description: {role_data['description']}
        Key Skills: {', '.join(role_data['key_skills'])}
        Experience Level: {role_data['experience_level']}
        
        Create questions that assess:
        1. Technical competency
        2. Practical experience
        3. Problem-solving abilities
        4. Communication skills
        5. Cultural fit
        6. Leadership potential
        7. Specific role knowledge
        
        Format each question on a new line starting with "Q:" followed by the question.
        Make questions specific, relevant, and appropriate for the experience level.
        
        Example format:
        Q: Can you describe your experience with [specific technology]?
        Q: How would you approach [specific scenario]?
        """
        
        try:
            questions = self._query_huggingface_api(prompt, max_tokens=500)
            parsed_questions = self._parse_questions(questions)
            
            # Ensure we have the right number of questions
            if len(parsed_questions) < self.config.MIN_QUESTION_COUNT:
                parsed_questions.extend(self._get_fallback_questions(role_data))
            
            return parsed_questions[:self.config.MAX_QUESTION_COUNT]
            
        except Exception as e:
            st.warning(f"Using fallback questions due to API error: {e}")
            return self._get_fallback_questions(role_data)
    
    def _query_huggingface_api(self, prompt: str, max_tokens: int = 300, model: str = None) -> str:
        """Query Hugging Face API with retry logic"""
        
        if not self.config.HF_API_TOKEN:
            raise ValueError("Hugging Face API token not configured")
        
        model_name = model or "microsoft/DialoGPT-medium"
        api_url = f"{self.config.HF_API_URL}/{model_name}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        max_retries = 3
        for attempt in range(max_retries):
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
                    # Model is loading, wait and retry
                    time.sleep(10 * (attempt + 1))
                    continue
                else:
                    response.raise_for_status()
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def _parse_questions(self, generated_text: str) -> List[str]:
        """Parse questions from generated text"""
        questions = []
        lines = generated_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                question = line[2:].strip()
                if len(question) > 10:  # Basic validation
                    questions.append(question)
            elif '?' in line and len(line) > 20:
                # Catch questions that might not have the Q: prefix
                questions.append(line.strip())
        
        return questions
    
    def _get_fallback_questions(self, role_data: Dict[str, Any]) -> List[str]:
        """Generate fallback questions when API fails"""
        
        role_title = role_data['title'].lower()
        base_questions = [
            f"Tell me about your experience in {role_data['title']} roles.",
            "What attracted you to this position and our company?",
            "Describe a challenging project you've worked on recently.",
            "How do you stay updated with industry trends and technologies?",
            "Tell me about a time you had to work under pressure or tight deadlines.",
            "How do you approach problem-solving in your work?",
            "Describe your experience working in a team environment."
        ]
        
        # Role-specific questions
        if 'developer' in role_title or 'engineer' in role_title:
            base_questions.extend([
                "Walk me through your development process from requirement to deployment.",
                "How do you ensure code quality and maintainability?",
                "Describe a technical challenge you overcame recently."
            ])
        
        elif 'data' in role_title:
            base_questions.extend([
                "How do you approach data analysis for business problems?",
                "What tools and technologies do you prefer for data work?",
                "Describe a data project that had significant business impact."
            ])
        
        elif 'manager' in role_title:
            base_questions.extend([
                "How do you prioritize features and make product decisions?",
                "Describe your experience with stakeholder management.",
                "Tell me about a successful product launch you've managed."
            ])
        
        return base_questions[:self.config.MAX_QUESTION_COUNT]
    
    def _get_fallback_content(self, role_data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Get fallback content when AI generation fails"""
        introduction = self._generate_introduction(role_data)
        questions = self._get_fallback_questions(role_data)
        return introduction, questions
    
    def evaluate_responses(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluate candidate responses and generate comprehensive report
        
        Args:
            role_data: Role information
            qa_pairs: List of question-answer pairs
            
        Returns:
            Evaluation report dictionary
        """
        try:
            return self._generate_evaluation_report(role_data, qa_pairs)
        except Exception as e:
            st.error(f"Error generating evaluation: {e}")
            return self._get_fallback_evaluation(role_data, qa_pairs)
    
    def _generate_evaluation_report(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate detailed evaluation using AI"""
        
        # Create context for evaluation
        context = f"""
        Role: {role_data['title']}
        Description: {role_data['description']}
        Key Skills Required: {', '.join(role_data['key_skills'])}
        Experience Level: {role_data['experience_level']}
        
        Interview Questions and Answers:
        """
        
        for i, qa in enumerate(qa_pairs, 1):
            context += f"\n\nQ{i}: {qa['question']}\nA{i}: {qa['answer'][:500]}..."  # Limit answer length for context
        
        # Generate summary
        summary_prompt = f"""
        {context}
        
        Based on the candidate's responses above, provide a comprehensive evaluation summary.
        Focus on:
        - Overall impression and fit for the role
        - Key strengths demonstrated
        - Areas for improvement or concerns
        - Specific examples from their responses
        - Recommendation (Strong Hire/Hire/Maybe/No Hire)
        
        Keep the summary professional, balanced, and specific.
        """
        
        try:
            summary = self._query_huggingface_api(summary_prompt, max_tokens=400)
        except:
            summary = "Unable to generate AI summary. Manual review recommended."
        
        # Generate skill ratings
        skill_ratings = self._evaluate_skills(role_data, qa_pairs)
        
        # Calculate overall score
        overall_score = sum(skill_ratings.values()) / len(skill_ratings) if skill_ratings else 0
        
        return {
            'overall_score': round(overall_score, 1),
            'summary': summary,
            'skill_ratings': skill_ratings,
            'recommendations': self._generate_recommendations(overall_score, skill_ratings),
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_questions': len(qa_pairs)
        }
    
    def _evaluate_skills(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, float]:
        """Evaluate specific skills based on responses"""
        skill_ratings = {}
        
        # Basic skill evaluation (this could be enhanced with more sophisticated NLP)
        for skill in role_data['key_skills']:
            rating = self._rate_skill_from_responses(skill, qa_pairs)
            skill_ratings[skill] = rating
        
        # Add evaluation criteria ratings
        for criteria in self.config.EVALUATION_CRITERIA:
            if criteria not in skill_ratings:
                rating = self._rate_criteria_from_responses(criteria, qa_pairs)
                skill_ratings[criteria] = rating
        
        return skill_ratings
    
    def _rate_skill_from_responses(self, skill: str, qa_pairs: List[Dict[str, str]]) -> float:
        """Rate a specific skill based on candidate responses"""
        # Simple keyword-based scoring (can be enhanced with ML models)
        skill_keywords = {
            'JavaScript': ['javascript', 'js', 'react', 'vue', 'angular', 'node'],
            'Python': ['python', 'django', 'flask', 'pandas', 'numpy'],
            'Communication': ['explain', 'team', 'collaborate', 'present', 'discuss'],
            'Leadership': ['lead', 'manage', 'mentor', 'guide', 'decision'],
            'Problem Solving': ['solve', 'challenge', 'debug', 'analyze', 'approach']
        }
        
        keywords = skill_keywords.get(skill, [skill.lower()])
        
        score = 0
        total_responses = len(qa_pairs)
        
        for qa in qa_pairs:
            answer_lower = qa['answer'].lower()
            keyword_count = sum(1 for keyword in keywords if keyword in answer_lower)
            response_length = len(qa['answer'])
            
            # Score based on keyword presence and response quality
            if keyword_count > 0:
                score += min(keyword_count * 0.3, 1.0)  # Max 1 point per response
            
            # Bonus for detailed responses
            if response_length > 100:
                score += 0.2
        
        # Normalize to 1-5 scale
        normalized_score = 1 + (score / total_responses) * 4
        return min(5.0, max(1.0, normalized_score))
    
    def _rate_criteria_from_responses(self, criteria: str, qa_pairs: List[Dict[str, str]]) -> float:
        """Rate evaluation criteria from responses"""
        # Basic heuristic scoring
        total_length = sum(len(qa['answer']) for qa in qa_pairs)
        avg_length = total_length / len(qa_pairs) if qa_pairs else 0
        
        # Score based on response quality indicators
        if avg_length > 200:
            return 4.0 + (min(avg_length, 500) - 200) / 300  # Scale from 4 to 5
        elif avg_length > 100:
            return 3.0 + (avg_length - 100) / 100  # Scale from 3 to 4
        elif avg_length > 50:
            return 2.0 + (avg_length - 50) / 50   # Scale from 2 to 3
        else:
            return 1.0 + avg_length / 50  # Scale from 1 to 2
    
    def _generate_recommendations(self, overall_score: float, skill_ratings: Dict[str, float]) -> List[str]:
        """Generate recommendations based on evaluation"""
        recommendations = []
        
        if overall_score >= 4.0:
            recommendations.append("Strong candidate - Recommend for next round")
        elif overall_score >= 3.0:
            recommendations.append("Good candidate - Consider for next round with reservations")
        else:
            recommendations.append("May not be the right fit for this role")
        
        # Find strengths and weaknesses
        strengths = [skill for skill, rating in skill_ratings.items() if rating >= 4.0]
        weaknesses = [skill for skill, rating in skill_ratings.items() if rating < 2.5]
        
        if strengths:
            recommendations.append(f"Key strengths: {', '.join(strengths[:3])}")
        
        if weaknesses:
            recommendations.append(f"Areas for development: {', '.join(weaknesses[:3])}")
        
        return recommendations
    
    def _get_fallback_evaluation(self, role_data: Dict[str, Any], qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate fallback evaluation when AI fails"""
        return {
            'overall_score': 3.0,
            'summary': 'Evaluation generated using fallback method. Manual review recommended.',
            'skill_ratings': {skill: 3.0 for skill in role_data['key_skills']},
            'recommendations': ['Manual evaluation required', 'Review responses manually'],
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_questions': len(qa_pairs)
        }
