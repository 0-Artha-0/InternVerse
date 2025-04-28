"""
Database migration script for the Virtual Internship Simulator
"""
import logging
from app import app, db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run all database migrations
    """
    try:
        with app.app_context():
            # Check existing columns
            inspect_query = text("PRAGMA table_info(internship_track)")
            result = db.session.execute(inspect_query)
            columns = [row[1] for row in result.fetchall()]
            
            # Add company_id column if it doesn't exist
            if 'company_id' not in columns:
                alter_query = text("ALTER TABLE internship_track ADD COLUMN company_id INTEGER REFERENCES company(id)")
                db.session.execute(alter_query)
                db.session.commit()
                logger.info("Successfully added company_id column to internship_track table")
            else:
                logger.info("company_id column already exists in internship_track table")
            
            # Add role_id column if it doesn't exist
            if 'role_id' not in columns:
                alter_query = text("ALTER TABLE internship_track ADD COLUMN role_id INTEGER REFERENCES role(id)")
                db.session.execute(alter_query)
                db.session.commit()
                logger.info("Successfully added role_id column to internship_track table")
            else:
                logger.info("role_id column already exists in internship_track table")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    run_migrations()
    logger.info("All migrations completed successfully")