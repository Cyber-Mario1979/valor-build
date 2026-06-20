"""LLM interface — D-08 LOCKED (A16 §4).

The AI call shape is **locked**; only model selection is open (O1). This module
implements the locked interface, with a deterministic stub standing in for the model
(temperature 0 == deterministic for the walking skeleton):

  * **Prompt = versioned, hashed asset** — never an inline string; the version id and
    content hash are logged on every call.
  * **Schema-constrained JSON only** — the model's output is validated against the
    relevant draft-07 result schema *before it is allowed to mean anything*. Free-form
    prose out is a refusal.
  * **Refuse/accept loop** — on a schema-invalid response, **1 silent retry**; a second
    failure **escalates to a human** (never a third silent attempt, never a coerced parse).
  * **Audit, every call** — ``prompt_version`` + ``input_hash`` + ``output_hash`` +
    accept/refuse outcome + escalation flag, on the single audit channel.

The interface is **model-agnostic by construction** (A16 §4): swapping the generator
must not change this contract. ``Generator`` is the only seam a real model plugs into.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from ..engine.audit import AuditLog, canonical_hash
from ..engine.schemas import SchemaRegistry, SchemaValidationError

MAX_SILENT_RETRIES = 1  # D-08: exactly one silent retry, then escalate.


@dataclass(frozen=True)
class PromptAsset:
    """A versioned, hashed prompt asset. Not an inline string (D-08)."""

    version: str
    template: str

    @property
    def content_hash(self) -> str:
        return canonical_hash({"version": self.version, "template": self.template})


class Generator(Protocol):
    """The model seam. Receives the rendered prompt + input + attempt index.

    Returns a candidate result object (dict). A real model plugs in here without
    changing the locked interface around it.
    """

    def __call__(self, prompt: PromptAsset, model_input: dict, attempt: int) -> dict: ...


class EscalateToHuman(RuntimeError):
    """Raised after the silent retry budget is exhausted (D-08 second failure)."""

    def __init__(self, prompt_version: str, errors: list[str]):
        self.prompt_version = prompt_version
        self.errors = errors
        super().__init__(
            f"AI call escalated to human after {MAX_SILENT_RETRIES} silent retry: {errors}"
        )


class LLMInterface:
    def __init__(self, schemas: SchemaRegistry, audit: AuditLog):
        self.schemas = schemas
        self.audit = audit

    def generate(
        self,
        prompt: PromptAsset,
        model_input: dict,
        result_schema_ref: str,
        generator: Generator,
    ) -> dict:
        """Run the locked refuse/accept loop and return a schema-valid result.

        Validates each candidate against ``result_schema_ref``. Escalates to a human
        on the second failure. Logs provenance on every attempt.
        """
        input_hash = canonical_hash(model_input)
        last_errors: list[str] = []
        # attempt 0 (initial) + up to MAX_SILENT_RETRIES silent retries.
        for attempt in range(MAX_SILENT_RETRIES + 1):
            candidate = generator(prompt, model_input, attempt)
            output_hash = canonical_hash(candidate)
            try:
                self.schemas.validate(candidate, result_schema_ref)
            except SchemaValidationError as exc:
                last_errors = exc.errors
                self.audit.emit(
                    "ai_call",
                    prompt_version=prompt.version,
                    prompt_hash=prompt.content_hash,
                    input_hash=input_hash,
                    output_hash=output_hash,
                    attempt=attempt,
                    outcome="REFUSE",
                    escalated=False,
                    errors=exc.errors,
                )
                continue
            self.audit.emit(
                "ai_call",
                prompt_version=prompt.version,
                prompt_hash=prompt.content_hash,
                input_hash=input_hash,
                output_hash=output_hash,
                attempt=attempt,
                outcome="ACCEPT",
                escalated=False,
            )
            return candidate

        # Budget exhausted -> escalate (never a coerced parse, never a third try).
        self.audit.emit(
            "ai_call",
            prompt_version=prompt.version,
            prompt_hash=prompt.content_hash,
            input_hash=input_hash,
            attempt=MAX_SILENT_RETRIES,
            outcome="ESCALATE",
            escalated=True,
            errors=last_errors,
        )
        raise EscalateToHuman(prompt.version, last_errors)
