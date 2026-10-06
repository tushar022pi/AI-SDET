import os
import json
from openai import OpenAI


class TestCaseService:
    __test__ = False

    def __init__(self):
        self.use_mock = os.getenv(
            "USE_MOCK_LLM",
            "true"
        ).lower() == "true"

        if not self.use_mock:
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set"
                )

            self.client = OpenAI(api_key=api_key)

    def generate_test_cases(self, heading, body_text):

        if self.use_mock:
            return self.generate_mock_test_cases(
                heading,
                body_text
            )

        prompt = f"""
You are an AI test engineer.

Generate 3 to 5 concrete, repeatable software test cases
based ONLY on the requirement below.

Section:
{heading}

Requirement:
{body_text}

Return ONLY valid JSON in exactly this format:

{{
  "test_cases": [
    {{
      "title": "string",
      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ],
      "expected_result": "string"
    }}
  ]
}}

Rules:
- Do not invent requirements.
- Every test case must be traceable to the supplied requirement.
- Steps must be concrete and repeatable.
- Expected results must directly reflect the requirement.
- Return between 3 and 5 test cases.
"""

        max_attempts = 2
        last_error = None

        for attempt in range(max_attempts):

            try:
                response = self.client.responses.create(
                    model="gpt-5-mini",
                    input=prompt
                )

                output = response.output_text

                parsed = json.loads(output)

                self.validate_test_cases(parsed)

                return parsed["test_cases"]

            except (json.JSONDecodeError, ValueError) as error:

                last_error = error

                if attempt == max_attempts - 1:
                    break

                prompt = f"""
The previous response was invalid.

Fix the response and return ONLY valid JSON.

The JSON must have exactly this structure:

{{
  "test_cases": [
    {{
      "title": "string",
      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ],
      "expected_result": "string"
    }}
  ]
}}

Requirements:

Section:
{heading}

Requirement:
{body_text}

Rules:
- Return 3 to 5 test cases.
- Every test case must contain title, steps, and expected_result.
- steps must be a non-empty list.
- Do not invent requirements.
- Every test case must be traceable to the supplied requirement.
- Make every test case concrete and repeatable.
- Expected results must directly reflect the requirement.
"""

        raise ValueError(
            f"LLM returned malformed output after "
            f"{max_attempts} attempts: {last_error}"
        )

    def validate_test_cases(self, parsed):

        if not isinstance(parsed, dict):
            raise ValueError(
                "LLM output must be a JSON object"
            )

        if "test_cases" not in parsed:
            raise ValueError(
                "LLM output is missing 'test_cases'"
            )

        test_cases = parsed["test_cases"]

        if not isinstance(test_cases, list):
            raise ValueError(
                "'test_cases' must be a list"
            )

        if not 3 <= len(test_cases) <= 5:
            raise ValueError(
                "LLM must return between 3 and 5 test cases"
            )

        for index, test_case in enumerate(test_cases):

            if not isinstance(test_case, dict):
                raise ValueError(
                    f"Test case {index + 1} must be an object"
                )

            required_fields = [
                "title",
                "steps",
                "expected_result"
            ]

            for field in required_fields:

                if field not in test_case:
                    raise ValueError(
                        f"Test case {index + 1} is missing '{field}'"
                    )

            if not isinstance(test_case["title"], str):
                raise ValueError(
                    f"Test case {index + 1} title must be a string"
                )

            if not isinstance(test_case["steps"], list):
                raise ValueError(
                    f"Test case {index + 1} steps must be a list"
                )

            if len(test_case["steps"]) == 0:
                raise ValueError(
                    f"Test case {index + 1} must contain "
                    f"at least one step"
                )

            for step in test_case["steps"]:

                if not isinstance(step, str):
                    raise ValueError(
                        f"Test case {index + 1} contains "
                        f"a non-string step"
                    )

                if not step.strip():
                    raise ValueError(
                        f"Test case {index + 1} contains "
                        f"an empty step"
                    )

            if not isinstance(
                test_case["expected_result"],
                str
            ):
                raise ValueError(
                    f"Test case {index + 1} expected_result "
                    f"must be a string"
                )

            if not test_case["expected_result"].strip():
                raise ValueError(
                    f"Test case {index + 1} has "
                    f"an empty expected_result"
                )

    def generate_mock_test_cases(
        self,
        heading,
        body_text
    ):

        requirement = body_text.strip()

        return [
            {
                "title": (
                    f"Verify the documented requirement "
                    f"for {heading}"
                ),
                "steps": [
                    f"Open the '{heading}' section.",
                    f"Review the requirement: {requirement}",
                    (
                        "Configure the system according "
                        "to the stated requirement."
                    ),
                    (
                        "Verify that the configured value "
                        "satisfies the requirement."
                    )
                ],
                "expected_result": (
                    f"The system satisfies the documented "
                    f"requirement: {requirement}"
                )
            },
            {
                "title": (
                    f"Verify a value below the requirement "
                    f"for {heading}"
                ),
                "steps": [
                    f"Open the '{heading}' configuration.",
                    f"Review the requirement: {requirement}",
                    (
                        "Configure a value that is below "
                        "the documented minimum."
                    ),
                    "Apply the configuration.",
                    (
                        "Verify how the system handles "
                        "the invalid value."
                    )
                ],
                "expected_result": (
                    "The system rejects the invalid value "
                    "or otherwise prevents the documented "
                    "requirement from being violated."
                )
            },
            {
                "title": (
                    f"Verify the requirement after restart "
                    f"for {heading}"
                ),
                "steps": [
                    f"Open the '{heading}' section.",
                    (
                        f"Configure the system according "
                        f"to: {requirement}"
                    ),
                    "Save the configuration.",
                    "Restart the system.",
                    "Verify the configuration after restart."
                ],
                "expected_result": (
                    f"The configuration remains compliant "
                    f"with the documented requirement after "
                    f"restart: {requirement}"
                )
            }
        ]