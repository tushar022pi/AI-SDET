from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "AI SDET Assignment Running"


def test_ingest_version_1():
    response = client.post("/ingest/1")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data


def test_ingest_version_2():
    response = client.post("/ingest/2")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data


def test_nodes_contains_version_1():
    response = client.get("/nodes")

    assert response.status_code == 200

    nodes = response.json()

    assert isinstance(nodes, list)
    assert len(nodes) > 0

    version_1_nodes = [
        node
        for node in nodes
        if node["document_version"] == 1
    ]

    assert len(version_1_nodes) > 0


def test_nodes_contains_version_2():
    response = client.get("/nodes")

    assert response.status_code == 200

    nodes = response.json()

    assert isinstance(nodes, list)

    version_2_nodes = [
        node
        for node in nodes
        if node["document_version"] == 2
    ]

    assert len(version_2_nodes) > 0


def test_compare_versions():
    response = client.get("/compare")

    assert response.status_code == 200

    data = response.json()

    assert "unchanged" in data
    assert "changed" in data
    assert "new_nodes" in data

    changed_headings = [
        item["heading"]
        for item in data["changed"]
    ]

    assert "1. Installation" in changed_headings
    assert "3. Network Configuration" in changed_headings

    assert "2. Initial Setup" in data["unchanged"]
    assert "4. Safety Checks" in data["unchanged"]
    assert "5. Troubleshooting" in data["unchanged"]


def test_search_version_2():
    response = client.get(
        "/search",
        params={
            "q": "DHCP",
            "version": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "DHCP"
    assert data["version"] == 2

    results = data["results"]

    assert isinstance(results, list)
    assert len(results) > 0

    headings = [
        result["heading"]
        for result in results
    ]

    assert "3. Network Configuration" in headings


def test_create_selection():
    response = client.post(
        "/selection",
        json={
            "selections": [
                {
                    "node_id": 2,
                    "version": 1
                }
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "selection_id" in data
    assert "selection_hash" in data
    assert data["selection_count"] == 1

    assert len(data["selections"]) == 1

    selected = data["selections"][0]

    assert selected["node_id"] == 2
    assert selected["version"] == 1
    assert selected["heading"] == "1. Installation"


def test_duplicate_selection_is_reused():
    payload = {
        "selections": [
            {
                "node_id": 2,
                "version": 1
            }
        ]
    }

    first_response = client.post(
        "/selection",
        json=payload
    )

    second_response = client.post(
        "/selection",
        json=payload
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert (
        first_data["selection_id"]
        == second_data["selection_id"]
    )

    assert (
        first_data["selection_hash"]
        == second_data["selection_hash"]
    )


def test_generate_tests_for_selection():
    selection_response = client.post(
        "/selection",
        json={
            "selections": [
                {
                    "node_id": 2,
                    "version": 1
                }
            ]
        }
    )

    assert selection_response.status_code == 200

    selection_id = (
        selection_response.json()["selection_id"]
    )

    response = client.get(
        "/generate-tests/2",
        params={
            "selection_id": selection_id
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["node_id"] == 2
    assert data["selection_id"] == selection_id

    test_cases = data["test_cases"]

    assert isinstance(test_cases, list)
    assert len(test_cases) == 3

    for test_case in test_cases:
        assert test_case["selection_id"] == selection_id
        assert test_case["title"]

        assert isinstance(
            test_case["steps"],
            list
        )

        assert len(test_case["steps"]) > 0

        assert test_case["expected_result"]


def test_retrieve_generated_tests():
    response = client.get(
        "/test-cases/2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["node_id"] == 2
    assert data["test_case_count"] > 0

    test_cases = data["test_cases"]

    assert isinstance(test_cases, list)

    for test_case in test_cases:
        assert "id" in test_case
        assert "node_id" in test_case
        assert "document_version" in test_case
        assert "logical_node_id" in test_case
        assert "source_content_hash" in test_case
        assert "selection_id" in test_case
        assert "title" in test_case
        assert "steps" in test_case
        assert "expected_result" in test_case


def test_staleness_detection():
    response = client.get(
        "/test-cases/2/staleness"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["node_id"] == 2

    test_cases = data["test_cases"]

    assert isinstance(test_cases, list)
    assert len(test_cases) > 0

    for test_case in test_cases:
        assert test_case["status"] == "stale"
        assert test_case["generated_from_version"] == 1
        assert test_case["current_version"] == 2
        assert test_case["source_content_hash"]
        assert test_case["current_content_hash"]

        assert (
            test_case["source_content_hash"]
            != test_case["current_content_hash"]
        )