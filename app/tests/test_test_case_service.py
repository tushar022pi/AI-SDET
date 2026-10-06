from app.services.test_case_service import TestCaseService
import pytest


def test_validate_valid_test_cases():
    service = TestCaseService()

    data = {
        "test_cases": [
            {
                "title": "Test 1",
                "steps": ["Step 1", "Step 2"],
                "expected_result": "Requirement is satisfied."
            },
            {
                "title": "Test 2",
                "steps": ["Step 1", "Step 2"],
                "expected_result": "Invalid value is rejected."
            },
            {
                "title": "Test 3",
                "steps": ["Step 1", "Step 2"],
                "expected_result": "Requirement remains satisfied."
            }
        ]
    }

    service.validate_test_cases(data)


def test_validate_rejects_missing_test_cases():
    service = TestCaseService()

    data = {}

    with pytest.raises(ValueError):
        service.validate_test_cases(data)


def test_validate_rejects_too_few_test_cases():
    service = TestCaseService()

    data = {
        "test_cases": [
            {
                "title": "Test 1",
                "steps": ["Step 1"],
                "expected_result": "Requirement is satisfied."
            }
        ]
    }

    with pytest.raises(ValueError):
        service.validate_test_cases(data)


def test_validate_rejects_missing_field():
    service = TestCaseService()

    data = {
        "test_cases": [
            {
                "title": "Test 1",
                "steps": ["Step 1"],
                "expected_result": "Requirement is satisfied."
            },
            {
                "title": "Test 2",
                "steps": ["Step 1"],
                "expected_result": "Requirement is satisfied."
            },
            {
                "title": "Test 3",
                "steps": ["Step 1"]
            }
        ]
    }

    with pytest.raises(ValueError):
        service.validate_test_cases(data)


def test_validate_rejects_empty_steps():
    service = TestCaseService()

    data = {
        "test_cases": [
            {
                "title": "Test 1",
                "steps": [],
                "expected_result": "Requirement is satisfied."
            },
            {
                "title": "Test 2",
                "steps": ["Step 1"],
                "expected_result": "Requirement is satisfied."
            },
            {
                "title": "Test 3",
                "steps": ["Step 1"],
                "expected_result": "Requirement is satisfied."
            }
        ]
    }

    with pytest.raises(ValueError):
        service.validate_test_cases(data)