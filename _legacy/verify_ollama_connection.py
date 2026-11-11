"""Check that the connection to a local Ollama server is working.

Steps:
    1. Load the environment.
    2. Configure the Ollama model.
    3. Validate the environment (e.g. OLLAMA_API_BASE is set).
    4. Call the model via ``generate_completion``.
"""

from dotenv import load_dotenv, find_dotenv

from lib.completion import generate_completion
from lib.validation import validate_environment_for_model


def main() -> None:
    load_dotenv(find_dotenv())

    PROVIDER = "ollama"
    MODEL = "deepseek-r1:1.5b"
    MODEL_ID = f"{PROVIDER}/{MODEL}"

    validate_environment_for_model(model=MODEL_ID)

    SYSTEM_PROMPT = "You are a friendly assistant."
    USER_PROMPT = "Say hello in one short sentence to confirm the connection works."

    response = generate_completion(
        user_prompt=USER_PROMPT,
        model_name=MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        verbose=True,
    )

    print("\nRESPONSE from Ollama model:")
    print(response)


if __name__ == "__main__":
    main()
