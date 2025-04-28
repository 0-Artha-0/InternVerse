import logging
import json
import requests
from datetime import datetime
from openai import OpenAI, AzureOpenAI
from app import app

logger = logging.getLogger(__name__)

# Configure OpenAI client
if app.config.get("AZURE_OPENAI_KEY"):
    logger.info("Azure OpenAI client configured")
    client = AzureOpenAI(
        api_key=app.config.get("AZURE_OPENAI_KEY"),
        api_version=app.config.get("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
        azure_endpoint=app.config.get("AZURE_OPENAI_ENDPOINT"),
    )
    deployment_name = app.config.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
else:
    # Fallback to standard OpenAI if Azure credentials aren't available
    client = OpenAI(api_key=app.config.get("OPENAI_API_KEY"))
    deployment_name = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024

# Configure Cosmos DB client
cosmos_endpoint = app.config.get("COSMOS_ENDPOINT")
cosmos_key = app.config.get("COSMOS_KEY")
cosmos_database = app.config.get("COSMOS_DATABASE", "internship-simulator")

if cosmos_endpoint and cosmos_key:
    try:
        from azure.cosmos import CosmosClient
        # Placeholder for CosmosDB integration
        cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
        cosmos_db = cosmos_client.get_database_client(cosmos_database)
        logger.info("Cosmos DB client configured")
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB client: {e}")
        cosmos_client = None
else:
    logger.warning("Cosmos DB credentials not found. Using fallback storage.")
    cosmos_client = None

# Configure Azure AI Search client
search_endpoint = app.config.get("AZURE_SEARCH_ENDPOINT")
search_key = app.config.get("AZURE_SEARCH_KEY")
search_index = app.config.get("AZURE_SEARCH_INDEX", "internship-resources")

if search_endpoint and search_key:
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        # Placeholder for Azure Search integration
        search_credential = AzureKeyCredential(search_key)
        search_client = SearchClient(search_endpoint, search_index, search_credential)
        logger.info("Azure Search client configured")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search client: {e}")
        search_client = None
else:
    logger.warning("Azure Search credentials not found. Search functionality will be limited.")
    search_client = None

def generate_companies_and_roles(industry):
    """
    Generate companies and roles for a specific industry using OpenAI
    
    Args:
        industry (str): The industry to generate companies and roles for
        
    Returns:
        dict: Contains 'companies' and 'roles' lists
    """
    system_prompt = (
        "You are a career and industry expert. "
        "Create a set of realistic companies and corresponding job roles for a specific industry. "
        "For each company, provide a name, description, and location. "
        "For each role, provide a name, description, requirements, skills required, and experience level. "
        "Respond with a JSON object that contains two arrays: 'companies' and 'roles'."
    )
    
    user_prompt = (
        f"Generate 3-5 realistic companies for the {industry} industry, along with 2-3 internship roles for each company. "
        f"Companies should have: name, description, location. "
        f"Roles should have: name, description, company_name (matching one of the companies), requirements, "
        f"skills_required (comma-separated), and experience_level (Entry, Mid, or Senior)."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Ensure all expected fields are present
        if 'companies' not in result:
            result['companies'] = []
        if 'roles' not in result:
            result['roles'] = []
            
        return result
    except Exception as e:
        logger.error(f"Error generating companies and roles: {str(e)}")
        return {
            "companies": [],
            "roles": []
        }

def generate_internship(industry, major, interests):
    """
    Generate internship details using OpenAI
    
    Args:
        industry (str): The industry for the internship
        major (str): Student's major
        interests (str): Student's career interests
        
    Returns:
        dict: Internship details including title, description, and duration
    """
    system_prompt = (
        "You are an internship program designer. "
        "Create a detailed, professional description for a virtual internship program. "
        "Respond with a JSON object that includes title, description, and duration_weeks (integer between 4-12)."
    )
    
    user_prompt = (
        f"Generate a virtual internship for a student in the {industry} industry. "
        f"The student is majoring in {major} and has interests in {interests}."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        internship_text = response.choices[0].message.content
        internship = json.loads(internship_text)
        
        # Ensure all expected fields are present
        internship.setdefault("title", f"{industry} Virtual Internship")
        internship.setdefault("description", f"A comprehensive virtual internship experience in the {industry} industry.")
        internship.setdefault("duration_weeks", 8)
        
        return internship
    except Exception as e:
        logger.error(f"Error generating internship: {str(e)}")
        return {
            "title": f"{industry} Virtual Internship",
            "description": f"A comprehensive virtual internship experience in the {industry} industry.",
            "duration_weeks": 8
        }

def generate_tasks(internship_title, industry, major, week):
    """
    Generate tasks for a specific week of the internship
    
    Args:
        internship_title (str): The title of the internship
        industry (str): The industry for the internship
        major (str): Student's major
        week (int): The week number of the internship
        
    Returns:
        list: List of task dictionaries with title, description, instructions, difficulty, and points
    """
    system_prompt = (
        f"You are an internship coordinator for a program titled '{internship_title}' in the {industry} industry. "
        f"Create a list of 3-5 realistic weekly tasks for week {week} of the internship. "
        f"Tasks should be appropriate for a student majoring in {major}. "
        f"Respond with a JSON array where each task has a title, description, instructions, "
        f"difficulty (easy, medium, or hard), and points (between 50-150 based on difficulty)."
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate tasks for week {week}"}
            ],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        tasks_text = response.choices[0].message.content
        tasks = json.loads(tasks_text)
        
        # Ensure we have a list of tasks
        logger.info(f"Raw tasks response: {tasks_text}")
        
        if isinstance(tasks, dict) and "tasks" in tasks:
            logger.info("Task data is in 'tasks' field")
            tasks = tasks["tasks"]
        elif not isinstance(tasks, list):
            logger.warning(f"Unexpected tasks format: {type(tasks)}. Using empty list.")
            tasks = []
            
        logger.info(f"Processed tasks: {len(tasks)} tasks found")
        
        # Ensure each task has all required fields
        for task in tasks:
            task.setdefault("title", f"Week {week} Task")
            task.setdefault("description", "Complete this task as part of your virtual internship.")
            task.setdefault("instructions", "Follow the instructions carefully and submit your work.")
            task.setdefault("difficulty", "medium")
            task.setdefault("points", 100)
        
        return tasks
    except Exception as e:
        logger.error(f"Error generating tasks: {str(e)}")
        return [
            {
                "title": f"Week {week} Task 1",
                "description": f"Complete this {industry} task as part of your virtual internship.",
                "instructions": "Follow the instructions carefully and submit your work.",
                "difficulty": "medium",
                "points": 100
            },
            {
                "title": f"Week {week} Task 2",
                "description": f"Another {industry} task for your virtual internship.",
                "instructions": "Complete this task following industry best practices.",
                "difficulty": "medium",
                "points": 100
            }
        ]

def evaluate_submission(submission_id):
    """
    Trigger evaluation of a submission
    
    This could call an Azure Function to evaluate asynchronously
    
    Args:
        submission_id (int): The ID of the submission to evaluate
    """
    from models.internship import Submission, Task
    from services.supervisor_service import generate_feedback
    
    # Get the submission from the database
    submission = Submission.query.get(submission_id)
    if not submission:
        logger.error(f"Submission not found: {submission_id}")
        return
    
    # Get the associated task
    task = Task.query.get(submission.task_id)
    if not task:
        logger.error(f"Task not found for submission: {submission_id}")
        return
    
    # Get internship information
    internship = task.internship
    industry = internship.industry.name if internship and internship.industry else "general"
    
    # Call Azure Function if available
    azure_function_endpoint = app.config.get("AZURE_FUNCTION_ENDPOINT")
    azure_function_key = app.config.get("AZURE_FUNCTION_KEY")
    
    if azure_function_endpoint and azure_function_key:
        try:
            function_url = f"{azure_function_endpoint}/api/evaluate_submission"
            headers = {
                "Content-Type": "application/json",
                "x-functions-key": azure_function_key
            }
            data = {
                "submission_id": submission_id,
                "content": submission.content,
                "task_title": task.title,
                "task_description": task.description,
                "task_difficulty": task.difficulty,
                "industry": industry
            }
            
            response = requests.post(function_url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                
                # Update submission with feedback
                submission.score = result.get("score", 70)
                submission.feedback = json.dumps(result)
                submission.evaluated_at = datetime.utcnow()
                
                # Update task status
                task.status = "evaluated"
                
                from app import db
                db.session.commit()
                
                logger.info(f"Submission {submission_id} evaluated by Azure Function")
                return
            else:
                logger.error(f"Azure Function error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Failed to call Azure Function: {e}")
    
    # Fallback to local evaluation if Azure Function is not available
    try:
        feedback = generate_feedback(
            submission_content=submission.content,
            task_title=task.title,
            task_description=task.description,
            task_difficulty=task.difficulty,
            industry=industry
        )
        
        # Update submission with feedback
        from datetime import datetime
        submission.score = feedback.get("score", 70)
        submission.feedback = json.dumps(feedback)
        submission.evaluated_at = datetime.utcnow()
        
        # Update task status
        task.status = "evaluated"
        
        from app import db
        db.session.commit()
        
        logger.info(f"Submission {submission_id} evaluated locally")
    except Exception as e:
        logger.error(f"Failed to evaluate submission: {e}")

def search_resources(query, industry, task_type=None, limit=5):
    """
    Search for relevant resources using Azure AI Search
    
    Args:
        query (str): The search query
        industry (str): The industry context
        task_type (str, optional): The type of task (e.g., "research", "analysis")
        limit (int, optional): Maximum number of results to return
        
    Returns:
        list: List of resource dictionaries with title, description, and url
    """
    if search_client:
        try:
            filter_condition = None
            if task_type:
                filter_condition = f"task_type eq '{task_type}'"
            
            results = search_client.search(
                search_text=query,
                filter=filter_condition,
                query_type="semantic",
                query_language="en-us",
                semantic_configuration_name="default",
                query_caption="extractive",
                query_answer="extractive",
                top=limit
            )
            
            resources = []
            for result in results:
                resources.append({
                    "title": result["title"],
                    "description": result["description"],
                    "url": result["url"],
                    "type": result.get("resource_type", "article")
                })
            
            return resources
        except Exception as e:
            logger.error(f"Azure Search error: {e}")
    
    # Fallback to OpenAI generated resources if Azure Search is not available
    from services.supervisor_service import suggest_resources
    return suggest_resources(query, query, industry)

def generate_certificate(user_name, internship_title, industry, tasks_completed, avg_score):
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
    from services.supervisor_service import generate_certificate_for_internship
    
    certificate = generate_certificate_for_internship(
        user_name=user_name,
        internship_title=internship_title,
        industry=industry,
        tasks_completed=tasks_completed,
        avg_score=avg_score
    )
    
    # In a real implementation, this could generate a PDF certificate and upload it to Azure Storage
    # For now, we'll just return the certificate details
    
    return certificate