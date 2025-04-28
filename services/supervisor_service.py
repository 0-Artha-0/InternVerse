import logging
import os
import json
from openai import OpenAI, AzureOpenAI
from app import app

logger = logging.getLogger(__name__)

# Configure OpenAI client
if app.config.get("AZURE_OPENAI_KEY"):
    logger.info("AI Supervisor: Azure OpenAI client configured")
    client = AzureOpenAI(
        api_key=app.config.get("AZURE_OPENAI_KEY"),
        api_version=app.config.get("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
        azure_endpoint=app.config.get("AZURE_OPENAI_ENDPOINT"),
    )
    deployment_name = app.config.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
else:
    # Fallback to standard OpenAI if Azure credentials aren't available
    logger.info("AI Supervisor: Standard OpenAI client configured")
    client = OpenAI(api_key=app.config.get("OPENAI_API_KEY"))
    deployment_name = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024

def ask_question(question, user_profile, internship=None, task=None):
    """
    Generate a response to a user's question using the AI supervisor bot
    
    Args:
        question (str): The user's question
        user_profile (UserProfile): The user's profile
        internship (InternshipTrack, optional): The current internship
        task (Task, optional): The current task
        
    Returns:
        str: The AI supervisor's response
    """
    # Create context from user profile and internship details
    context = f"You are an AI supervisor for a virtual internship program. "
    context += f"You are helping a student named {user_profile.full_name or 'a student'} "
    
    if user_profile.major:
        context += f"who is studying {user_profile.major} "
    
    if internship:
        context += f"during their {internship.industry.name} internship titled '{internship.title}'. "
    else:
        context += "who is interested in starting a virtual internship. "
    
    if task:
        context += f"They are currently working on a task titled '{task.title}'. "
        context += f"Task description: {task.description}. "
        context += f"Task instructions: {task.instructions}. "
    
    prompt = context + f"\n\nStudent question: {question}\n\nYour response (be helpful, encouraging, and professional):"
    
    try:
        logger.info(f"Sending request to AI with question: {question[:50]}...")
        
        # Use the same code path regardless of Azure or OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        logger.info(f"Received AI response: {answer[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"Error generating supervisor response: {str(e)}")
        return "I apologize, but I'm having trouble processing your question at the moment. Please try again later or contact support if the issue persists."


def generate_feedback(submission_content, task_title, task_description, task_difficulty, industry="professional"):
    """
    Generate feedback for a student's task submission
    
    Args:
        submission_content (str): The content of the student's submission
        task_title (str): The title of the task
        task_description (str): The description of the task
        task_difficulty (str): The difficulty level of the task
        industry (str, optional): The industry context
        
    Returns:
        dict: Feedback including score and detailed comments
    """
    system_prompt = (
        f"You are an experienced mentor in the {industry} industry evaluating intern submissions. "
        f"You need to provide detailed, constructive feedback on a submission for a task titled '{task_title}'. "
        f"The task difficulty is {task_difficulty}. "
        f"Task description: {task_description}. "
        "Evaluate the work as if it were submitted by a real intern. "
        "Be constructive but realistic in your assessment. "
        "Respond with a JSON object having these fields: "
        "score (0-100), feedback_summary, strengths (list), areas_for_improvement (list), and next_steps (list)."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": submission_content}
            ],
            max_tokens=1000,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        feedback_text = response.choices[0].message.content
        feedback = json.loads(feedback_text)
        
        # Ensure all expected fields are present
        if not isinstance(feedback, dict):
            feedback = {}
        
        feedback.setdefault("score", 70)
        feedback.setdefault("feedback_summary", "Thank you for your submission.")
        feedback.setdefault("strengths", ["Completed the task"])
        feedback.setdefault("areas_for_improvement", ["Continue practicing"])
        feedback.setdefault("next_steps", ["Review the feedback and apply it to future tasks"])
        
        return feedback
    except Exception as e:
        logger.error(f"Error generating feedback: {str(e)}")
        return {
            "score": 70,
            "feedback_summary": "Thank you for your submission. The feedback system is currently experiencing technical difficulties.",
            "strengths": ["Completed the task"],
            "areas_for_improvement": ["Continue practicing"],
            "next_steps": ["Please try again later if you need detailed feedback"]
        }


def suggest_resources(task_title, task_description, industry):
    """
    Suggest learning resources for a specific task
    
    Args:
        task_title (str): The title of the task
        task_description (str): The description of the task
        industry (str): The industry of the internship
        
    Returns:
        list: List of suggested resources with titles and brief descriptions
    """
    system_prompt = (
        f"You are a knowledgeable resource advisor in the {industry} industry. "
        f"Provide a list of 3-5 quality learning resources related to the following task that an intern needs to complete: "
        f"Task: '{task_title}' - {task_description}. "
        f"For each resource, include a title, brief description, and resource type (e.g., article, video, tutorial). "
        f"Respond with a JSON array where each object has title, description, and type fields."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Suggest resources for: {task_title}"}
            ],
            max_tokens=800,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        resources_text = response.choices[0].message.content
        resources = json.loads(resources_text)
        
        # Ensure we have a list of resources
        if isinstance(resources, dict) and "resources" in resources:
            resources = resources["resources"]
        elif not isinstance(resources, list):
            resources = []
        
        return resources
    except Exception as e:
        logger.error(f"Error suggesting resources: {str(e)}")
        return [
            {
                "title": "Getting Started Guide",
                "description": "A basic resource to help you get started with this task. Note: resource suggestions are currently limited due to technical issues.",
                "type": "guide"
            }
        ]


def generate_certificate_for_internship(user_name, internship_title, industry, tasks_completed, avg_score):
    """
    Generate a certificate for a completed internship
    
    Args:
        user_name (str): The user's full name
        internship_title (str): The title of the internship
        industry (str): The industry of the internship
        tasks_completed (int): Number of tasks completed
        avg_score (float): Average score across all tasks
        
    Returns:
        dict: Certificate details including title, description, and skills acquired
    """
    system_prompt = (
        f"You are creating an official certificate for {user_name} who has completed a virtual internship "
        f"titled '{internship_title}' in the {industry} industry. "
        f"They completed {tasks_completed} tasks with an average score of {avg_score}/100. "
        f"Create a professional certificate description and list of skills acquired during this internship. "
        f"Respond with a JSON object having these fields: title, description, and skills_acquired (list of strings)."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate certificate content"}
            ],
            max_tokens=800,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        certificate_text = response.choices[0].message.content
        certificate = json.loads(certificate_text)
        
        # Ensure expected fields are present
        certificate.setdefault("title", f"{industry} Virtual Internship Certificate")
        certificate.setdefault("description", f"This certifies that {user_name} has successfully completed the {internship_title} virtual internship program.")
        certificate.setdefault("skills_acquired", [f"{industry} fundamentals", "Professional communication", "Problem solving"])
        
        return certificate
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        return {
            "title": f"{industry} Virtual Internship Certificate",
            "description": f"This certifies that {user_name} has successfully completed the {internship_title} virtual internship program.",
            "skills_acquired": [f"{industry} fundamentals", "Professional communication", "Problem solving"]
        }