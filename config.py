"""
Configuration settings for the Virtual Internship Simulator application.
"""
import os
import logging

# Flask configuration
SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
DEBUG = True

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///internship.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = "https://thepromptocrats-hackathon-stg-openai-uaen-01.openai.azure.com/"
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"
AZURE_OPENAI_API_VERSION = "2023-12-01-preview"  # Use a version compatible with the current Azure OpenAI SDK

# Standard OpenAI configuration (fallback)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "internship-simulator")

# Azure AI Search configuration
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "internship-resources")

# Azure Function configuration
AZURE_FUNCTION_ENDPOINT = os.environ.get("AZURE_FUNCTION_ENDPOINT")
AZURE_FUNCTION_KEY = os.environ.get("AZURE_FUNCTION_KEY")

# Application configuration
DEFAULT_INDUSTRIES = [
    {
        "name": "Technology & IT",
        "description": "Experience the fast-paced world of technology, developing software, managing IT infrastructure, or designing digital solutions.",
        "icon": "bi-cpu"
    },
    {
        "name": "Business & Finance",
        "description": "Dive into the world of business strategy, financial analysis, marketing, and corporate operations.",
        "icon": "bi-cash-coin"
    },
    {
        "name": "Healthcare",
        "description": "Explore careers in health services, medical research, healthcare administration, or public health.",
        "icon": "bi-hospital"
    },
    {
        "name": "Education",
        "description": "Discover roles in teaching, curriculum development, educational technology, or academic administration.",
        "icon": "bi-book"
    },
    {
        "name": "Environmental Science & Sustainability",
        "description": "Work on projects related to environmental conservation, renewable energy, sustainability consulting, or climate research.",
        "icon": "bi-tree"
    },
    {
        "name": "Media & Communications",
        "description": "Develop skills in journalism, digital media production, public relations, or content creation.",
        "icon": "bi-camera"
    },
    {
        "name": "Law & Government",
        "description": "Experience legal research, policy analysis, public administration, or compliance work.",
        "icon": "bi-bank"
    },
    {
        "name": "Arts & Design",
        "description": "Explore creative roles in graphic design, user experience, product design, or multimedia production.",
        "icon": "bi-palette"
    },
    {
        "name": "Engineering",
        "description": "Work on projects in mechanical, civil, electrical, or other engineering disciplines.",
        "icon": "bi-gear"
    },
    {
        "name": "Hospitality & Tourism",
        "description": "Experience roles in hotel management, tourism development, event planning, or customer service.",
        "icon": "bi-airplane"
    }
]

DEFAULT_COMPANIES = [
    {
        "name": "TechNova Solutions",
        "industry": "Technology & IT",
        "description": "A leading technology firm specializing in cloud solutions, AI development, and enterprise software."
    },
    {
        "name": "Global Finance Partners",
        "industry": "Business & Finance",
        "description": "A multinational financial services company offering investment banking, asset management, and financial advisory."
    },
    {
        "name": "MediCare Innovations",
        "industry": "Healthcare",
        "description": "A healthcare technology company developing digital health solutions and medical devices."
    },
    {
        "name": "EduTech Pioneers",
        "industry": "Education",
        "description": "An educational technology company creating learning platforms and digital curriculum."
    },
    {
        "name": "GreenEarth Sustainability",
        "industry": "Environmental Science & Sustainability",
        "description": "A consulting firm focused on sustainability strategies, environmental impact assessments, and renewable energy."
    },
    {
        "name": "MediaSphere Global",
        "industry": "Media & Communications",
        "description": "A digital media company producing content across multiple platforms and offering marketing services."
    },
    {
        "name": "LegalEdge Associates",
        "industry": "Law & Government",
        "description": "A law firm specializing in corporate law, intellectual property, and regulatory compliance."
    },
    {
        "name": "Creative Design Studio",
        "industry": "Arts & Design",
        "description": "A design agency working on brand identity, user experience, and product design for various clients."
    },
    {
        "name": "Innovate Engineering",
        "industry": "Engineering",
        "description": "An engineering firm that designs and implements infrastructure, products, and systems across various industries."
    },
    {
        "name": "Horizon Hospitality Group",
        "industry": "Hospitality & Tourism",
        "description": "A hospitality management company operating hotels, resorts, and tourism experiences worldwide."
    }
]

# Logging configuration
LOG_LEVEL = logging.INFO