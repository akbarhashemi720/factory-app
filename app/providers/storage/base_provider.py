"""
Base Provider Interface — AI Factory Foundation

Every external capability (Storage, Agent, Deploy, Bot, CRM, Payment...)
is a provider behind this interface. The factory decides which provider
to use. The customer never manages providers directly.

This is the first foundational layer of the Build → Connect → Operate → Manage vision.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Common interface for all factory providers.

    Future providers inherit from this:
      StorageProvider, AgentProvider, BotProvider,
      DeploymentProvider, PaymentProvider, SecretProvider, ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    def version(self) -> str:
        return "1.0"

    def health_check(self) -> dict[str, Any]:
        """Return provider health status. Override for real checks."""
        return {"provider": self.name, "status": "ok", "version": self.version}
