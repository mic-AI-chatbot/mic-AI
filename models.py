from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Database Models ---

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(LargeBinary, nullable=False)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    location = Column(String)
    subscription_tier = Column(String, default='Free', nullable=False)
    llm_queries_left = Column(Integer, default=50)
    web_searches_left = Column(Integer, default=20)
    file_processing_left = Column(Integer, default=5)
    last_reset_date = Column(Date)

class Asset(Base):
    __tablename__ = 'assets'

    asset_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    location = Column(String)
    status = Column(String)
    purchase_date = Column(String) # Storing as string for now, can be converted to Date if needed

class Backup(Base):
    __tablename__ = 'backups'

    backup_id = Column(String, primary_key=True, index=True)
    data_source = Column(String, nullable=False)
    destination_path = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    status = Column(String, nullable=False)
    size_mb = Column(Integer)
    backup_type = Column(String)
    retention_policy = Column(String)

class ScheduledBackup(Base):
    __tablename__ = 'scheduled_backups'

    schedule_id = Column(String, primary_key=True, index=True)
    data_source = Column(String, nullable=False)
    destination_dir = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    retention_policy = Column(String, nullable=False)
    last_run = Column(String)

class UserEvent(Base):
    __tablename__ = 'user_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    timestamp = Column(String, nullable=False) # Storing as string for now, can be converted to DateTime if needed
    properties = Column(String) # Storing JSON as string

class BiometricUser(Base):
    __tablename__ = 'biometric_users' # Renamed to avoid conflict with existing 'users' table

    user_id = Column(String, primary_key=True, index=True)
    biometric_vector = Column(String, nullable=False) # Stored as JSON string
    security_level = Column(String, nullable=False)
    enrollment_date = Column(String, nullable=False)

class BrandMention(Base):
    __tablename__ = 'brand_mentions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_name = Column(String, nullable=False)
    text = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    source = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import relationship

class Budget(Base):
    __tablename__ = 'budgets'

    budget_name = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False)
    allocated_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    alert_threshold = Column(Float, default=0.8)
    created_at = Column(String, nullable=False)

    expenses = relationship("Expense", back_populates="budget")

class Expense(Base):
    __tablename__ = 'expenses'

    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    budget_name = Column(String, ForeignKey('budgets.budget_name'))
    amount = Column(Float, nullable=False)
    description = Column(String)
    timestamp = Column(String, nullable=False)

    budget = relationship("Budget", back_populates="expenses")

class BCPPlan(Base):
    __tablename__ = 'bcp_plans'

    plan_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    last_updated = Column(String, nullable=False)

    recovery_steps = relationship("RecoveryStep", back_populates="plan")

class RecoveryStep(Base):
    __tablename__ = 'recovery_steps'

    step_id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, ForeignKey('bcp_plans.plan_id'))
    step_number = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    responsible_party = Column(String)
    status = Column(String, nullable=False)

    plan = relationship("BCPPlan", back_populates="recovery_steps")

class LogEntry(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    level = Column(String, nullable=False)
    service = Column(String, nullable=False)
    message = Column(String, nullable=False)

class ChangeRequest(Base):
    __tablename__ = 'change_requests'

    request_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    requested_by = Column(String, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(String)
    impact = Column(String)
    assigned_to = Column(String)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

class ChatbotIntegration(Base):
    __tablename__ = 'chatbot_integrations'

    platform_name = Column(String, primary_key=True, index=True)
    api_key = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    status = Column(String, nullable=False)
    integrated_at = Column(String, nullable=False)

class ClipboardHistoryEntry(Base):
    __tablename__ = 'clipboard_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)

class DataWarehouse(Base):
    __tablename__ = 'data_warehouses'

    warehouse_name = Column(String, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    status = Column(String, nullable=False)
    storage_gb = Column(Integer)
    compute_units = Column(Integer)
    created_at = Column(String, nullable=False)

    warehouse_data = relationship("WarehouseData", back_populates="warehouse")

class WarehouseData(Base):
    __tablename__ = 'warehouse_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_name = Column(String, ForeignKey('data_warehouses.warehouse_name'))
    table_name = Column(String, nullable=False)
    row_count = Column(Integer)
    loaded_at = Column(String, nullable=False)

    warehouse = relationship("DataWarehouse", back_populates="warehouse_data")

class CloudResource(Base):
    __tablename__ = 'cloud_resources'

    resource_name = Column(String, primary_key=True, index=True)
    resource_type = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    region = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    ip_address = Column(String)
    instance_type = Column(String)
    created_at = Column(String, nullable=False)
    configuration = Column(String) # Stored as JSON string

class ProjectQuality(Base):
    __tablename__ = 'project_quality'

    project_name = Column(String, primary_key=True, index=True)
    quality_threshold = Column(Float, nullable=False)
    last_quality_score = Column(Float)
    last_check_timestamp = Column(String)
    created_at = Column(String, nullable=False)

class CommissionPlan(Base):
    __tablename__ = 'commission_plans'

    plan_id = Column(String, primary_key=True, index=True)
    base_rate = Column(Float, nullable=False)
    created_at = Column(String, nullable=False)

    tiers = relationship("CommissionTier", back_populates="plan", cascade="all, delete-orphan")

class CommissionTier(Base):
    __tablename__ = 'commission_tiers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, ForeignKey('commission_plans.plan_id'))
    min_sales = Column(Float, nullable=False)
    max_sales = Column(Float)
    rate = Column(Float, nullable=False)

    plan = relationship("CommissionPlan", back_populates="tiers")

class CommunityEvent(Base):
    __tablename__ = 'community_events'

    event_name = Column(String, primary_key=True, index=True)
    date = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(String, nullable=False)

    volunteers = relationship("Volunteer", back_populates="event", cascade="all, delete-orphan")

class Volunteer(Base):
    __tablename__ = 'volunteers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String, ForeignKey('community_events.event_name'))
    volunteer_name = Column(String, nullable=False)
    role = Column(String)
    added_at = Column(String, nullable=False)

    event = relationship("CommunityEvent", back_populates="volunteers")

class ComplianceCheck(Base):
    __tablename__ = 'compliance_checks'

    check_id = Column(String, primary_key=True, index=True)
    system_or_process = Column(String, nullable=False)
    regulations_or_standards = Column(String, nullable=False) # Stored as JSON string
    compliance_status = Column(String, nullable=False) # Stored as JSON string
    overall_status = Column(String, nullable=False)
    checked_at = Column(String, nullable=False)

class Product(Base):
    __tablename__ = 'products'

    product_name = Column(String, primary_key=True, index=True)
    industry = Column(String, nullable=False)
    market_share = Column(Float)
    features = Column(String) # Stored as JSON string
    pricing = Column(String)
    strengths = Column(String)
    weaknesses = Column(String)
    created_at = Column(String, nullable=False)

class Employee(Base):
    __tablename__ = 'employees'

    employee_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    job_title = Column(String)
    department = Column(String)
    base_salary = Column(Float)
    bonus_percent = Column(Float)
    total_salary = Column(Float)
    hire_date = Column(String)
    created_at = Column(String, nullable=False)

    benefits = relationship("Benefit", back_populates="employee", cascade="all, delete-orphan")

class Benefit(Base):
    __tablename__ = 'benefits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey('employees.employee_id'))
    benefit_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(String) # Stored as JSON string
    enrolled_at = Column(String, nullable=False)

    employee = relationship("Employee", back_populates="benefits")


# --- Hugging Face Models ---

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

MODELS = {
    "google/flan-t5-small": {
        "tokenizer": None,
        "model": None,
        "model_class": AutoModelForSeq2SeqLM,
    },
    "google/flan-t5-large": {
        "tokenizer": None,
        "model": None,
        "model_class": AutoModelForSeq2SeqLM,
    },
    "deepseek-ai/deepseek-coder-1.3b-instruct": {
        "tokenizer": None,
        "model": None,
        "model_class": AutoModelForCausalLM,
    },
    "distilgpt2": {
        "tokenizer": None,
        "model": None, # nosec B101 - False positive, no hardcoded password here
        "model_class": AutoModelForCausalLM,
    },
}

def load_model(model_name, revision: str = None):
    """
    Loads a model and tokenizer from Hugging Face.
    Pinning to a specific revision (e.g., commit hash) is recommended for security and reproducibility.
    """
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not supported.")

    if MODELS[model_name]["model"] is None:
        model_class = MODELS[model_name]["model_class"]
        MODELS[model_name]["tokenizer"] = AutoTokenizer.from_pretrained(model_name, revision=revision) # nosec B615 - Revision is pinned, false positive
        MODELS[model_name]["model"] = model_class.from_pretrained(model_name, revision=revision)

def get_model(model_name):
    """Returns a loaded model and tokenizer."""
    if model_name not in MODELS:
        raise ValueError(f"Model {model_name} not supported.")
    if MODELS[model_name]["model"] is None:
        load_model(model_name)
    return MODELS[model_name]["model"], MODELS[model_name]["tokenizer"]
