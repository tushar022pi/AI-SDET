from app.services.version_service import VersionService


def test_compare_versions():

    service = VersionService()

    result = service.compare_versions(
        [],
        []
    )

    assert "unchanged" in result
    assert "changed" in result
    assert "new_nodes" in result