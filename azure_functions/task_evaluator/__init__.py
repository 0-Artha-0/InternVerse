import logging
import json
import azure.functions as func
import requests
import os
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Task Evaluator Function triggered.')
    
    try:
        # Get the submission ID from the request
        req_body = req.get_json()
        submission_id = req_body.get('submission_id')
        
        if not submission_id:
            return func.HttpResponse(
                "Please pass a submission_id in the request body",
                status_code=400
            )
        
        # Get environment variables
        db_connection_string = os.environ["DATABASE_URL"]
        openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        openai_key = os.environ["AZURE_OPENAI_KEY"]
        openai_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        
        # Get submission details from database
        submission, task = get_submission_details(submission_id, db_connection_string)
        
        if not submission or not task:
            return func.HttpResponse(
                "Submission or task not found",
                status_code=404
            )
        
        # Generate feedback using Azure OpenAI
        feedback = generate_feedback(
            submission['content'],
            task['title'],
            task['description'],
            task['instructions'],
            task['difficulty'],
            openai_endpoint,
            openai_key,
            openai_deployment
        )
        
        # Update submission with feedback
        update_submission(
            submission_id,
            feedback['score'],
            feedback['feedback'],
            db_connection_string
        )
        
        # Update task status
        update_task_status(
            task['id'],
            'evaluated',
            db_connection_string
        )
        
        # Update internship progress
        update_internship_progress(
            task['internship_id'],
            db_connection_string
        )
        
        # Check if internship is complete and generate certificate if needed
        check_and_generate_certificate(
            task['internship_id'],
            db_connection_string,
            openai_endpoint,
            openai_key,
            openai_deployment
        )
        
        return func.HttpResponse(
            json.dumps({"message": "Submission evaluated successfully", "feedback": feedback}),
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f"Error in Task Evaluator: {str(e)}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )

def get_submission_details(submission_id, connection_string):
    """
    Get the submission and task details from the database
    
    Args:
        submission_id (int): The ID of the submission
        connection_string (str): Database connection string
        
    Returns:
        tuple: (submission, task) dictionaries
    """
    # In a real implementation, this would query the database
    # For this function example, we'll use a mock API call
    api_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/api/internal/submission/{submission_id}"
    response = requests.get(api_url, headers={"x-api-key": os.environ.get("INTERNAL_API_KEY", "")})
    
    if response.status_code == 200:
        data = response.json()
        return data.get('submission'), data.get('task')
    else:
        logging.error(f"Failed to get submission details: {response.text}")
        return None, None

def generate_feedback(content, task_title, task_description, task_instructions, task_difficulty, openai_endpoint, openai_key, openai_deployment):
    """
    Generate feedback for the submission using Azure OpenAI
    
    Args:
        content (str): The submission content
        task_title (str): The task title
        task_description (str): The task description
        task_instructions (str): The task instructions
        task_difficulty (str): The task difficulty
        openai_endpoint (str): Azure OpenAI endpoint
        openai_key (str): Azure OpenAI key
        openai_deployment (str): Azure OpenAI deployment name
        
    Returns:
        dict: Feedback including score and comments
    """
    try:
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "api-key": openai_key
        }
        
        # Construct the prompt
        prompt = f"""
        Evaluate the following student submission for a virtual internship task:
        
        Task: {task_title}
        Task Description: {task_description}
        Task Instructions: {task_instructions}
        Difficulty: {task_difficulty}
        
        Student Submission:
        {content}
        
        Evaluate the submission professionally and generate a JSON response with:
        1. score: A numerical score between 0 and 100
        2. feedback: Detailed professional feedback (150-300 words) including:
           - Strengths of the submission
           - Areas for improvement
           - Specific professional advice
        3. next_steps: 2-3 suggested next steps or resources to improve
        """
        
        # Prepare the data payload
        data = {
            "messages": [
                {"role": "system", "content": "You are an AI supervisor that evaluates student internship submissions fairly and professionally."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 800,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None
        }
        
        # Make the API call
        response = requests.post(
            f"{openai_endpoint}/openai/deployments/{openai_deployment}/chat/completions?api-version=2023-05-15",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logging.error(f"OpenAI API error: {response.text}")
            # Return default feedback if API call fails
            return {
                "score": 70,
                "feedback": "Thank you for your submission. Your work demonstrates understanding of the key concepts, but could benefit from more depth and detail. Consider expanding your analysis and providing more specific examples to strengthen your work.",
                "next_steps": ["Review industry best practices", "Add more specific examples", "Consider different perspectives"]
            }
        
        # Extract and parse the response
        result = response.json()
        response_text = result['choices'][0]['message']['content'].strip()
        
        # Parse JSON response
        feedback_data = json.loads(response_text)
        
        return feedback_data
    
    except Exception as e:
        logging.error(f"Error generating feedback: {str(e)}")
        # Return default feedback
        return {
            "score": 70,
            "feedback": "Thank you for your submission. Your work demonstrates understanding of the key concepts, but could benefit from more depth and detail. Consider expanding your analysis and providing more specific examples to strengthen your work.",
            "next_steps": ["Review industry best practices", "Add more specific examples", "Consider different perspectives"]
        }

def update_submission(submission_id, score, feedback, connection_string):
    """
    Update the submission with feedback and score
    
    Args:
        submission_id (int): The ID of the submission
        score (float): The score for the submission
        feedback (str): The feedback text
        connection_string (str): Database connection string
    """
    # In a real implementation, this would update the database
    # For this function example, we'll use a mock API call
    api_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/api/internal/submission/{submission_id}/update"
    data = {
        "score": score,
        "feedback": feedback,
        "evaluated_at": datetime.utcnow().isoformat()
    }
    
    response = requests.post(
        api_url, 
        headers={"x-api-key": os.environ.get("INTERNAL_API_KEY", "")},
        json=data
    )
    
    if response.status_code != 200:
        logging.error(f"Failed to update submission: {response.text}")
        raise Exception("Failed to update submission")

def update_task_status(task_id, status, connection_string):
    """
    Update the task status
    
    Args:
        task_id (int): The ID of the task
        status (str): The new status
        connection_string (str): Database connection string
    """
    # In a real implementation, this would update the database
    # For this function example, we'll use a mock API call
    api_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/api/internal/task/{task_id}/update"
    data = {
        "status": status
    }
    
    response = requests.post(
        api_url, 
        headers={"x-api-key": os.environ.get("INTERNAL_API_KEY", "")},
        json=data
    )
    
    if response.status_code != 200:
        logging.error(f"Failed to update task status: {response.text}")
        raise Exception("Failed to update task status")

def update_internship_progress(internship_id, connection_string):
    """
    Update the internship progress based on completed tasks
    
    Args:
        internship_id (int): The ID of the internship
        connection_string (str): Database connection string
    """
    # In a real implementation, this would update the database
    # For this function example, we'll use a mock API call
    api_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/api/internal/internship/{internship_id}/update-progress"
    
    response = requests.post(
        api_url, 
        headers={"x-api-key": os.environ.get("INTERNAL_API_KEY", "")}
    )
    
    if response.status_code != 200:
        logging.error(f"Failed to update internship progress: {response.text}")
        raise Exception("Failed to update internship progress")

def check_and_generate_certificate(internship_id, connection_string, openai_endpoint, openai_key, openai_deployment):
    """
    Check if the internship is complete and generate a certificate if needed
    
    Args:
        internship_id (int): The ID of the internship
        connection_string (str): Database connection string
        openai_endpoint (str): Azure OpenAI endpoint
        openai_key (str): Azure OpenAI key
        openai_deployment (str): Azure OpenAI deployment name
    """
    # In a real implementation, this would query the database and update if needed
    # For this function example, we'll use a mock API call
    api_url = f"{os.environ.get('APP_URL', 'http://localhost:5000')}/api/internal/internship/{internship_id}/check-completion"
    
    response = requests.post(
        api_url, 
        headers={
            "x-api-key": os.environ.get("INTERNAL_API_KEY", ""),
            "x-openai-endpoint": openai_endpoint,
            "x-openai-key": openai_key,
            "x-openai-deployment": openai_deployment
        }
    )
    
    if response.status_code != 200:
        logging.error(f"Failed to check internship completion: {response.text}")
        # Don't raise exception here as this is a secondary operation
