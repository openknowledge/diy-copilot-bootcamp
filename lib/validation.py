from litellm import validate_environment


def validate_environment_for_model(model: str):
    validation_result = validate_environment(model)
    missing_keys = validation_result["missing_keys"]

    if len(missing_keys) > 0:
        raise ValueError(
            f"Necessary environment variables for mode {model} missing: {missing_keys}"
        )
