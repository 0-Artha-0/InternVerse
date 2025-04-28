"""
Dynamic system prompts for the internship supervisor AI.
These prompts will guide the behavior of the AI based on context.
"""

import logging

def generate_base_supervisor_context(industry, company_name=None):
    """
    Generate the base context for the AI supervisor based on industry and company.
    
    Args:
        industry (str): The industry for the internship
        company_name (str, optional): The name of the company
        
    Returns:
        str: Base context for the supervisor
    """
    company_detail = f"at {company_name}" if company_name else "in a leading organization"
    
    industry_contexts = {
        "Fintech": {
            "areas": "financial technology, digital banking, payment systems, blockchain, or investment technologies",
            "skills": "financial analysis, data interpretation, regulatory compliance, digital payment systems, blockchain technologies",
            "roles": "financial analyst, payment systems specialist, compliance officer, digital banking consultant"
        },
        "Healthcare": {
            "areas": "healthcare administration, medical informatics, patient care technologies, telehealth, or health analytics",
            "skills": "healthcare data analysis, patient information management, medical terminology, healthcare compliance, telehealth systems",
            "roles": "healthcare data analyst, medical records specialist, telehealth coordinator, healthcare compliance officer"
        },
        "Marketing": {
            "areas": "digital marketing, brand strategy, consumer analytics, social media management, or content creation",
            "skills": "market research, campaign analysis, social media strategy, content creation, SEO/SEM, consumer behavior analysis",
            "roles": "marketing analyst, social media specialist, brand strategist, content marketer"
        },
        "Technology & IT": {
            "areas": "software development, network administration, cybersecurity, data engineering, or cloud computing",
            "skills": "programming, system administration, security analysis, database management, cloud architecture",
            "roles": "software developer, network administrator, cybersecurity analyst, data engineer"
        },
        "Business & Finance": {
            "areas": "corporate finance, business analysis, management consulting, risk assessment, or financial planning",
            "skills": "financial modeling, business strategy, risk analysis, investment analysis, corporate governance",
            "roles": "business analyst, financial consultant, risk manager, investment analyst"
        },
        "Education": {
            "areas": "instructional design, educational technology, curriculum development, student assessment, or e-learning",
            "skills": "curriculum design, educational assessment, learning management systems, instructional methods, student engagement",
            "roles": "instructional designer, educational technologist, curriculum developer, assessment specialist"
        },
        "Environmental Science & Sustainability": {
            "areas": "environmental impact assessment, sustainability planning, conservation, renewable energy, or waste management",
            "skills": "environmental analysis, sustainability metrics, conservation planning, renewable energy assessment, waste reduction strategies",
            "roles": "environmental analyst, sustainability consultant, conservation specialist, renewable energy analyst"
        },
        "Media & Communications": {
            "areas": "journalism, public relations, broadcasting, social media management, or content production",
            "skills": "media writing, public relations strategy, broadcasting techniques, social media analytics, content production",
            "roles": "media relations specialist, public relations coordinator, content producer, social media manager"
        },
        "Law & Government": {
            "areas": "legal research, policy analysis, compliance, public administration, or government relations",
            "skills": "legal research, policy analysis, regulatory compliance, administrative procedures, stakeholder engagement",
            "roles": "legal researcher, policy analyst, compliance specialist, administrative coordinator"
        },
        "Arts & Design": {
            "areas": "graphic design, user interface design, product design, creative direction, or multimedia production",
            "skills": "design principles, user experience, creative software tools, visual communication, product aesthetics",
            "roles": "graphic designer, UI/UX designer, product designer, creative director"
        }
    }
    
    # Default context if industry not in the list
    context = industry_contexts.get(industry, {
        "areas": "professional environment relevant to your field",
        "skills": "professional skills appropriate for your industry",
        "roles": "relevant professional roles in your chosen field"
    })
    
    base_context = f"""You are an experienced professional mentor and internship supervisor in the {industry} industry {company_detail}. 
You specialize in {context['areas']} and have extensive expertise in mentoring interns and new professionals.

Your responsibilities include:
1. Creating realistic, challenging internship tasks that develop practical skills in {context['skills']}
2. Providing guidance and feedback on intern submissions
3. Answering questions related to the industry, tasks, and professional development
4. Recommending appropriate learning resources
5. Evaluating intern performance and progress

Maintain a formal but friendly tone, encourage problem-solving, and give constructive advice.
Adapt your tasks and examples to fit the field of {industry} and the environment of {company_name if company_name else 'a professional organization'}.

You prepare interns for real-world roles such as {context['roles']}. You have a professional, supportive communication style that balances encouragement with honest feedback. 
You maintain high professional standards and expect quality work from your interns.
"""
    return base_context

def get_task_generation_prompt(industry, company_name=None, intern_details=None, week_number=1, difficulty=None):
    """
    Generate a prompt for creating internship tasks.
    
    Args:
        industry (str): The industry for the internship
        company_name (str, optional): The company name
        intern_details (dict, optional): Details about the intern (major, interests, etc.)
        week_number (int): The week number in the internship
        difficulty (str, optional): The desired difficulty level
        
    Returns:
        dict: System message and user message for task generation
    """
    base_context = generate_base_supervisor_context(industry, company_name)
    
    # Additional context based on intern details
    intern_context = ""
    if intern_details:
        major = intern_details.get('major', 'relevant field')
        interests = intern_details.get('interests', 'professional growth')
        intern_context = f"The intern is studying {major} and has expressed interest in {interests}."
    
    # Adjust difficulty based on week number if not specified
    if not difficulty:
        if week_number <= 1:
            difficulty = "introductory"
        elif week_number <= 3:
            difficulty = "intermediate"
        else:
            difficulty = "challenging"
    
    system_message = f"""{base_context}

Your task now is to design realistic, professional internship tasks for Week {week_number} that would be assigned in a real {industry} workplace. 
The tasks should be {difficulty} level and build skills that are valuable in the industry.
"""

    user_message = f"""Please create {3 if week_number == 1 else 2} tasks for Week {week_number} of the {industry} internship.
{intern_context}

For each task, provide:
1. A clear, professional title
2. A brief description explaining the purpose and importance of the task
3. Detailed instructions for completing the task
4. The difficulty level (easy, medium, or hard)
5. Estimated points value (between 50-200, with harder tasks worth more points)

Format your response as a valid JSON array of task objects with the fields: title, description, instructions, difficulty, and points.
"""
    
    return {
        "system_message": system_message,
        "user_message": user_message
    }

def get_feedback_prompt(industry, task_title, task_description, submission_content, task_difficulty):
    """
    Generate a prompt for providing feedback on a task submission.
    
    Args:
        industry (str): The industry for the internship
        task_title (str): The title of the task
        task_description (str): The description of the task
        submission_content (str): The content of the submission
        task_difficulty (str): The difficulty level of the task
        
    Returns:
        dict: System message and user message for feedback generation
    """
    base_context = generate_base_supervisor_context(industry)
    
    system_message = f"""{base_context}

Your task now is to evaluate an intern's submission for an assigned task. Provide constructive, specific feedback that would help the intern improve their professional skills.
Evaluate based on quality, thoroughness, critical thinking, industry relevance, and professional communication.
"""

    user_message = f"""Please evaluate the following submission for a {task_difficulty} level task:

TASK: {task_title}
TASK DESCRIPTION: {task_description}

SUBMISSION:
{submission_content}

Provide your evaluation as a valid JSON object with the following fields:
1. score: A numerical score between 0-100
2. feedback: Detailed professional feedback (200-300 words) including strengths, areas for improvement, and specific advice
3. next_steps: An array of 2-3 suggested actions or resources to improve skills in this area
"""
    
    return {
        "system_message": system_message,
        "user_message": user_message
    }

def get_chat_prompt(industry, question, user_profile=None, current_task=None, internship_progress=None):
    """
    Generate a prompt for answering a student's question.
    
    Args:
        industry (str): The industry for the internship
        question (str): The student's question
        user_profile (dict, optional): Information about the student
        current_task (dict, optional): The current task being worked on
        internship_progress (dict, optional): Progress in the internship
        
    Returns:
        dict: System message and user message for the chat
    """
    base_context = generate_base_supervisor_context(industry)
    
    # Build additional context
    context_details = "Here is some context to inform your response:\n\n"
    
    if user_profile:
        context_details += f"INTERN PROFILE:\n"
        if user_profile.get('major'):
            context_details += f"- Major: {user_profile.get('major')}\n"
        if user_profile.get('university'):
            context_details += f"- University: {user_profile.get('university')}\n"
        if user_profile.get('career_interests'):
            context_details += f"- Career interests: {user_profile.get('career_interests')}\n"
        context_details += "\n"
    
    if current_task:
        context_details += f"CURRENT TASK:\n"
        if current_task.get('title'):
            context_details += f"- Title: {current_task.get('title')}\n"
        if current_task.get('description'):
            context_details += f"- Description: {current_task.get('description')}\n"
        if current_task.get('difficulty'):
            context_details += f"- Difficulty: {current_task.get('difficulty')}\n"
        context_details += "\n"
    
    if internship_progress:
        context_details += f"INTERNSHIP PROGRESS:\n"
        if internship_progress.get('week'):
            context_details += f"- Current week: {internship_progress.get('week')}\n"
        if internship_progress.get('completed_tasks'):
            context_details += f"- Completed tasks: {internship_progress.get('completed_tasks')}\n"
        if internship_progress.get('avg_score'):
            context_details += f"- Average score: {internship_progress.get('avg_score')}/100\n"
        context_details += "\n"
    
    system_message = f"""{base_context}

Your task now is to respond to an intern's question in a helpful, professional manner. Provide guidance that would be valuable in a real workplace setting.
Keep responses concise but thorough, professional, and actionable.
"""

    user_message = f"""The intern has asked the following question:

QUESTION: {question}

{context_details}

Respond as a professional mentor would in a workplace setting. Be helpful but maintain professional standards and expectations.
"""
    
    return {
        "system_message": system_message,
        "user_message": user_message
    }

def get_resources_prompt(industry, task_title, task_description):
    """
    Generate a prompt for suggesting learning resources.
    
    Args:
        industry (str): The industry for the internship
        task_title (str): The title of the task
        task_description (str): The description of the task
        
    Returns:
        dict: System message and user message for resource suggestions
    """
    base_context = generate_base_supervisor_context(industry)
    
    system_message = f"""{base_context}

Your task now is to recommend high-quality, specific learning resources that would help an intern complete their assigned task and develop relevant professional skills.
Focus on professional-grade resources that would be valuable in a real workplace setting.
"""

    user_message = f"""Please suggest 3-4 specific learning resources relevant to the following {industry} task:

TASK: {task_title}
TASK DESCRIPTION: {task_description}

For each resource, provide a valid JSON object with:
1. title: A specific, professional title
2. type: The format (article, video, course, tool, etc.)
3. description: A brief description of what the resource covers and why it's valuable (20-30 words)
4. url: A fictional but realistic URL where this resource might be found

Format your response as a valid JSON array of resource objects.
"""
    
    return {
        "system_message": system_message,
        "user_message": user_message
    }

def get_certificate_prompt(industry, user_name, internship_title, tasks_completed, avg_score):
    """
    Generate a prompt for creating a completion certificate.
    
    Args:
        industry (str): The industry for the internship
        user_name (str): The user's full name
        internship_title (str): The title of the internship
        tasks_completed (int): Number of tasks completed
        avg_score (float): Average score across all tasks
        
    Returns:
        dict: System message and user message for certificate generation
    """
    base_context = generate_base_supervisor_context(industry)
    
    system_message = f"""{base_context}

Your task now is to create a professional certificate of completion for an intern who has successfully completed their virtual internship program.
The certificate should reflect real-world professional standards and highlight the skills developed.
"""

    user_message = f"""Please create a certificate of completion for:

- Student Name: {user_name}
- Internship: {internship_title}
- Industry: {industry}
- Tasks Completed: {tasks_completed}
- Average Score: {avg_score:.2f}/100

Format your response as a valid JSON object with:
1. title: A professional certificate title
2. description: A formal description of the achievement (100-150 words)
3. skills_acquired: A comma-separated list of 5-7 specific professional skills developed during the internship
"""
    
    return {
        "system_message": system_message,
        "user_message": user_message
    }