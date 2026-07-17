class TestCaseService:

    def generate_test_cases(self, heading, body_text):

        test_cases = []

        text = body_text.lower()

        if "pdf" in text:
            test_cases.append(
                "Verify PDF is parsed successfully"
            )

        if "version" in text:
            test_cases.append(
                "Verify document versioning works correctly"
            )

        if "hash" in text:
            test_cases.append(
                "Verify content hash changes when content changes"
            )

        if "api" in text:
            test_cases.append(
                "Verify API returns expected response"
            )

        if not test_cases:
            test_cases.append(
                f"Verify section '{heading}' behaves as expected"
            )

        return test_cases