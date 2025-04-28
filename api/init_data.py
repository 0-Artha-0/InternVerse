import logging
from app import db
from models.user import User, UserProfile, AdminUser
from models.internship import Industry, Company

logger = logging.getLogger(__name__)

def initialize_data(force=False):
    """
    Initialize sample data for the application
    
    Args:
        force (bool): Force re-initialization even if data exists
    """
    # Check if we already have data
    industry_count = Industry.query.count()
    if industry_count > 0 and not force:
        logger.info("Data already initialized, skipping")
        return
    
    logger.info("Initializing sample data")
    
    # Create admin user if not exists
    admin = User.query.filter_by(email="admin@internverse.com").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@internverse.com",
            is_admin=True
        )
        admin.set_password("admin123")
        
        admin_profile = UserProfile(
            user=admin,
            full_name="Admin User",
            profile_completed=True
        )
        
        admin_role = AdminUser(
            user=admin,
            organization="InternVerse",
            role="Administrator",
            access_level="super"
        )
        
        db.session.add(admin)
        db.session.add(admin_profile)
        db.session.add(admin_role)
        logger.info("Created admin user")
    
    # Create industries
    industries = [
        {
            "name": "Technology",
            "description": "Experience virtual internships in software development, cybersecurity, data science, and IT management.",
            "icon": "fa-laptop-code"
        },
        {
            "name": "Business",
            "description": "Gain experience in marketing, finance, management, and entrepreneurship through virtual business internships.",
            "icon": "fa-chart-line"
        },
        {
            "name": "Healthcare",
            "description": "Explore healthcare administration, biotech research, medical informatics, and public health.",
            "icon": "fa-heartbeat"
        },
        {
            "name": "Engineering",
            "description": "Work on projects in mechanical, electrical, civil, and aerospace engineering disciplines.",
            "icon": "fa-cogs"
        },
        {
            "name": "Creative Arts",
            "description": "Develop portfolios in graphic design, content creation, digital media, and creative writing.",
            "icon": "fa-paint-brush"
        },
        {
            "name": "Education",
            "description": "Experience teaching methodologies, curriculum development, educational technology, and student assessment.",
            "icon": "fa-graduation-cap"
        },
        {
            "name": "Environmental Science",
            "description": "Work on sustainability projects, climate research, conservation efforts, and environmental policy.",
            "icon": "fa-leaf"
        },
        {
            "name": "Media & Communications",
            "description": "Gain experience in journalism, public relations, social media management, and digital content creation.",
            "icon": "fa-comments"
        },
        {
            "name": "Hospitality & Tourism",
            "description": "Learn about hotel management, event planning, tourism development, and customer experience design.",
            "icon": "fa-concierge-bell"
        },
        {
            "name": "Finance & Banking",
            "description": "Experience financial analysis, investment management, banking operations, and fintech innovation.",
            "icon": "fa-money-bill-wave"
        }
    ]
    
    industry_objects = {}
    
    for industry_data in industries:
        industry = Industry.query.filter_by(name=industry_data["name"]).first()
        if not industry:
            industry = Industry(**industry_data)
            db.session.add(industry)
            logger.info(f"Created industry: {industry_data['name']}")
        industry_objects[industry_data["name"]] = industry
    
    # Create companies
    companies = [
        # Technology
        {
            "name": "TechNova",
            "industry": "Technology",
            "description": "A leading innovative technology company specializing in AI and machine learning solutions.",
            "logo": "technova-logo.png",
            "website": "https://technova.example.com",
            "location": "Silicon Valley"
        },
        {
            "name": "CodeX Systems",
            "industry": "Technology",
            "description": "An enterprise software development company creating scalable solutions for various industries.",
            "logo": "codex-logo.png",
            "website": "https://codex.example.com",
            "location": "Seattle"
        },
        
        # Business
        {
            "name": "FinEdge",
            "industry": "Business",
            "description": "A fintech startup revolutionizing personal finance and investment management.",
            "logo": "finedge-logo.png",
            "website": "https://finedge.example.com",
            "location": "New York City"
        },
        {
            "name": "GlobalStrategy Partners",
            "industry": "Business",
            "description": "A consulting firm offering strategic business advice and market analysis to Fortune 500 clients.",
            "logo": "globalstrategy-logo.png",
            "website": "https://globalstrategy.example.com",
            "location": "Chicago"
        },
        
        # Healthcare
        {
            "name": "MediCura",
            "industry": "Healthcare",
            "description": "A healthcare provider focused on telemedicine and digital health solutions.",
            "logo": "medicura-logo.png",
            "website": "https://medicura.example.com",
            "location": "Boston"
        },
        {
            "name": "BioGenetics",
            "industry": "Healthcare",
            "description": "A biotech research company working on genomic solutions for personalized medicine.",
            "logo": "biogenetics-logo.png",
            "website": "https://biogenetics.example.com",
            "location": "San Diego"
        },
        
        # Engineering
        {
            "name": "EngiPro",
            "industry": "Engineering",
            "description": "An engineering firm specializing in sustainable infrastructure and green energy solutions.",
            "logo": "engipro-logo.png",
            "website": "https://engipro.example.com",
            "location": "Chicago"
        },
        {
            "name": "RoboTech Innovations",
            "industry": "Engineering",
            "description": "A robotics engineering company developing autonomous systems for industrial applications.",
            "logo": "robotech-logo.png",
            "website": "https://robotech.example.com",
            "location": "Detroit"
        },
        
        # Creative Arts
        {
            "name": "DesignFusion",
            "industry": "Creative Arts",
            "description": "A creative agency delivering innovative design solutions for digital and print media.",
            "logo": "designfusion-logo.png",
            "website": "https://designfusion.example.com",
            "location": "Los Angeles"
        },
        {
            "name": "ArtSpace Studios",
            "industry": "Creative Arts",
            "description": "A digital art studio producing animations, illustrations, and visual content for entertainment.",
            "logo": "artspace-logo.png",
            "website": "https://artspace.example.com",
            "location": "San Francisco"
        },
        
        # Education
        {
            "name": "EduTech Solutions",
            "industry": "Education",
            "description": "An educational technology company developing digital learning platforms for schools and universities.",
            "logo": "edutech-logo.png",
            "website": "https://edutech.example.com",
            "location": "Boston"
        },
        {
            "name": "Global Learning Institute",
            "industry": "Education",
            "description": "An international education organization developing curriculum and assessment tools for global learners.",
            "logo": "globallearning-logo.png",
            "website": "https://globallearning.example.com",
            "location": "Washington DC"
        },
        
        # Environmental Science
        {
            "name": "EcoSolutions",
            "industry": "Environmental Science",
            "description": "A consulting firm specializing in environmental impact assessments and sustainability planning.",
            "logo": "ecosolutions-logo.png",
            "website": "https://ecosolutions.example.com",
            "location": "Portland"
        },
        {
            "name": "ClimateWatch Research",
            "industry": "Environmental Science",
            "description": "A research organization monitoring climate change and developing mitigation strategies.",
            "logo": "climatewatch-logo.png",
            "website": "https://climatewatch.example.com",
            "location": "Boulder"
        },
        
        # Media & Communications
        {
            "name": "MediaPulse",
            "industry": "Media & Communications",
            "description": "A digital media company producing news content across multiple platforms.",
            "logo": "mediapulse-logo.png",
            "website": "https://mediapulse.example.com",
            "location": "New York"
        },
        {
            "name": "Viral Communications",
            "industry": "Media & Communications",
            "description": "A PR and social media agency managing campaigns for major brands and personalities.",
            "logo": "viralcomm-logo.png",
            "website": "https://viralcomm.example.com",
            "location": "Los Angeles"
        },
        
        # Hospitality & Tourism
        {
            "name": "Global Adventures",
            "industry": "Hospitality & Tourism",
            "description": "A travel company organizing sustainable tourism experiences worldwide.",
            "logo": "globaladventures-logo.png",
            "website": "https://globaladventures.example.com",
            "location": "Miami"
        },
        {
            "name": "LuxStay Hotels",
            "industry": "Hospitality & Tourism",
            "description": "A premium hotel chain focusing on experiential hospitality and local cultural immersion.",
            "logo": "luxstay-logo.png",
            "website": "https://luxstay.example.com",
            "location": "Las Vegas"
        },
        
        # Finance & Banking
        {
            "name": "Quantum Finance",
            "industry": "Finance & Banking",
            "description": "A global investment bank offering services in asset management and financial advisory.",
            "logo": "quantumfinance-logo.png",
            "website": "https://quantumfinance.example.com",
            "location": "New York"
        },
        {
            "name": "DigiBank",
            "industry": "Finance & Banking",
            "description": "A digital banking platform offering innovative financial services and products.",
            "logo": "digibank-logo.png",
            "website": "https://digibank.example.com",
            "location": "San Francisco"
        }
    ]
    
    for company_data in companies:
        industry_name = company_data.pop("industry")
        industry = industry_objects.get(industry_name)
        
        if not industry:
            logger.error(f"Industry not found: {industry_name}")
            continue
        
        company = Company.query.filter_by(name=company_data["name"]).first()
        if not company:
            company = Company(
                industry_id=industry.id,
                **company_data
            )
            db.session.add(company)
            logger.info(f"Created company: {company_data['name']}")
    
    # Create roles for different industries and companies
    from models.internship import Role
    
    # Get all companies
    all_companies = Company.query.all()
    company_dict = {company.name: company for company in all_companies}
    
    # Create roles
    roles = [
        # Technology Roles
        {
            "name": "Software Developer Intern",
            "industry": "Technology",
            "company": "TechNova",
            "description": "Work on developing and testing software applications under the guidance of experienced developers.",
            "requirements": "Knowledge of programming languages such as Python, JavaScript, or Java. Familiar with software development lifecycle.",
            "skills_required": "Programming, Problem Solving, Version Control",
            "experience_level": "Entry"
        },
        {
            "name": "Data Science Intern",
            "industry": "Technology",
            "company": "TechNova",
            "description": "Analyze large datasets and build predictive models to derive business insights.",
            "requirements": "Knowledge of statistics, machine learning, and programming languages like Python or R.",
            "skills_required": "Python, Data Analysis, Statistics",
            "experience_level": "Entry"
        },
        {
            "name": "UX/UI Design Intern",
            "industry": "Technology",
            "company": "CodeX Systems",
            "description": "Design user interfaces for web and mobile applications with a focus on usability and aesthetics.",
            "requirements": "Knowledge of design principles, wireframing, and prototyping tools.",
            "skills_required": "UI Design, Wireframing, User Research",
            "experience_level": "Entry"
        },
        {
            "name": "Cybersecurity Intern",
            "industry": "Technology",
            "company": "CodeX Systems",
            "description": "Assist in identifying and mitigating security threats to company systems and networks.",
            "requirements": "Basic understanding of cybersecurity principles, network protocols, and security tools.",
            "skills_required": "Network Security, Risk Assessment, Security Tools",
            "experience_level": "Entry"
        },
        
        # Business Roles
        {
            "name": "Marketing Intern",
            "industry": "Business",
            "company": "FinEdge",
            "description": "Support marketing campaigns, conduct market research, and analyze campaign performance.",
            "requirements": "Knowledge of marketing principles, social media platforms, and basic analytics.",
            "skills_required": "Marketing, Social Media, Analytics",
            "experience_level": "Entry"
        },
        {
            "name": "Business Analyst Intern",
            "industry": "Business",
            "company": "GlobalStrategy Partners",
            "description": "Collect and analyze business data to provide insights and recommendations for improvement.",
            "requirements": "Knowledge of business processes, data analysis, and problem-solving skills.",
            "skills_required": "Data Analysis, Business Knowledge, Problem Solving",
            "experience_level": "Entry"
        },
        
        # Healthcare Roles
        {
            "name": "Clinical Research Intern",
            "industry": "Healthcare",
            "company": "MediCura",
            "description": "Assist in conducting clinical trials, collecting and analyzing patient data, and preparing research reports.",
            "requirements": "Knowledge of medical terminology, research methods, and data analysis.",
            "skills_required": "Research Methods, Data Analysis, Medical Knowledge",
            "experience_level": "Entry"
        },
        {
            "name": "Healthcare Administration Intern",
            "industry": "Healthcare",
            "company": "BioGenetics",
            "description": "Support administrative functions in healthcare settings, including patient records management and operational workflow.",
            "requirements": "Knowledge of healthcare systems, administrative procedures, and regulatory compliance.",
            "skills_required": "Administration, Healthcare Knowledge, Organization",
            "experience_level": "Entry"
        },
        
        # Engineering Roles
        {
            "name": "Civil Engineering Intern",
            "industry": "Engineering",
            "company": "EngiPro",
            "description": "Assist in designing and analyzing civil structures and infrastructure projects.",
            "requirements": "Knowledge of civil engineering principles, CAD software, and structural analysis.",
            "skills_required": "CAD, Structural Analysis, Technical Drawing",
            "experience_level": "Entry"
        },
        {
            "name": "Mechanical Engineering Intern",
            "industry": "Engineering",
            "company": "RoboTech Innovations",
            "description": "Support the design, testing, and analysis of mechanical systems and components.",
            "requirements": "Knowledge of mechanical engineering principles, CAD software, and physics.",
            "skills_required": "CAD, Engineering Design, Materials Science",
            "experience_level": "Entry"
        },
        
        # Creative Arts Roles
        {
            "name": "Graphic Design Intern",
            "industry": "Creative Arts",
            "company": "DesignFusion",
            "description": "Create visual concepts and designs for various media including print, digital, and social.",
            "requirements": "Knowledge of design principles, proficiency in design software, and a strong portfolio.",
            "skills_required": "Adobe Creative Suite, Typography, Visual Design",
            "experience_level": "Entry"
        },
        {
            "name": "Content Creator Intern",
            "industry": "Creative Arts",
            "company": "ArtSpace Studios",
            "description": "Develop engaging content for various platforms including blogs, social media, and websites.",
            "requirements": "Strong writing skills, creativity, and understanding of content marketing.",
            "skills_required": "Writing, Content Strategy, SEO",
            "experience_level": "Entry"
        },
        
        # Education Roles
        {
            "name": "Educational Technology Intern",
            "industry": "Education",
            "company": "EduTech Solutions",
            "description": "Support the development and implementation of educational technology solutions.",
            "requirements": "Knowledge of educational principles, e-learning platforms, and instructional design.",
            "skills_required": "E-Learning, Instructional Design, Educational Technology",
            "experience_level": "Entry"
        },
        {
            "name": "Curriculum Development Intern",
            "industry": "Education",
            "company": "Global Learning Institute",
            "description": "Assist in developing and reviewing educational curriculum for various subjects and grade levels.",
            "requirements": "Knowledge of pedagogy, curriculum design, and subject matter expertise.",
            "skills_required": "Curriculum Design, Educational Theory, Content Creation",
            "experience_level": "Entry"
        },
        
        # Finance & Banking Roles
        {
            "name": "Financial Analyst Intern",
            "industry": "Finance & Banking",
            "company": "Quantum Finance",
            "description": "Analyze financial data, prepare reports, and assist in financial planning and forecasting.",
            "requirements": "Knowledge of financial principles, Excel, and financial analysis techniques.",
            "skills_required": "Financial Analysis, Excel, Financial Modeling",
            "experience_level": "Entry"
        },
        {
            "name": "Investment Banking Intern",
            "industry": "Finance & Banking",
            "company": "DigiBank",
            "description": "Support investment banking activities including mergers and acquisitions, capital raising, and market research.",
            "requirements": "Knowledge of finance, accounting, and investment banking principles.",
            "skills_required": "Financial Analysis, Valuation, Market Research",
            "experience_level": "Entry"
        }
    ]
    
    # Add roles to the database
    for role_data in roles:
        industry_name = role_data.pop("industry")
        company_name = role_data.pop("company")
        
        industry = industry_objects.get(industry_name)
        company = company_dict.get(company_name)
        
        if not industry:
            logger.error(f"Industry not found for role: {industry_name}")
            continue
        
        if not company:
            logger.error(f"Company not found for role: {company_name}")
            continue
        
        role = Role.query.filter_by(name=role_data["name"], company_id=company.id).first()
        if not role:
            role = Role(
                industry_id=industry.id,
                company_id=company.id,
                **role_data
            )
            db.session.add(role)
            logger.info(f"Created role: {role_data['name']} for {company_name}")
    
    db.session.commit()
    logger.info("Data initialization complete")