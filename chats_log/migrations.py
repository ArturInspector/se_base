import logging
from sqlalchemy import text, inspect
from db import Session, engine

logger = logging.getLogger(__name__)


def check_and_add_column(table_name, column_name, column_type, default=None):
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name in columns:
            return False
        
        default_clause = f" DEFAULT {default}" if default else ""
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"
        logger.info(f"Adding column {column_name} to {table_name}")
        
        with Session() as session:
            session.execute(text(sql))
            session.commit()
        return True
    except Exception as e:
        logger.debug(f"Column {column_name} already exists or error: {e}")
        return False


def check_and_create_table(table_name, create_sql):
    try:
        inspector = inspect(engine)
        if table_name in inspector.get_table_names():
            return False
        
        logger.info(f"Creating table {table_name}")
        
        with Session() as session:
            session.execute(text(create_sql))
            session.commit()
        return True
    except Exception as e:
        logger.debug(f"Table {table_name} already exists or error: {e}")
        return False


def run_migrations():
    logger.info("Starting auto-migrations for KPI system")
    
    changes = []
    
    if check_and_add_column('chats_logs', 'extracted_city', 'VARCHAR(100)'):
        changes.append('extracted_city')
    
    if check_and_add_column('chats_logs', 'extracted_people', 'INTEGER'):
        changes.append('extracted_people')
    
    if check_and_add_column('chats_logs', 'extracted_hours', 'INTEGER'):
        changes.append('extracted_hours')
    
    if check_and_add_column('chats_logs', 'extracted_phone', 'VARCHAR(20)'):
        changes.append('extracted_phone')
    
    if check_and_add_column('chats_logs', 'extracted_intent', 'VARCHAR(50)'):
        changes.append('extracted_intent')
    
    if check_and_add_column('chats_logs', 'ai_model', 'VARCHAR(50)', "'gpt-4o'"):
        changes.append('ai_model')
    
    if check_and_add_column('chats_logs', 'function_calls', 'TEXT'):
        changes.append('function_calls')
    
    if check_and_add_column('chats_logs', 'had_tool_calls', 'BOOLEAN', 'FALSE'):
        changes.append('had_tool_calls')
    
    if check_and_add_column('chats_logs', 'deal_created', 'BOOLEAN', 'FALSE'):
        changes.append('deal_created')
    
    if check_and_add_column('chats_logs', 'deal_id', 'INTEGER'):
        changes.append('deal_id')
    
    if check_and_add_column('chats_logs', 'quality_score', 'FLOAT'):
        changes.append('quality_score')
    
    if check_and_add_column('chats_logs', 'has_hallucination', 'BOOLEAN', 'FALSE'):
        changes.append('has_hallucination')
    
    if check_and_add_column('chats_logs', 'is_too_verbose', 'BOOLEAN', 'FALSE'):
        changes.append('is_too_verbose')
    
    if check_and_add_column('chats_logs', 'missed_opportunity', 'BOOLEAN', 'FALSE'):
        changes.append('missed_opportunity')
    
    if check_and_add_column('chats_logs', 'outcome', 'VARCHAR(50)'):
        changes.append('outcome')
    
    if check_and_add_column('chats_logs', 'failure_reason', 'VARCHAR(100)'):
        changes.append('failure_reason')
    
    if check_and_add_column('chats_logs', 'experiment_variant', 'VARCHAR(50)'):
        changes.append('experiment_variant')
    
    if check_and_add_column('chats_logs', 'response_time_ms', 'INTEGER'):
        changes.append('response_time_ms')
    
    if check_and_add_column('chats_logs', 'tokens_used', 'INTEGER'):
        changes.append('tokens_used')
    
    conversation_grades_sql = """
    CREATE TABLE conversation_grades (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        chat_id VARCHAR(64) UNIQUE,
        outcome VARCHAR(50),
        deal_id INTEGER,
        total_messages INTEGER,
        messages_to_deal INTEGER,
        unnecessary_questions INTEGER,
        had_hallucinations BOOLEAN DEFAULT FALSE,
        had_data_extraction_errors BOOLEAN DEFAULT FALSE,
        had_business_rule_violations BOOLEAN DEFAULT FALSE,
        conversation_score FLOAT,
        started_at DATETIME,
        completed_at DATETIME,
        duration_minutes FLOAT,
        experiment_variant VARCHAR(50),
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    if check_and_create_table('conversation_grades', conversation_grades_sql):
        changes.append('conversation_grades table')
    
    if changes:
        logger.info(f"Auto-migration complete. Added: {', '.join(changes)}")
    else:
        logger.info("No migrations needed. Database is up to date.")
    
    return len(changes) > 0

