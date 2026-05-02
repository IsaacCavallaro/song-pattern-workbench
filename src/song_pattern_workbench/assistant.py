from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from song_pattern_workbench.models import AskRun, SearchRun
from song_pattern_workbench.search import run_search


class FixtureAssistantClient:
    def __init__(self, path: str) -> None:
        self.payload = json.loads(Path(path).read_text())

    def answer(self, question: str, search_run: SearchRun) -> tuple[str, dict[str, object]]:
        entry = self.payload.get(search_run.normalized_pattern) or self.payload.get(question)
        if not isinstance(entry, dict):
            raise KeyError(
                f"No fixture assistant response found for pattern {search_run.normalized_pattern!r}"
            )
        answer = entry.get("answer")
        if not isinstance(answer, str):
            raise ValueError("Fixture assistant entries require a string answer")
        return answer, {"fixture_key": search_run.normalized_pattern}


class OpenAICompatibleAssistantClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key_env: str,
        system_prompt: str,
        temperature: float = 0.2,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    def answer(self, question: str, search_run: SearchRun) -> tuple[str, dict[str, object]]:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key in environment variable {self.api_key_env}")
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": _build_grounded_prompt(question, search_run),
                },
            ],
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Assistant request failed: {exc.code} {message}") from exc
        parsed = json.loads(body)
        answer = parsed["choices"][0]["message"]["content"]
        return answer, {"response": parsed}


def run_ask(
    config: dict[str, object],
    *,
    pattern: str,
    question: str,
    limit: int | None = None,
    offset: int = 0,
) -> AskRun:
    assistant_config = config.get("assistant")
    if not isinstance(assistant_config, dict):
        raise ValueError("Config must contain an assistant object for ask runs.")
    search_run = run_search(config, pattern=pattern, limit=limit, offset=offset)
    client = build_assistant_client(assistant_config)
    answer, raw = client.answer(question, search_run)
    provider_name = str(assistant_config.get("type", "unknown"))
    return AskRun(
        question=question,
        search_run=search_run,
        answer=answer,
        provider_name=provider_name,
        raw=raw,
    )


def build_assistant_client(
    config: dict[str, object],
) -> FixtureAssistantClient | OpenAICompatibleAssistantClient:
    provider_type = config.get("type")
    if provider_type == "fixture":
        path = config.get("path")
        if not isinstance(path, str):
            raise ValueError("fixture assistant requires string path")
        return FixtureAssistantClient(path)
    if provider_type == "openai_compatible":
        base_url = config.get("base_url")
        model = config.get("model")
        api_key_env = config.get("api_key_env")
        system_prompt = config.get(
            "system_prompt",
            (
                "You are a music-pattern assistant. Answer using only the retrieved matches and "
                "their metadata. If the retrieved context is insufficient, say so plainly."
            ),
        )
        temperature = config.get("temperature", 0.2)
        timeout_seconds = config.get("timeout_seconds", 60.0)
        if not all(isinstance(value, str) for value in (base_url, model, api_key_env, system_prompt)):
            raise ValueError(
                "openai_compatible assistant requires string base_url, model, api_key_env, and system_prompt"
            )
        return OpenAICompatibleAssistantClient(
            base_url=base_url,
            model=model,
            api_key_env=api_key_env,
            system_prompt=system_prompt,
            temperature=float(temperature),
            timeout_seconds=float(timeout_seconds),
        )
    raise ValueError(f"Unsupported assistant type: {provider_type!r}")


def _build_grounded_prompt(question: str, search_run: SearchRun) -> str:
    lines = [
        f"Question: {question}",
        f"Pattern query: {search_run.pattern}",
        f"Normalized pattern: {search_run.normalized_pattern}",
        f"Returned matches: {len(search_run.results)}",
        f"Total available: {search_run.total_available}",
        "",
        "Retrieved matches:",
    ]
    for index, hit in enumerate(search_run.results, start=1):
        metadata = ", ".join(f"{key}={value}" for key, value in hit.metadata.items())
        line = f"{index}. {hit.title} | {hit.artist}"
        if hit.section:
            line += f" | section={hit.section}"
        if metadata:
            line += f" | {metadata}"
        lines.append(line)
    lines.append("")
    lines.append("Answer using only the retrieved matches above.")
    return "\n".join(lines)
