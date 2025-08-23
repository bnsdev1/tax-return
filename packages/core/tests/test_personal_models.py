"""Unit tests for personal information models."""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from core.models.personal import PersonalInfo, ReturnContext


class TestPersonalInfo:
    """Test cases for PersonalInfo model."""
    
    def test_valid_personal_info(self):
        """Test creating a valid PersonalInfo instance."""
        dob = date(1990, 5, 15)
        personal_info = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            father_name="Robert Doe",
            date_of_birth=dob,
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        assert personal_info.pan == "ABCDE1234F"
        assert personal_info.name == "John Doe"
        assert personal_info.father_name == "Robert Doe"
        assert personal_info.date_of_birth == dob
        assert personal_info.address == "123 Main Street, City, State - 123456"
        assert personal_info.mobile == "9876543210"
        assert personal_info.email == "john.doe@example.com"
    
    def test_minimal_personal_info(self):
        """Test creating PersonalInfo with only required fields."""
        dob = date(1985, 12, 25)
        personal_info = PersonalInfo(
            pan="XYZAB5678C",
            name="Jane Smith",
            date_of_birth=dob,
            address="456 Oak Avenue, Town, State - 654321"
        )
        
        assert personal_info.pan == "XYZAB5678C"
        assert personal_info.name == "Jane Smith"
        assert personal_info.father_name is None
        assert personal_info.date_of_birth == dob
        assert personal_info.address == "456 Oak Avenue, Town, State - 654321"
        assert personal_info.mobile is None
        assert personal_info.email is None
    
    def test_pan_validation(self):
        """Test PAN validation."""
        base_data = {
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Valid PAN
        personal_info = PersonalInfo(pan="ABCDE1234F", **base_data)
        assert personal_info.pan == "ABCDE1234F"
        
        # Invalid PAN formats
        invalid_pans = [
            "",  # Empty
            "ABCD1234F",  # Too short
            "ABCDE12345F",  # Too long
            "12345ABCDF",  # Wrong format
            "ABCDE123AF",  # Wrong format
            "abcde1234f",  # Lowercase (should be converted)
        ]
        
        for invalid_pan in invalid_pans[:-1]:  # Skip lowercase test
            with pytest.raises(ValidationError):
                PersonalInfo(pan=invalid_pan, **base_data)
        
        # Test lowercase conversion
        personal_info = PersonalInfo(pan="abcde1234f", **base_data)
        assert personal_info.pan == "ABCDE1234F"
    
    def test_name_validation(self):
        """Test name field validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Valid names
        valid_names = [
            "John Doe",
            "Mary-Jane Smith",
            "O'Connor",
            "Dr. Smith",
            "Jean-Pierre"
        ]
        
        for name in valid_names:
            personal_info = PersonalInfo(name=name, **base_data)
            assert personal_info.name == name.title()
        
        # Invalid names
        invalid_names = [
            "",  # Empty
            "   ",  # Only whitespace
            "John123",  # Contains numbers
            "John@Doe",  # Contains special characters
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError):
                PersonalInfo(name=invalid_name, **base_data)
    
    def test_date_of_birth_validation(self):
        """Test date of birth validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "address": "Test Address 123456"
        }
        
        today = date.today()
        
        # Valid dates
        valid_dates = [
            date(1990, 5, 15),  # Normal adult
            today - timedelta(days=18*365 + 5),  # Just over 18
            today - timedelta(days=80*365),  # 80 years old
        ]
        
        for valid_date in valid_dates:
            personal_info = PersonalInfo(date_of_birth=valid_date, **base_data)
            assert personal_info.date_of_birth == valid_date
        
        # Invalid dates
        invalid_dates = [
            today - timedelta(days=17*365),  # Under 18
            today - timedelta(days=121*365),  # Over 120 years
            today + timedelta(days=1),  # Future date
        ]
        
        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError):
                PersonalInfo(date_of_birth=invalid_date, **base_data)
    
    def test_address_validation(self):
        """Test address validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1)
        }
        
        # Valid addresses
        valid_addresses = [
            "123 Main Street, City, State - 123456",
            "Apartment 4B, Building Name, Area, City - 654321",
            "House No. 45, Street Name, Locality, City, State, PIN - 111111"
        ]
        
        for address in valid_addresses:
            personal_info = PersonalInfo(address=address, **base_data)
            assert personal_info.address == address
        
        # Invalid addresses
        invalid_addresses = [
            "",  # Empty
            "Short",  # Too short
            "   ",  # Only whitespace
        ]
        
        for invalid_address in invalid_addresses:
            with pytest.raises(ValidationError):
                PersonalInfo(address=invalid_address, **base_data)
    
    def test_mobile_validation(self):
        """Test mobile number validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Valid mobile numbers
        valid_mobiles = [
            "9876543210",
            "8765432109",
            "7654321098",
            "6543210987"
        ]
        
        for mobile in valid_mobiles:
            personal_info = PersonalInfo(mobile=mobile, **base_data)
            assert personal_info.mobile == mobile
        
        # Test None mobile
        personal_info = PersonalInfo(mobile=None, **base_data)
        assert personal_info.mobile is None
        
        # Invalid mobile numbers
        invalid_mobiles = [
            "123456789",  # Too short
            "12345678901",  # Too long
            "5876543210",  # Starts with 5
            "abcdefghij",  # Non-numeric
            "987-654-3210",  # Contains hyphens
        ]
        
        for invalid_mobile in invalid_mobiles:
            with pytest.raises(ValidationError):
                PersonalInfo(mobile=invalid_mobile, **base_data)
    
    def test_email_validation(self):
        """Test email validation."""
        base_data = {
            "pan": "ABCDE1234F",
            "name": "Test User",
            "date_of_birth": date(1990, 1, 1),
            "address": "Test Address 123456"
        }
        
        # Valid emails
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.in",
            "user+tag@example.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            personal_info = PersonalInfo(email=email, **base_data)
            assert personal_info.email == email.lower()
        
        # Test None email
        personal_info = PersonalInfo(email=None, **base_data)
        assert personal_info.email is None
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user space@example.com",
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError):
                PersonalInfo(email=invalid_email, **base_data)
    
    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        original = PersonalInfo(
            pan="ABCDE1234F",
            name="John Doe",
            father_name="Robert Doe",
            date_of_birth=date(1990, 5, 15),
            address="123 Main Street, City, State - 123456",
            mobile="9876543210",
            email="john.doe@example.com"
        )
        
        # Test serialization
        json_data = original.model_dump()
        assert json_data['pan'] == "ABCDE1234F"
        assert json_data['date_of_birth'] == date(1990, 5, 15)
        
        # Test deserialization
        restored = PersonalInfo.model_validate(json_data)
        assert restored == original
        
        # Test JSON string serialization
        json_str = original.model_dump_json()
        restored_from_json = PersonalInfo.model_validate_json(json_str)
        assert restored_from_json == original


class TestReturnContext:
    """Test cases for ReturnContext model."""
    
    def test_valid_return_context(self):
        """Test creating a valid ReturnContext instance."""
        filing_date = date(2024, 7, 31)
        context = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1",
            filing_date=filing_date,
            revised_return=False
        )
        
        assert context.assessment_year == "2025-26"
        assert context.form_type == "ITR1"
        assert context.filing_date == filing_date
        assert context.revised_return is False
        assert context.original_return_date is None
    
    def test_minimal_return_context(self):
        """Test creating ReturnContext with only required fields."""
        context = ReturnContext(
            assessment_year="2024-25",
            form_type="ITR2"
        )
        
        assert context.assessment_year == "2024-25"
        assert context.form_type == "ITR2"
        assert context.filing_date is None
        assert context.revised_return is False
        assert context.original_return_date is None
    
    def test_revised_return_context(self):
        """Test creating a revised return context."""
        filing_date = date(2024, 12, 31)
        original_date = date(2024, 7, 31)
        
        context = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1",
            filing_date=filing_date,
            revised_return=True,
            original_return_date=original_date
        )
        
        assert context.assessment_year == "2025-26"
        assert context.form_type == "ITR1"
        assert context.filing_date == filing_date
        assert context.revised_return is True
        assert context.original_return_date == original_date
    
    def test_assessment_year_validation(self):
        """Test assessment year validation."""
        base_data = {"form_type": "ITR1"}
        
        # Valid assessment years
        valid_years = [
            "2024-25",
            "2025-26",
            "2023-24",
            "2030-31"
        ]
        
        for year in valid_years:
            context = ReturnContext(assessment_year=year, **base_data)
            assert context.assessment_year == year
        
        # Invalid assessment years
        invalid_years = [
            "",  # Empty
            "2024-2025",  # Wrong format
            "24-25",  # Wrong format
            "2024-24",  # Same year
            "2024-27",  # Wrong increment
            "invalid",  # Non-numeric
        ]
        
        for invalid_year in invalid_years:
            with pytest.raises(ValidationError):
                ReturnContext(assessment_year=invalid_year, **base_data)
    
    def test_form_type_validation(self):
        """Test form type validation."""
        base_data = {"assessment_year": "2025-26"}
        
        # Valid form types
        valid_forms = ["ITR1", "ITR2", "ITR3", "ITR4", "ITR5", "ITR6", "ITR7"]
        
        for form_type in valid_forms:
            context = ReturnContext(form_type=form_type, **base_data)
            assert context.form_type == form_type
        
        # Test lowercase conversion
        context = ReturnContext(form_type="itr1", **base_data)
        assert context.form_type == "ITR1"
        
        # Invalid form types
        invalid_forms = [
            "",  # Empty
            "ITR8",  # Non-existent
            "FORM1",  # Wrong format
            "invalid",  # Invalid
        ]
        
        for invalid_form in invalid_forms:
            with pytest.raises(ValidationError):
                ReturnContext(form_type=invalid_form, **base_data)
    
    def test_filing_date_validation(self):
        """Test filing date validation."""
        base_data = {
            "assessment_year": "2025-26",
            "form_type": "ITR1"
        }
        
        today = date.today()
        
        # Valid filing dates
        valid_dates = [
            today,  # Today
            today - timedelta(days=1),  # Yesterday
            today - timedelta(days=365),  # One year ago
        ]
        
        for filing_date in valid_dates:
            context = ReturnContext(filing_date=filing_date, **base_data)
            assert context.filing_date == filing_date
        
        # Invalid filing dates
        invalid_dates = [
            today + timedelta(days=1),  # Future date
            today + timedelta(days=365),  # Far future
        ]
        
        for invalid_date in invalid_dates:
            with pytest.raises(ValidationError):
                ReturnContext(filing_date=invalid_date, **base_data)
    
    def test_revised_return_validation(self):
        """Test revised return validation."""
        base_data = {
            "assessment_year": "2025-26",
            "form_type": "ITR1",
            "filing_date": date(2024, 12, 31)
        }
        
        # Valid revised return with original date
        original_date = date(2024, 7, 31)
        context = ReturnContext(
            revised_return=True,
            original_return_date=original_date,
            **base_data
        )
        assert context.revised_return is True
        assert context.original_return_date == original_date
        
        # Invalid: revised return without original date
        with pytest.raises(ValidationError):
            ReturnContext(revised_return=True, **base_data)
        
        # Invalid: original date without revised return
        with pytest.raises(ValidationError):
            ReturnContext(
                revised_return=False,
                original_return_date=original_date,
                **base_data
            )
        
        # Invalid: original date after filing date
        with pytest.raises(ValidationError):
            ReturnContext(
                revised_return=True,
                original_return_date=date(2025, 1, 31),  # After filing date
                **base_data
            )
    
    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        original = ReturnContext(
            assessment_year="2025-26",
            form_type="ITR1",
            filing_date=date(2024, 7, 31),
            revised_return=True,
            original_return_date=date(2024, 3, 31)
        )
        
        # Test serialization
        json_data = original.model_dump()
        assert json_data['assessment_year'] == "2025-26"
        assert json_data['form_type'] == "ITR1"
        assert json_data['filing_date'] == date(2024, 7, 31)
        assert json_data['revised_return'] is True
        assert json_data['original_return_date'] == date(2024, 3, 31)
        
        # Test deserialization
        restored = ReturnContext.model_validate(json_data)
        assert restored == original
        
        # Test JSON string serialization
        json_str = original.model_dump_json()
        restored_from_json = ReturnContext.model_validate_json(json_str)
        assert restored_from_json == original