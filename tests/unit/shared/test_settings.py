from src.shared.config.settings import Settings


def test_should_load_default_settings() -> None:
    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "Strategic Indicators AI"
    assert settings.AI_PROVIDER == "ollama"
    assert settings.AI_MODEL == "llama3.2"
    assert settings.AI_BASE_URL == "http://localhost:11434/v1"
    assert settings.AI_TIMEOUT_SECONDS == 30.0


def test_should_allow_overriding_settings() -> None:
    custom = Settings(
        AI_PROVIDER="openai",
        AI_MODEL="gpt-4o",
        AI_BASE_URL="https://api.openai.com/v1",
        AI_API_KEY="sk-test",
    )
    assert custom.AI_PROVIDER == "openai"
    assert custom.AI_MODEL == "gpt-4o"
    assert custom.AI_BASE_URL == "https://api.openai.com/v1"
    assert custom.AI_API_KEY == "sk-test"
