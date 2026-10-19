from app.config import load_settings, validate_active_provider
from app.model_router import ModelRouter


def main() -> None:
    settings = load_settings()
    validate_active_provider(settings)

    router = ModelRouter(settings)

    response = router.generate([
        {
            "role": "system",
            "content": "You are a concise coding assistant.",
        },
        {
            "role": "user",
            "content": "Explain what a Python function is in one sentence.",
        },
    ])

    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Response: {response.content}")
    print(f"Usage: {response.usage}")


if __name__ == "__main__":
    main()
