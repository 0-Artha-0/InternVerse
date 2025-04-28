"""
Service for interacting with the AI supervisor model.
This file handles all communications with the OpenAI API.
"""

import json
import logging
from app import app
from openai import OpenAI, AzureOpenAI
from supervisor_prompts import (
    get_task_generation_prompt,
    get_feedback_prompt,
    get_chat_prompt,
    get_resources_prompt,
    get_certificate_prompt
)

# Initialize OpenAI client with Azure or standard OpenAI
def init_openai_client():
    """Initialize the appropriate OpenAI client (Azure or Standard) based on available credentials."""
    # First try Azure OpenAI
    if app.config.get("AZURE_OPENAI_ENDPOINT") and app.config.get("AZURE_OPENAI_KEY"):
        try:
            # Create Azure OpenAI client
            client = AzureOpenAI(
                api_key=app.config["AZURE_OPENAI_KEY"],
                azure_endpoint=app.config["AZURE_OPENAI_ENDPOINT"],
                api_version=app.config.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
            )
            logging.info("AI Supervisor: Azure OpenAI client configured")
            return client, "azure"
        except Exception as e:
            logging.error(f"AI Supervisor: Error configuring Azure OpenAI client: {str(e)}")
            # Fall back to standard OpenAI below
    
    # Try standard OpenAI API if Azure failed or not configured
    if app.config.get("OPENAI_API_KEY"):
        try:
            # Create standard OpenAI client
            client = OpenAI(api_key=app.config["OPENAI_API_KEY"])
            logging.info("AI Supervisor: Standard OpenAI client configured")
            return client, "standard"
        except Exception as e:
            logging.error(f"AI Supervisor: Error configuring standard OpenAI client: {str(e)}")
            return None, None
    else:
        logging.warning("AI Supervisor: No OpenAI credentials found. Using fallback responses.")
        return None, None

# Call this at application startup
openai_client, openai_type = init_openai_client()

def call_openai_api(system_message, user_message):
    """
    Make a call to the OpenAI API with the given messages.
    
    Args:
        system_message (str): The system message to guide the AI's behavior
        user_message (str): The user message containing the specific request
        
    Returns:
        str: The AI's response text
    """
    try:
        if not openai_client:
            raise Exception("No OpenAI client available")
            
        # Check which OpenAI API we're using
        if openai_type == "azure":
            # Using Azure OpenAI
            if not app.config.get("AZURE_OPENAI_DEPLOYMENT"):
                raise Exception("Azure OpenAI deployment not configured")
                
            completion = openai_client.chat.completions.create(
                deployment_id=app.config["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
        elif openai_type == "standard":
            # Using standard OpenAI API
            model = app.config.get("OPENAI_MODEL", "gpt-4o")
            
            completion = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
        else:
            raise Exception("Unknown OpenAI client type")
            
        # Extract response from the client response format
        response_text = completion.choices[0].message.content.strip()
        return response_text
        
    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        raise e

def generate_tasks(industry, company_name=None, intern_details=None, week_number=1, difficulty=None):
    """
    Generate internship tasks using the AI supervisor.
    
    Args:
        industry (str): The industry for the internship
        company_name (str, optional): The company name
        intern_details (dict, optional): Details about the intern (major, interests, etc.)
        week_number (int): The week number in the internship
        difficulty (str, optional): The desired difficulty level
        
    Returns:
        list: List of task dictionaries
    """
    try:
        prompt = get_task_generation_prompt(
            industry, 
            company_name, 
            intern_details, 
            week_number, 
            difficulty
        )
        
        try:
            response_text = call_openai_api(prompt["system_message"], prompt["user_message"])
            tasks = json.loads(response_text)
            return tasks
        except Exception as e:
            logging.error(f"Error generating tasks with OpenAI: {str(e)}")
            logging.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            
            # Fallback tasks
            return generate_fallback_tasks(industry, week_number)
            
    except Exception as e:
        logging.error(f"Error in task generation: {str(e)}")
        return generate_fallback_tasks(industry, week_number)

def generate_fallback_tasks(industry, week_number):
    """
    Generate fallback tasks when OpenAI is unavailable.
    
    Args:
        industry (str): The industry for the internship
        week_number (int): The week number in the internship
        
    Returns:
        list: List of fallback task dictionaries
    """
    default_tasks = [
        {
            "title": f"Week {week_number} Research Assignment",
            "description": f"Research current trends and best practices in the {industry} industry.",
            "instructions": f"Conduct research using industry publications, websites, and academic sources to identify current trends in {industry}. Write a 500-word report summarizing your findings and highlighting 3-5 key developments that are shaping the industry today.",
            "difficulty": "medium",
            "points": 100
        },
        {
            "title": f"Week {week_number} Analysis Project",
            "description": f"Analyze a case study or scenario related to {industry}.",
            "instructions": f"Review the provided materials and analyze the key challenges, opportunities, and decisions involved. Prepare a detailed analysis that includes your recommendations and the rationale behind them.",
            "difficulty": "medium",
            "points": 120
        }
    ]
    
    if week_number == 1:
        default_tasks.append({
            "title": "Industry Introduction Assignment",
            "description": f"Get familiar with the key aspects of the {industry} industry.",
            "instructions": "Create a mind map or structured overview of the major companies, technologies, roles, and current challenges in this industry. Include at least 3 examples in each category.",
            "difficulty": "easy",
            "points": 80
        })
        
    return default_tasks

def generate_feedback(submission_content, task_title, task_description, industry, task_difficulty):
    """
    Generate feedback for a student's task submission.
    
    Args:
        submission_content (str): The content of the student's submission
        task_title (str): The title of the task
        task_description (str): The description of the task
        industry (str): The industry of the internship
        task_difficulty (str): The difficulty level of the task
        
    Returns:
        dict: Feedback including score and detailed comments
    """
    try:
        prompt = get_feedback_prompt(
            industry,
            task_title,
            task_description,
            submission_content,
            task_difficulty
        )
        
        try:
            response_text = call_openai_api(prompt["system_message"], prompt["user_message"])
            feedback_data = json.loads(response_text)
            return feedback_data
        except Exception as e:
            logging.error(f"Error generating feedback with OpenAI: {str(e)}")
            logging.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            
            # Fallback feedback
            return generate_fallback_feedback(task_title, task_difficulty)
            
    except Exception as e:
        logging.error(f"Error in feedback generation: {str(e)}")
        return generate_fallback_feedback(task_title, task_difficulty)

def generate_fallback_feedback(task_title, task_difficulty):
    """
    Generate fallback feedback when OpenAI is unavailable.
    
    Args:
        task_title (str): The title of the task
        task_difficulty (str): The difficulty level of the task
        
    Returns:
        dict: Feedback dictionary
    """
    # Vary feedback based on task difficulty
    if task_difficulty.lower() == "easy":
        score = 75
        feedback = f"Your submission for '{task_title}' shows a good understanding of the basic concepts. You've addressed the key requirements and demonstrated effort. To improve further, consider adding more specific examples and connecting your insights more directly to real-world applications."
    elif task_difficulty.lower() == "hard":
        score = 65
        feedback = f"Your submission for '{task_title}' shows commendable effort on this challenging task. You've introduced some good ideas, but your analysis could benefit from more depth and critical thinking. Try to address all aspects of the task requirements more thoroughly and support your arguments with stronger evidence."
    else:  # medium or any other
        score = 70
        feedback = f"Your submission for '{task_title}' demonstrates a solid understanding of the key concepts. Your work addresses the main requirements, but could be strengthened with more thorough analysis and specific examples. Consider expanding on your ideas and providing more concrete applications to improve your work."
    
    return {
        "score": score,
        "feedback": feedback,
        "next_steps": [
            "Review industry best practices related to this task",
            "Add more specific examples to illustrate your points",
            "Consider different perspectives or approaches to the problem"
        ]
    }

def ask_supervisor(question, user_profile=None, current_task=None, internship=None):
    """
    Get a response from the AI supervisor for a student's question.
    
    Args:
        question (str): The student's question
        user_profile (dict, optional): Information about the student
        current_task (dict, optional): The current task being worked on
        internship (dict, optional): Information about the internship
        
    Returns:
        str: The AI supervisor's response
    """
    try:
        # Get industry from internship or default to general
        industry = internship.get("industry", "professional") if internship else "professional"
        
        # Build internship progress if available
        internship_progress = None
        if internship:
            internship_progress = {
                "week": internship.get("current_week", 1),
                "completed_tasks": internship.get("completed_tasks", 0),
                "avg_score": internship.get("avg_score", 0)
            }
        
        prompt = get_chat_prompt(
            industry,
            question,
            user_profile,
            current_task,
            internship_progress
        )
        
        try:
            response_text = call_openai_api(prompt["system_message"], prompt["user_message"])
            return response_text
        except Exception as e:
            logging.error(f"Error generating chat response with OpenAI: {str(e)}")
            
            # Fallback response based on question content
            return generate_fallback_response(question, industry)
            
    except Exception as e:
        logging.error(f"Error in chat response generation: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties at the moment. Please try again later or contact support if the issue persists."

def generate_fallback_response(question, industry="professional"):
    """
    Generate a fallback response when OpenAI is unavailable.
    
    Args:
        question (str): The student's question
        industry (str): The industry context
        
    Returns:
        str: A fallback response
    """
    question_lower = question.lower()
    
    # Generate response based on keywords in the question
    if any(keyword in question_lower for keyword in ["internship", "program"]):
        return f"This virtual internship program is designed to provide you with hands-on experience in the {industry} industry. You'll complete realistic tasks, receive feedback, and develop valuable professional skills that will help you in your career."
    
    elif any(keyword in question_lower for keyword in ["task", "assignment", "submit"]):
        return "For your current task, focus on following the instructions carefully and submitting high-quality work before the deadline. Professional quality and attention to detail are important in workplace settings."
    
    elif any(keyword in question_lower for keyword in ["feedback", "score", "grade", "evaluation"]):
        return "Feedback is provided based on the quality of your work, attention to detail, and how well you've met the requirements of the task. Scores are calculated on a scale of 0-100, with higher scores reflecting professional-quality work."
    
    elif any(keyword in question_lower for keyword in ["help", "stuck", "confused", "difficult"]):
        return "If you're finding a task challenging, try breaking it down into smaller steps and tackling them one by one. The resources section provides helpful materials related to your current task. Remember that learning to overcome challenges independently is an important professional skill."
    
    elif any(keyword in question_lower for keyword in ["resource", "material", "learn", "article"]):
        return f"We provide various learning resources tailored to your {industry} internship tasks. These include articles, videos, and reference materials that will help you complete your assignments successfully and deepen your understanding of industry concepts."
    
    elif any(keyword in question_lower for keyword in ["certificate", "completion", "finish"]):
        return "Upon successful completion of your virtual internship, you'll receive a certificate detailing the skills you've developed and the tasks you've completed. This can be a valuable addition to your resume or portfolio."
    
    else:
        return f"Thank you for your question. As your virtual internship supervisor in the {industry} field, I'm here to provide guidance and support throughout your program. To give you the most helpful response, could you provide more specific details about what you're looking for help with?"

def suggest_resources(task_title, task_description, industry):
    """
    Suggest learning resources for a specific task.
    
    Args:
        task_title (str): The title of the task
        task_description (str): The description of the task
        industry (str): The industry of the internship
        
    Returns:
        list: List of suggested resources
    """
    try:
        prompt = get_resources_prompt(
            industry,
            task_title,
            task_description
        )
        
        try:
            response_text = call_openai_api(prompt["system_message"], prompt["user_message"])
            resources = json.loads(response_text)
            return resources
        except Exception as e:
            logging.error(f"Error generating resources with OpenAI: {str(e)}")
            logging.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            
            # Fallback resources
            return generate_fallback_resources(industry)
            
    except Exception as e:
        logging.error(f"Error in resource suggestion: {str(e)}")
        return generate_fallback_resources(industry)

def generate_fallback_resources(industry):
    """
    Generate fallback resources when OpenAI is unavailable.
    
    Args:
        industry (str): The industry context
        
    Returns:
        list: List of fallback resources
    """
    # Industry-specific resources
    industry_resources = {
        "Fintech": [
            {
                "title": "Introduction to Financial Technology",
                "type": "article",
                "description": "An overview of key concepts and innovations in the fintech industry.",
                "url": "https://example.com/fintech-introduction"
            },
            {
                "title": "Digital Banking Fundamentals",
                "type": "course",
                "description": "Learn the core principles of digital banking systems and services.",
                "url": "https://example.com/digital-banking-course"
            }
        ],
        "Healthcare": [
            {
                "title": "Healthcare Data Management Best Practices",
                "type": "article",
                "description": "Guidelines for effectively managing and securing healthcare data.",
                "url": "https://example.com/healthcare-data-management"
            },
            {
                "title": "Introduction to Medical Informatics",
                "type": "course",
                "description": "An overview of how information technology is applied in healthcare settings.",
                "url": "https://example.com/medical-informatics"
            }
        ],
        "Marketing": [
            {
                "title": "Digital Marketing Strategy Framework",
                "type": "article",
                "description": "A comprehensive approach to developing effective digital marketing strategies.",
                "url": "https://example.com/digital-marketing-framework"
            },
            {
                "title": "Social Media Analytics Fundamentals",
                "type": "course",
                "description": "Learn how to measure and analyze social media performance metrics.",
                "url": "https://example.com/social-media-analytics"
            }
        ],
        "Technology & IT": [
            {
                "title": "Software Development Life Cycle Guide",
                "type": "article",
                "description": "A comprehensive overview of the software development process.",
                "url": "https://example.com/sdlc-guide"
            },
            {
                "title": "Introduction to Cloud Computing",
                "type": "course",
                "description": "Learn the fundamentals of cloud architecture and services.",
                "url": "https://example.com/cloud-computing-intro"
            }
        ],
        "Business & Finance": [
            {
                "title": "Financial Analysis Techniques",
                "type": "article",
                "description": "Methods for analyzing financial statements and business performance.",
                "url": "https://example.com/financial-analysis"
            },
            {
                "title": "Business Strategy Fundamentals",
                "type": "course",
                "description": "Core concepts in developing and implementing business strategies.",
                "url": "https://example.com/business-strategy"
            }
        ],
        "Education": [
            {
                "title": "Instructional Design Best Practices",
                "type": "article",
                "description": "Principles for creating effective learning experiences and materials.",
                "url": "https://example.com/instructional-design"
            },
            {
                "title": "Educational Technology Integration",
                "type": "course",
                "description": "Strategies for incorporating technology into educational settings.",
                "url": "https://example.com/edtech-integration"
            }
        ],
        "Environmental Science & Sustainability": [
            {
                "title": "Environmental Impact Assessment Methods",
                "type": "article",
                "description": "Techniques for evaluating environmental effects of projects and policies.",
                "url": "https://example.com/environmental-assessment"
            },
            {
                "title": "Sustainability Metrics and Reporting",
                "type": "course",
                "description": "Framework for measuring and communicating sustainability performance.",
                "url": "https://example.com/sustainability-metrics"
            }
        ],
        "Media & Communications": [
            {
                "title": "Effective Media Writing Techniques",
                "type": "article",
                "description": "Guidelines for creating compelling content across media platforms.",
                "url": "https://example.com/media-writing"
            },
            {
                "title": "Content Strategy Development",
                "type": "course",
                "description": "Approaches to planning, creating, and managing content.",
                "url": "https://example.com/content-strategy"
            }
        ],
        "Law & Government": [
            {
                "title": "Legal Research Methodology",
                "type": "article",
                "description": "Techniques for conducting thorough and effective legal research.",
                "url": "https://example.com/legal-research"
            },
            {
                "title": "Public Policy Analysis Framework",
                "type": "course",
                "description": "Structured approach to analyzing and evaluating public policies.",
                "url": "https://example.com/policy-analysis"
            }
        ],
        "Arts & Design": [
            {
                "title": "Design Thinking Process Guide",
                "type": "article",
                "description": "Step-by-step approach to creative problem-solving through design.",
                "url": "https://example.com/design-thinking"
            },
            {
                "title": "Visual Communication Principles",
                "type": "course",
                "description": "Fundamentals of creating effective visual content and messaging.",
                "url": "https://example.com/visual-communication"
            }
        ]
    }
    
    # Get industry-specific resources or default ones
    resources = industry_resources.get(industry, [
        {
            "title": "Professional Communication Skills",
            "type": "article",
            "description": "Techniques for effective written and verbal communication in professional settings.",
            "url": "https://example.com/professional-communication"
        },
        {
            "title": "Problem-Solving Methods for Professionals",
            "type": "course",
            "description": "Structured approaches to analyzing and solving workplace challenges.",
            "url": "https://example.com/problem-solving"
        }
    ])
    
    # Add general resources
    resources.append({
        "title": "Professional Development Planning",
        "type": "guide",
        "description": "Framework for setting career goals and developing professional skills.",
        "url": "https://example.com/professional-development"
    })
    
    return resources

def generate_certificate(user_name, internship_title, industry, tasks_completed, avg_score):
    """
    Generate a certificate for a completed internship.
    
    Args:
        user_name (str): The user's full name
        internship_title (str): The title of the internship
        industry (str): The industry of the internship
        tasks_completed (int): Number of tasks completed
        avg_score (float): Average score across all tasks
        
    Returns:
        dict: Certificate details
    """
    try:
        prompt = get_certificate_prompt(
            industry,
            user_name,
            internship_title,
            tasks_completed,
            avg_score
        )
        
        try:
            response_text = call_openai_api(prompt["system_message"], prompt["user_message"])
            certificate_data = json.loads(response_text)
            return certificate_data
        except Exception as e:
            logging.error(f"Error generating certificate with OpenAI: {str(e)}")
            logging.error(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            
            # Fallback certificate
            return generate_fallback_certificate(user_name, internship_title, industry, avg_score)
            
    except Exception as e:
        logging.error(f"Error in certificate generation: {str(e)}")
        return generate_fallback_certificate(user_name, internship_title, industry, avg_score)

def generate_fallback_certificate(user_name, internship_title, industry, avg_score):
    """
    Generate a fallback certificate when OpenAI is unavailable.
    
    Args:
        user_name (str): The user's full name
        internship_title (str): The title of the internship
        industry (str): The industry of the internship
        avg_score (float): Average score across all tasks
        
    Returns:
        dict: Certificate details
    """
    # Industry-specific skills
    industry_skills = {
        "Fintech": "Financial analysis, Digital payment systems, Regulatory compliance, Data-driven decision making, Financial technology tools",
        "Healthcare": "Healthcare data analysis, Medical information management, Healthcare compliance, Patient experience design, Health informatics",
        "Marketing": "Digital marketing strategy, Marketing analytics, Campaign management, Social media optimization, Content creation",
        "Technology & IT": "Software development, System architecture, Technical problem-solving, Code optimization, Development lifecycle management",
        "Business & Finance": "Financial modeling, Business analysis, Strategic planning, Risk assessment, Project management",
        "Education": "Instructional design, Curriculum development, Educational assessment, Learning technologies, Student engagement strategies",
        "Environmental Science & Sustainability": "Environmental analysis, Sustainability assessment, Conservation planning, Ecological research, Environmental policy analysis",
        "Media & Communications": "Media content creation, Public relations strategy, Audience engagement, Strategic communication, Media analytics",
        "Law & Government": "Legal research, Policy analysis, Regulatory compliance, Administrative procedures, Stakeholder communication",
        "Arts & Design": "Visual design principles, User experience design, Creative problem-solving, Design software proficiency, Brand identity development"
    }
    
    # Get industry-specific skills or default ones
    skills = industry_skills.get(industry, "Professional communication, Critical thinking, Problem-solving, Project management, Industry research")
    
    performance_level = "excellent" if avg_score >= 90 else "strong" if avg_score >= 80 else "good" if avg_score >= 70 else "satisfactory"
    
    return {
        "title": f"Certificate of Completion: {internship_title}",
        "description": f"This certifies that {user_name} has successfully completed the {internship_title} virtual internship program in the {industry} industry. Throughout this program, {user_name} demonstrated {performance_level} performance in completing professional tasks and projects, achieving an overall score of {avg_score:.1f}/100. This internship provided hands-on experience in real-world scenarios typical of the {industry} field.",
        "skills_acquired": skills
    }