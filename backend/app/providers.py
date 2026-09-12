from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable, Optional

from .security import redact_value

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[Any]]


def configured_provider(provider_override: Optional[str] = None) -> str:
    chosen = provider_override or os.getenv("LLM_PROVIDER", "openai")
    chosen = chosen.lower()
    if chosen not in {"openai", "openrouter", "deterministic"}:
        return os.getenv("LLM_PROVIDER", "openai").lower()
    return chosen


def llm_available(provider_override: Optional[str] = None) -> bool:
    provider = configured_provider(provider_override)
    if provider == "deterministic":
        return False
    if OpenAI is None:
        return False
    if provider == "openrouter":
        return bool(os.getenv("OPENROUTER_API_KEY"))
    return bool(os.getenv("OPENAI_API_KEY"))


def effective_provider(provider_override: Optional[str] = None) -> str:
    provider = configured_provider(provider_override)
    if provider == "deterministic":
        return provider
    if llm_available(provider):
        return provider
    return "deterministic"


def provider_summary() -> dict[str, Any]:
    current = configured_provider()
    return {
        "active_provider": current,
        "providers": {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
            },
            "openrouter": {
                "configured": bool(os.getenv("OPENROUTER_API_KEY")),
                "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6"),
                "base_url": "https://openrouter.ai/api/v1",
            },
            "deterministic": {
                "configured": True,
                "model": "deterministic-rules",
            },
        },
    }


def _client_and_model(provider_override: Optional[str] = None) -> tuple[Any, str]:
    """Create the OpenAI-compatible client used by standard and tool calls."""
    provider = configured_provider(provider_override)
    if provider == "openrouter":
        return (
            OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", os.getenv("APP_BASE_URL", "http://localhost:3000")),
                    "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "TrueSource"),
                },
            ),
            os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6"),
        )
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY")), os.getenv("OPENAI_MODEL", "gpt-5.6")


def run_json_prompt(system_prompt: str, payload: dict[str, Any], response_keys: list[str], provider_override: Optional[str] = None) -> dict[str, Any] | None:
    if not llm_available(provider_override) or OpenAI is None:
        return None

    client, model = _client_and_model(provider_override)

    prompt = (
        f"{system_prompt}\n"
        f"Return JSON with keys: {', '.join(response_keys)}.\n"
        "Do not invent facts beyond the payload.\n"
        f"Payload: {json.dumps(redact_value(payload), indent=2)}"
    )
    response = client.responses.create(model=model, input=prompt)
    try:
        return json.loads(response.output_text)
    except Exception:
        return None


async def run_tool_agent(
    system_prompt: str,
    question: str,
    tools: list[dict[str, Any]],
    execute_tool: ToolExecutor,
    provider_override: Optional[str] = None,
    max_tool_rounds: int = 3,
) -> str | None:
    """Run a bounded OpenRouter/OpenAI function-calling loop.

    The model can request a tool but never executes it itself.  The caller owns
    execution (here, through the MCP client) and this function returns each
    redacted result to the model as a ``tool`` message.
    """
    if not llm_available(provider_override) or OpenAI is None or not tools:
        return None

    client, model = _client_and_model(provider_override)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    for tool_round in range(max_tool_rounds + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False,
            )
        except Exception:
            return None

        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        if not tool_calls:
            return message.content.strip() if message.content else None

        # Do not permit an unbounded model → tool cycle.
        if tool_round >= max_tool_rounds:
            return message.content.strip() if message.content else None

        messages.append(message.model_dump(exclude_none=True))
        for tool_call in tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                tool_result = await execute_tool(tool_call.function.name, arguments)
            except (json.JSONDecodeError, ValueError) as exc:
                tool_result = {"error": f"Invalid tool arguments: {exc}"}
            except Exception:
                # Tool diagnostics can contain internal endpoint details; keep
                # them out of the model context while allowing it to recover.
                tool_result = {"error": "The requested TrueSource tool was unavailable."}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(redact_value(tool_result)),
                }
            )

    return None
