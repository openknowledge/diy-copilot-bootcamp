from litellm import completion, get_supported_openai_params

from lib.constants import DEFAULT_GENERATION_MODEL
from lib.retry import call_with_retry


def generate_completion_with_tools(
    user_prompt: str,
    tools: list[dict],
    model_name: str = DEFAULT_GENERATION_MODEL,
    system_prompt: str = "You are a friendly assistant",
    verbose: bool = False,
) -> dict:
    """Call a model with tool declarations and return the response.

    Parameters
    ----------
    user_prompt : str
        The prompt to send to the model.
    tools : list[dict]
        List of tool declarations in OpenAI format.
    model_name : str
        The LiteLLM model identifier.
    system_prompt : str
        The system prompt to use.
    verbose : bool
        If True, print the raw response.

    Returns
    -------
    dict with keys:
        - "text": str | None — the text response (if any)
        - "tool_calls": list | None — list of tool calls (if any)
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = call_with_retry(
        completion,
        model=model_name,
        messages=messages,
        tools=tools,
    )

    message = response.choices[0].message

    if verbose:
        print(f"Response: {response}")

    return {
        "text": message.content,
        "tool_calls": message.tool_calls,
    }


class Chat:
    """A multi-turn chat session backed by LiteLLM.

    Maintains conversation history automatically. Each instance is an
    independent session — create a new instance to start a fresh conversation.

    Example
    -------
    >>> bot = Chat(system_prompt="You are a helpful assistant.")
    >>> answer = bot.send("Hello!")
    >>> answer = bot.send("Tell me more.")  # history is preserved
    >>> bot.clear()                          # reset without recreating
    """

    def __init__(
        self,
        system_prompt: str = "You are a friendly assistant",
        model_name: str = DEFAULT_GENERATION_MODEL,
        temperature: float = 0.9,
        max_tokens: int = 500,
    ):
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.history: list[dict] = []

    def send(self, user_prompt: str) -> str:
        """Send a message and return the assistant's reply.

        The conversation history is updated automatically after each call.

        Parameters
        ----------
        user_prompt : str
            The message to send to the model.

        Returns
        -------
        str
            The assistant's reply.
        """
        self.history.append({"role": "user", "content": user_prompt})
        messages = [{"role": "system", "content": self.system_prompt}] + self.history
        response = call_with_retry(
            completion,
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        answer = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def clear(self):
        """Clear the conversation history, keeping the system prompt."""
        self.history = []


def generate_completion(
    user_prompt: str,
    model_name: str = DEFAULT_GENERATION_MODEL,
    temperature: float = 0.9,
    top_p: float = None,
    top_k: int = None,
    max_output_tokens: int = 1000,
    presence_penalty: float = None,
    frequency_penalty: float = None,
    system_prompt: str = "You are a friendly assistant",
    response_format: dict | None = None,
    verbose: bool = False,
) -> str:
    """Calls a model with a given set of parameters and returns the completions

    Parameters
    ----------
    user_prompt : str
        The user prompt to use for the completion
    model_name : str, optional [default: DEFAULT_GENERATION_MODEL]
        The name of the model to use for the completion
    temperature : float, optional [default: 0.9]
        The temperature of the model
    max_output_tokens : int, optional [default: 600]
        The maximum number of output tokens to return
    presence_penalty : float [default: None]
        Controls how much the model penalizes new tokens that are already present in the conversation. Ranges from -2.0 to 2.0.
    frequency_penalty : float [default: None]
        Controls how much the model penalizes tokens proportionally to how often they have already appeared in the conversation. Ranges from -2.0 to 2.0.
    top_k : int [default: None]
        Determines the amount of tokens to be considered when sampling with temperature
    top_p : float [default: None]
        An alternative to sampling with temperature. It instructs the model to consider the results of the tokens with top_p probability. For example, 0.1 means only the tokens comprising the top 10% probability mass are considered.
    system_prompt : str, optional [default: "Your are a friendly assistant"]
        The system prompt to use for the completion
    response_format : dict | None, optional [default: None]
        Optional response format passed to LiteLLM (e.g. a Pydantic model class
        or ``{"type": "json_object"}``).
    verbose : bool, optional [default: False]
        Whether to print details of the completion process or not. Defaults to False
    Returns
    -------
    str :
        the generated text
    """
    if verbose:
        # print out summary of input values / parameters
        print("Generating answer for following config:")
        print(f"  - SYSTEM PROMPT used:\n {system_prompt}")
        print(f"  - USER PROMPT used:\n {user_prompt}")
        print(
            f"  - MODEL used:\n {model_name} (temperature = {temperature}, max_output_tokens = {max_output_tokens})"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    requested_params = {
        "temperature": temperature,
        "max_completion_tokens": max_output_tokens,
        "top_p": top_p,
        "top_k": top_k,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
    }
    provided = {k: v for k, v in requested_params.items() if v is not None}

    supported = set(get_supported_openai_params(model=model_name) or [])
    # LiteLLM reports `max_tokens`, but we pass it as `max_completion_tokens`.
    if "max_tokens" in supported:
        supported.add("max_completion_tokens")

    accepted = {k: v for k, v in provided.items() if k in supported}
    dropped = sorted(k for k in provided if k not in supported)
    if dropped:
        print(
            f"Warning: model '{model_name}' does not support the following "
            f"parameter(s); they were dropped: {dropped}"
        )

    kwargs = dict(model=model_name, messages=messages, **accepted)
    if response_format is not None:
        kwargs["response_format"] = response_format

    response = call_with_retry(completion, **kwargs)

    return response.choices[0].message.content
