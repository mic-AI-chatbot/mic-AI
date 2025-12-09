import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from mic.auth import register_user, hash_password, verify_password
from mic.models import User # Assuming User model is accessible

# Mock the User model for testing purposes if needed,
# but for register_user, we mostly interact with the session.

@pytest.fixture
def mock_db_session():
    """Fixture to provide a mocked SQLAlchemy session."""
    session = MagicMock(spec=Session)
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    return session

def test_register_user_success(mock_db_session):
    """Test successful user registration."""
    username = "testuser"
    password = "password123"
    email = "test@example.com"
    age = 30
    location = "Testland"

    result = register_user(mock_db_session, username, password, email, age, location)

    assert result is True
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_not_called()

    # Verify password hashing (indirectly, by checking if User object was created with hashed password)
    # This requires inspecting the call to db.add, which is more complex for a simple mock.
    # For a more robust test, you'd mock the User constructor or inspect mock_db_session.add.call_args
    # For now, we trust hash_password works as it's a separate unit.

def test_register_user_invalid_email(mock_db_session):
    """Test user registration with an invalid email format."""
    username = "testuser"
    password = "password123"
    email = "invalid-email" # Invalid email
    age = 30
    location = "Testland"

    result = register_user(mock_db_session, username, password, email, age, location)

    assert result is False
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.rollback.assert_not_called()

def test_register_user_invalid_age(mock_db_session):
    """Test user registration with an invalid age."""
    username = "testuser"
    password = "password123"
    email = "test@example.com"
    age = 150 # Invalid age
    location = "Testland"

    result = register_user(mock_db_session, username, password, email, age, location)

    assert result is False
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.rollback.assert_not_called()

def test_register_user_existing_username_or_email(mock_db_session):
    """Test user registration when username or email already exists (IntegrityError)."""
    username = "existinguser"
    password = "password123"
    email = "existing@example.com"
    age = 25
    location = "Testland"

    # Simulate IntegrityError on commit
    mock_db_session.commit.side_effect = IntegrityError("duplicate key value violates unique constraint", {}, {})

    result = register_user(mock_db_session, username, password, email, age, location)

    assert result is False
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_called_once()

# You can add more tests for hash_password and verify_password if they are not
# implicitly covered by other tests or if you want to test them in isolation.
def test_hash_and_verify_password():
    password = "securepassword"
    hashed = hash_password(password)
    assert isinstance(hashed, bytes)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
