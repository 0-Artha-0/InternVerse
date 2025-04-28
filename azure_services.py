import os
import requests
import json
import logging
from app import app
from azure.cosmos import CosmosClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import openai
from openai import AsyncAzureOpenAI
import asyncio

# Initialize clients as None
cosmos_client = None
db = None
container = None
search_client = None

# Configure Azure OpenAI client if credentials are available
if app.config.get("AZURE_OPENAI_ENDPOINT") and app.config.get("AZURE_OPENAI_KEY"):
    openai.api_type = "azure"
    openai.api_base = app.config["AZURE_OPENAI_ENDPOINT"]
    openai.api_key = app.config["AZURE_OPENAI_KEY"]
    openai.api_version = "2023-05-15"
    logging.info("Azure OpenAI client configured")
else:
    logging.warning("Azure OpenAI credentials not found. Some features will be limited.")

# Configure Cosmos DB client if credentials are available
if app.config.get("COSMOS_ENDPOINT") and app.config.get("COSMOS_KEY"):
    try:
        cosmos_client = CosmosClient(
            app.config["COSMOS_ENDPOINT"],
            app.config["COSMOS_KEY"]
        )
        db = cosmos_client.get_database_client(app.config["COSMOS_DATABASE"])
        container = db.get_container_client("internships")
        logging.info("Cosmos DB client configured")
    except Exception as e:
        logging.error(f"Failed to initialize Cosmos DB client: {str(e)}")
else:
    logging.warning("Cosmos DB credentials not found. Using fallback storage.")

# Configure Azure AI Search if credentials are available
if app.config.get("AZURE_SEARCH_ENDPOINT") and app.config.get("AZURE_SEARCH_KEY"):
    try:
        search_client = SearchClient(
            endpoint=app.config["AZURE_SEARCH_ENDPOINT"],
            index_name=app.config["AZURE_SEARCH_INDEX"],
            credential=AzureKeyCredential(app.config["AZURE_SEARCH_KEY"])
        )
        logging.info("Azure Search client configured")
    except Exception as e:
        logging.error(f"Failed to initialize Azure Search client: {str(e)}")
else:
    logging.warning("Azure Search credentials not found. Search functionality will be limited.")

def generate_internship(industry, major, interests):
    """
    Generate internship details using Azure OpenAI
    
    Args:
        industry (str): The industry for the internship
        major (str): Student's major
        interests (str): Student's career interests
        
    Returns:
        dict: Internship details including title, description, and duration
    """
    try:
        # Check if Azure OpenAI is configured
        if not app.config.get("AZURE_OPENAI_ENDPOINT") or not app.config.get("AZURE_OPENAI_KEY") or not app.config.get("AZURE_OPENAI_DEPLOYMENT"):
            logging.warning("Azure OpenAI not configured. Using default internship details.")
            return {
                "title": f"{industry} Virtual Internship",
                "description": f"A virtual internship experience in {industry} tailored for {major} students with interests in {interests}. You will work on realistic projects to build practical skills in this field.",
                "duration_weeks": 6
            }
            
        prompt = f"""
        Create a realistic virtual internship for a student with the following details:
        - Industry: {industry}
        - Student major: {major}
        - Student interests: {interests}
        
        Generate a JSON response with the following fields:
        - title: The title of the internship (e.g., "Marketing Analytics Intern at TechCorp")
        - description: A detailed description of the internship and what the student will learn
        - duration_weeks: The duration of the internship in weeks (between 4 and 12)
        """
        
        try:
            completion = openai.ChatCompletion.create(
                deployment_id=app.config["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": "You are an AI assistant that generates realistic virtual internship scenarios."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            internship_data = json.loads(response_text)
        except Exception as e:
            logging.error(f"Error in OpenAI API call: {str(e)}")
            return {
                "title": f"{industry} Virtual Internship",
                "description": f"A virtual internship experience in {industry} tailored for {major} students with interests in {interests}. You will work on realistic projects to build practical skills in this field.",
                "duration_weeks": 6
            }
        
        # Save to Cosmos DB if available
        if container:
            try:
                container.upsert_item({
                    "id": f"{industry}-{major}-{internship_data['title']}",
                    "type": "internship",
                    "industry": industry,
                    "major": major,
                    "interests": interests,
                    "title": internship_data["title"],
                    "description": internship_data["description"],
                    "duration_weeks": internship_data["duration_weeks"]
                })
            except Exception as e:
                logging.error(f"Error saving internship to Cosmos DB: {str(e)}")
        
        return internship_data
        
    except Exception as e:
        logging.error(f"Error generating internship: {str(e)}")
        # Return default internship details
        return {
            "title": f"{industry} Virtual Internship",
            "description": f"A virtual internship experience in {industry} tailored for {major} students. You will work on real-world projects to build practical skills.",
            "duration_weeks": 6
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
    try:
        # Check if Azure OpenAI is configured
        if not app.config.get("AZURE_OPENAI_ENDPOINT") or not app.config.get("AZURE_OPENAI_KEY") or not app.config.get("AZURE_OPENAI_DEPLOYMENT"):
            logging.warning("Azure OpenAI not configured. Using default task details.")
            # Return default tasks
            default_tasks = [
                {
                    "title": f"Week {week} Research Task",
                    "description": f"Research current trends in the {industry} industry.",
                    "instructions": f"Conduct research on recent developments in {industry}. Write a 500-word report summarizing your findings.",
                    "difficulty": "medium",
                    "points": 100
                },
                {
                    "title": f"Week {week} Analysis Task",
                    "description": f"Analyze a case study related to {industry}.",
                    "instructions": f"Review the provided case study and write an analysis focusing on key issues and potential solutions.",
                    "difficulty": "medium",
                    "points": 120
                }
            ]
            
            if week == 1:
                default_tasks.append({
                    "title": "Introduction Task",
                    "description": f"Introduction to the {industry} industry.",
                    "instructions": "Create a mind map of the key companies, technologies, and trends in this industry.",
                    "difficulty": "easy",
                    "points": 80
                })
                
            return default_tasks
            
        prompt = f"""
        Generate {3 if week == 1 else 2} realistic professional tasks for week {week} of a virtual internship:
        - Internship: {internship_title}
        - Industry: {industry}
        - Student major: {major}
        
        For each task, provide a JSON object with the following fields:
        - title: A short, professional title for the task
        - description: What the task is about and why it's important
        - instructions: Detailed instructions on how to complete the task
        - difficulty: One of "easy", "medium", or "hard"
        - points: Points value for the task (between 50 and 200)
        
        Return a JSON array of these task objects.
        """
        
        try:
            # Create a more detailed system message based on industry
            system_message = f"""You are an experienced professional supervisor in the {industry} industry.
You create realistic, challenging internship tasks that would be assigned in a real workplace.
Focus on developing practical skills relevant to {industry} for students majoring in {major}.
Ensure tasks are appropriate for week {week} of the internship (earlier weeks should be simpler).
Create tasks that would help build a professional portfolio and provide transferable skills.
Maintain a formal but friendly tone, encourage problem-solving, and give constructive advice.
Adapt your tasks and examples to fit the field of {industry} and the environment of a professional organization.
Format your response as a proper JSON array that can be parsed without errors."""

            completion = openai.ChatCompletion.create(
                deployment_id=app.config["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            tasks_data = json.loads(response_text)
        except Exception as e:
            logging.error(f"Error in OpenAI API call for tasks: {str(e)}")
            # Return default tasks
            default_tasks = [
                {
                    "title": f"Week {week} Research Task",
                    "description": f"Research current trends in the {industry} industry.",
                    "instructions": f"Conduct research on recent developments in {industry}. Write a 500-word report summarizing your findings.",
                    "difficulty": "medium",
                    "points": 100
                },
                {
                    "title": f"Week {week} Analysis Task",
                    "description": f"Analyze a case study related to {industry}.",
                    "instructions": f"Review the provided case study and write an analysis focusing on key issues and potential solutions.",
                    "difficulty": "medium",
                    "points": 120
                }
            ]
            
            if week == 1:
                default_tasks.append({
                    "title": "Introduction Task",
                    "description": f"Introduction to the {industry} industry.",
                    "instructions": "Create a mind map of the key companies, technologies, and trends in this industry.",
                    "difficulty": "easy",
                    "points": 80
                })
                
            return default_tasks
        
        # Save tasks to Cosmos DB if available
        if container:
            try:
                for task in tasks_data:
                    container.upsert_item({
                        "id": f"{internship_title}-{task['title']}",
                        "type": "task",
                        "internship_title": internship_title,
                        "industry": industry,
                        "week": week,
                        "title": task["title"],
                        "description": task["description"],
                        "instructions": task["instructions"],
                        "difficulty": task["difficulty"],
                        "points": task["points"]
                    })
            except Exception as e:
                logging.error(f"Error saving tasks to Cosmos DB: {str(e)}")
        
        return tasks_data
        
    except Exception as e:
        logging.error(f"Error generating tasks: {str(e)}")
        # Return default tasks
        default_tasks = [
            {
                "title": f"Week {week} Research Task",
                "description": f"Research current trends in the {industry} industry.",
                "instructions": f"Conduct research on recent developments in {industry}. Write a 500-word report summarizing your findings.",
                "difficulty": "medium",
                "points": 100
            },
            {
                "title": f"Week {week} Analysis Task",
                "description": f"Analyze a case study related to {industry}.",
                "instructions": f"Review the provided case study and write an analysis focusing on key issues and potential solutions.",
                "difficulty": "medium",
                "points": 120
            }
        ]
        
        if week == 1:
            default_tasks.append({
                "title": "Introduction Task",
                "description": f"Introduction to the {industry} industry.",
                "instructions": "Create a mind map of the key companies, technologies, and trends in this industry.",
                "difficulty": "easy",
                "points": 80
            })
            
        return default_tasks

def evaluate_submission(submission_id):
    """
    Trigger Azure Function to evaluate a submission
    
    Args:
        submission_id (int): The ID of the submission to evaluate
    """
    try:
        # Check if Azure Function endpoint is configured
        function_url = app.config.get("AZURE_FUNCTION_ENDPOINT")
        function_key = app.config.get("AZURE_FUNCTION_KEY")
        
        if not function_url or not function_key:
            logging.warning("Azure Function not configured. Using local evaluation as fallback.")
            # In a real implementation, you might want to add a local evaluation logic here
            # or queue the submission for later evaluation when the function is available
            return
        
        headers = {
            "Content-Type": "application/json",
            "x-functions-key": function_key
        }
        
        data = {
            "submission_id": submission_id
        }
        
        # Make asynchronous call to Azure Function
        response = requests.post(function_url, headers=headers, json=data)
        
        if response.status_code != 202:
            logging.error(f"Error calling task evaluation function: {response.text}")
            # You might want to implement a fallback evaluation here
    
    except Exception as e:
        logging.error(f"Error triggering submission evaluation: {str(e)}")
        # You might want to implement a fallback evaluation here

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
    try:
        # Enhance search query with industry and task type
        search_query = f"{query} {industry}"
        if task_type:
            search_query += f" {task_type}"
        
        # Execute search if search client is available
        resources = []
        if search_client:
            try:
                results = search_client.search(
                    search_text=search_query,
                    select=["title", "description", "url", "resourceType", "industry"],
                    top=limit
                )
                
                # Format results
                for result in results:
                    resources.append({
                        "title": result["title"],
                        "description": result["description"],
                        "url": result["url"],
                        "type": result.get("resourceType", "article"),
                        "industry": result.get("industry", industry)
                    })
            except Exception as e:
                logging.error(f"Error executing search: {str(e)}")
        else:
            # Provide default resources when search client is not available
            resources = [
                {
                    "title": f"{industry} Learning Resources",
                    "description": f"A curated list of learning resources for {industry} related to {query}.",
                    "url": f"https://www.example.com/{industry.lower()}/resources",
                    "type": "article",
                    "industry": industry
                },
                {
                    "title": f"{query} Guide",
                    "description": f"Comprehensive guide about {query} in the context of {industry}.",
                    "url": f"https://www.example.com/guides/{query.lower().replace(' ', '-')}",
                    "type": "tutorial",
                    "industry": industry
                }
            ]
        
        return resources
        
    except Exception as e:
        logging.error(f"Error searching resources: {str(e)}")
        return []

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
    try:
        # Check if Azure OpenAI is configured
        if not app.config.get("AZURE_OPENAI_ENDPOINT") or not app.config.get("AZURE_OPENAI_KEY") or not app.config.get("AZURE_OPENAI_DEPLOYMENT"):
            logging.warning("Azure OpenAI not configured. Using default certificate details.")
            return {
                "title": f"Certificate of Completion: {internship_title}",
                "description": f"This is to certify that {user_name} has successfully completed the {internship_title} virtual internship program in {industry} with an average score of {avg_score:.2f}/100 across {tasks_completed} tasks.",
                "skills_acquired": f"Industry knowledge, Professional communication, Problem-solving, Critical thinking, {industry} analysis"
            }
            
        prompt = f"""
        Generate a professional certificate for:
        - Student: {user_name}
        - Internship: {internship_title}
        - Industry: {industry}
        - Tasks completed: {tasks_completed}
        - Average score: {avg_score:.2f}/100
        
        Generate a JSON response with the following fields:
        - title: The title of the certificate (e.g., "Certificate of Completion: Marketing Analytics Virtual Internship")
        - description: A formal description of the internship achievement
        - skills_acquired: A comma-separated list of 5-7 specific skills developed during this internship
        """
        
        try:
            # Create detailed system message for certificate generation
            system_message = f"""You are a professional certification authority for the {industry} industry.
You create formal, professional certificates that recognize the completion of virtual internship programs.
Focus on highlighting the professional development and industry-specific skills acquired during the internship.
Use appropriate professional language that would be suitable for a certificate to be shared on LinkedIn.
Maintain a formal but friendly tone, encourage problem-solving, and give constructive advice.
Adapt your certificate to fit the field of {industry} and the environment of a professional organization.
Format your response as a proper JSON object that can be parsed without errors."""

            completion = openai.ChatCompletion.create(
                deployment_id=app.config["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            certificate_data = json.loads(response_text)
        except Exception as e:
            logging.error(f"Error in OpenAI API call for certificate: {str(e)}")
            return {
                "title": f"Certificate of Completion: {internship_title}",
                "description": f"This is to certify that {user_name} has successfully completed the {internship_title} virtual internship program in {industry} with an average score of {avg_score:.2f}/100 across {tasks_completed} tasks.",
                "skills_acquired": f"Industry knowledge, Professional communication, Problem-solving, Critical thinking, {industry} analysis"
            }
        
        # Save to Cosmos DB if available
        if container:
            try:
                container.upsert_item({
                    "id": f"{user_name}-{internship_title}-certificate",
                    "type": "certificate",
                    "user_name": user_name,
                    "internship_title": internship_title,
                    "industry": industry,
                    "tasks_completed": tasks_completed,
                    "avg_score": avg_score,
                    "title": certificate_data["title"],
                    "description": certificate_data["description"],
                    "skills_acquired": certificate_data["skills_acquired"]
                })
            except Exception as e:
                logging.error(f"Error saving certificate to Cosmos DB: {str(e)}")
        
        return certificate_data
        
    except Exception as e:
        logging.error(f"Error generating certificate: {str(e)}")
        # Return default certificate details
        return {
            "title": f"Certificate of Completion: {internship_title}",
            "description": f"This is to certify that {user_name} has successfully completed the {internship_title} virtual internship program in {industry}.",
            "skills_acquired": f"Industry knowledge, Professional communication, Problem-solving, Critical thinking, {industry} analysis"
        }
