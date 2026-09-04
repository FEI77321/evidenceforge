from evidenceforge.infrastructure.config import Settings


def test_default_fixture_source_path_points_to_an_existing_file() -> None:
    settings = Settings(
        postgres_user="test-user",
        postgres_password="test-password",
        postgres_db="test-database",
    )

    fixture_path = settings.fixture_research_source_path

    assert fixture_path.is_file()
    assert fixture_path.name == "fastapi_background_tasks.md"