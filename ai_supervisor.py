import os
import logging
from app import app
import json
from supervisor_service import (
    ask_supervisor as svc_ask_supervisor,
    generate_tasks as svc_generate_tasks,
    generate_feedback as svc_generate_feedback,
    suggest_resources as svc_suggest_resources,
    generate_certificate as svc_generate_certificate
)

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
    try:
        # Prepare user profile data
        user_data = None
        if user_profile:
            user_data = {
                "major": user_profile.major,
                "university": user_profile.university,
                "career_interests": user_profile.career_interests
            }
        
        # Prepare internship data
        internship_data = None
        if internship:
            internship_data = {
                "industry": internship.industry.name if hasattr(internship, "industry") and internship.industry else "professional",
                "title": internship.title,
                "description": internship.description,
                "current_week": (internship.progress // 25) + 1,  # Estimate week from progress
                "completed_tasks": len([t for t in internship.tasks if t.status == "evaluated"]) if hasattr(internship, "tasks") else 0,
                "avg_score": sum([s.score for s in [t.submissions[0] for t in internship.tasks if t.submissions and t.submissions[0].score is not None]]) / 
                            len([t for t in internship.tasks if t.submissions and t.submissions[0].score is not None]) if hasattr(internship, "tasks") and 
                            any(t.submissions and t.submissions[0].score is not None for t in internship.tasks) else 0
            }
        
        # Prepare task data
        task_data = None
        if task:
            task_data = {
                "title": task.title,
                "description": task.description,
                "instructions": task.instructions,
                "difficulty": task.difficulty,
                "status": task.status
            }
        
        # Get industry from internship or default
        industry = internship.industry.name if internship and hasattr(internship, "industry") and internship.industry else "professional"
        
        # Call the supervisor service
        response = svc_ask_supervisor(question, user_data, task_data, internship_data)
        return response
        
    except Exception as e:
        logging.error(f"Error in AI supervisor: {str(e)}")
        return "I apologize, but I'm having trouble processing your question right now. Please try again later or contact support if the issue persists."

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
    try:
        # Call the supervisor service
        feedback_data = svc_generate_feedback(submission_content, task_title, task_description, industry, task_difficulty)
        return feedback_data
    except Exception as e:
        logging.error(f"Error generating feedback: {str(e)}")
        # Return default feedback on general error
        return {
            "score": 70,
            "feedback": "Thank you for your submission. Your work demonstrates understanding of the key concepts, but could benefit from more depth and detail. Consider expanding your analysis and providing more specific examples to strengthen your work.",
            "next_steps": ["Review industry best practices", "Add more specific examples", "Consider different perspectives"]
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
    try:
        # Call the supervisor service
        resources = svc_suggest_resources(task_title, task_description, industry)
        return resources
    except Exception as e:
        logging.error(f"Error suggesting resources: {str(e)}")
        
        # Industry-specific default resources
        industry_resources = {
            "finance": [
                {
                    "title": "Financial Analysis Fundamentals",
                    "type": "course",
                    "url": "https://www.coursera.org/learn/financial-analysis",
                    "description": "Learn essential financial analysis techniques used by professionals."
                },
                {
                    "title": "Wall Street Journal - Finance Section",
                    "type": "article",
                    "url": "https://www.wsj.com/finance",
                    "description": "Latest news and analysis on finance, markets, and investing."
                },
                {
                    "title": "CFA Institute Resources",
                    "type": "article",
                    "url": "https://www.cfainstitute.org/en/membership/professional-development/refresher-readings",
                    "description": "Professional materials for financial analysts and investment professionals."
                }
            ],
            "technology": [
                {
                    "title": "Introduction to Software Development",
                    "type": "course",
                    "url": "https://www.edx.org/learn/computer-programming",
                    "description": "Learn fundamentals of programming and software development."
                },
                {
                    "title": "GitHub Learning Lab",
                    "type": "tutorial",
                    "url": "https://lab.github.com/",
                    "description": "Interactive tutorials for learning Git and development workflows."
                },
                {
                    "title": "AWS Documentation",
                    "type": "documentation",
                    "url": "https://docs.aws.amazon.com/",
                    "description": "Comprehensive guides for cloud services and application development."
                }
            ],
            "healthcare": [
                {
                    "title": "Introduction to Healthcare Systems",
                    "type": "course",
                    "url": "https://www.coursera.org/learn/healthcare-system",
                    "description": "Overview of healthcare delivery, policy, and management."
                },
                {
                    "title": "World Health Organization Resources",
                    "type": "article",
                    "url": "https://www.who.int/publications/i",
                    "description": "Guidelines and research on healthcare practices and policies."
                },
                {
                    "title": "Healthcare IT Best Practices",
                    "type": "article",
                    "url": "https://www.himss.org/resources",
                    "description": "Resources for healthcare information technology professionals."
                }
            ],
            "marketing": [
                {
                    "title": "Digital Marketing Fundamentals",
                    "type": "course",
                    "url": "https://www.coursera.org/learn/digital-marketing",
                    "description": "Comprehensive introduction to modern marketing techniques."
                },
                {
                    "title": "HubSpot Academy",
                    "type": "tutorial",
                    "url": "https://academy.hubspot.com/",
                    "description": "Free certification courses on marketing, sales, and customer service."
                },
                {
                    "title": "Content Marketing Institute",
                    "type": "article",
                    "url": "https://contentmarketinginstitute.com/",
                    "description": "Resources and guides for content marketing strategies."
                }
            ],
            "education": [
                {
                    "title": "Modern Teaching Methods",
                    "type": "course",
                    "url": "https://www.edx.org/learn/education",
                    "description": "Learn about innovative approaches to teaching and learning."
                },
                {
                    "title": "Education Resources Information Center",
                    "type": "article",
                    "url": "https://eric.ed.gov/",
                    "description": "Database of education research and information."
                },
                {
                    "title": "Khan Academy",
                    "type": "tutorial",
                    "url": "https://www.khanacademy.org/",
                    "description": "Free educational resources for students and teachers."
                }
            ]
        }
        
        # General resources for all industries
        general_resources = [
            {
                "title": "Introduction to Professional Communication",
                "type": "article",
                "url": "https://hbr.org/topic/communication",
                "description": "Harvard Business Review articles on effective communication in professional settings."
            },
            {
                "title": "Project Management Institute",
                "type": "article",
                "url": "https://www.pmi.org/learning/library",
                "description": "Resources for project management best practices across industries."
            },
            {
                "title": "LinkedIn Learning",
                "type": "course",
                "url": "https://www.linkedin.com/learning/",
                "description": "Professional courses on business, creative, and technology skills."
            }
        ]
        
        # If we have resources for this industry, use them, otherwise use general resources
        return industry_resources.get(industry.lower(), general_resources)

def generate_tasks_for_internship(industry, intern_details=None, company_name=None, week_number=1, difficulty=None):
    """
    Generate tasks for a specific week of an internship
    
    Args:
        industry (str): The industry for the internship
        intern_details (dict, optional): Details about the intern (major, interests, etc.)
        company_name (str, optional): The company name for the internship
        week_number (int): The week number of the internship
        difficulty (str, optional): The desired difficulty level
        
    Returns:
        list: List of task dictionaries with title, description, instructions, difficulty, and points
    """
    try:
        # Prepare intern details if provided
        intern_data = None
        if isinstance(intern_details, dict):
            intern_data = intern_details
        elif hasattr(intern_details, 'major') and hasattr(intern_details, 'career_interests'):
            intern_data = {
                "major": intern_details.major,
                "interests": intern_details.career_interests
            }
        
        # Call the supervisor service
        tasks = svc_generate_tasks(
            industry=industry,
            company_name=company_name,
            intern_details=intern_data,
            week_number=week_number,
            difficulty=difficulty
        )
        
        return tasks
    except Exception as e:
        logging.error(f"Error generating tasks: {str(e)}")
        # Return default tasks on error
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
    try:
        # Call the supervisor service
        certificate_data = svc_generate_certificate(
            user_name=user_name,
            internship_title=internship_title, 
            industry=industry,
            tasks_completed=tasks_completed,
            avg_score=avg_score
        )
        
        return certificate_data
    except Exception as e:
        logging.error(f"Error generating certificate: {str(e)}")
        # Return default certificate on error
        performance_level = "excellent" if avg_score >= 90 else "strong" if avg_score >= 80 else "good" if avg_score >= 70 else "satisfactory"
        
        # Default industry-specific skills
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
        
        skills = industry_skills.get(industry, "Professional communication, Critical thinking, Problem-solving, Project management, Industry research")
        
        return {
            "title": f"Certificate of Completion: {internship_title}",
            "description": f"This certifies that {user_name} has successfully completed the {internship_title} virtual internship program in the {industry} industry. Throughout this program, {user_name} demonstrated {performance_level} performance in completing professional tasks and projects, achieving an overall score of {avg_score:.1f}/100. This internship provided hands-on experience in real-world scenarios typical of the {industry} field.",
            "skills_acquired": skills
        }
