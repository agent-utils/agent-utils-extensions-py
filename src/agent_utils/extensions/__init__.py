# SPDX-License-Identifier: MIT
"""Thin MCP-over-HTTP client for the hosted agent_utils Extensions server.

Extensions is the stateless half of agent_utils: exact math and unit
conversion (general, electrical, chemistry, thermodynamics), all on one endpoint.

This is a client, not the service - see https://agent-utils.ai.
Zero dependencies: standard library only.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_ENDPOINT = "https://mcp.agent-utils.ai/extensions"
STAGING_ENDPOINT = "https://mcp-staging.agent-utils.ai/extensions"
USER_AGENT = "agent-utils-extensions-py/0.1.0"

__all__ = ["AgentUtilsExtensions", "DEFAULT_ENDPOINT", "STAGING_ENDPOINT"]


class AgentUtilsExtensions:
    """Client for the agent_utils Extensions MCP server.

    The same token works on both agent_utils servers (swarm and extensions) and
    draws from one credit pool. Any secret works as a token - the first call
    auto-provisions a free trial. See https://agent-utils.ai.
    """

    def __init__(self, token: str, endpoint: str = DEFAULT_ENDPOINT) -> None:
        self._token = token
        self._endpoint = endpoint
        self._id = 0

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call any MCP tool by name and return its result."""
        self._id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                              "params": {"name": name, "arguments": arguments or {}}}).encode()
        req = urllib.request.Request(self._endpoint, data=payload, method="POST",
                                     headers={"Authorization": f"Bearer {self._token}",
                                              "Content-Type": "application/json",
                                              # Cloudflare rejects urllib's default User-Agent (error 1010).
                                              "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read())
        except urllib.error.HTTPError as exc:  # pragma: no cover
            raise RuntimeError(f"agent_utils HTTP {exc.code}: {exc.read().decode()}") from exc
        if isinstance(body, dict) and body.get("error"):
            raise RuntimeError(f"agent_utils: {body['error'].get('message', 'unknown error')}")
        return body.get("result") if isinstance(body, dict) else body

    def eval_expr(self, **kwargs: Any) -> Any:
        return self.call("eval_expr", kwargs)

    def convert(self, quantity: str, from_unit: str, to_unit: str, amount: float) -> Any:
        """Convert `amount` between units of `quantity` (e.g. "length", "electric_potential")."""
        return self.call("convert_" + quantity, {"from": from_unit, "to": to_unit, "amount": amount})

    # --- account (also on swarm) ---------------------------------------------

    def get_account(self) -> Any:
        return self.call("get_account", {})

    def list_api_keys(self, **kwargs: Any) -> Any:
        return self.call("list_api_keys", kwargs)

    def create_api_key(self, **kwargs: Any) -> Any:
        return self.call("create_api_key", kwargs)

    def revoke_api_key(self, **kwargs: Any) -> Any:
        return self.call("revoke_api_key", kwargs)

    def list_payments(self, **kwargs: Any) -> Any:
        return self.call("list_payments", kwargs)

    def settle_balance(self, **kwargs: Any) -> Any:
        return self.call("settle_balance", kwargs)

    def submit_feature_request(self, **kwargs: Any) -> Any:
        return self.call("submit_feature_request", kwargs)

    def submit_exit_feedback(self, **kwargs: Any) -> Any:
        return self.call("submit_exit_feedback", kwargs)

    def delete_account(self, **kwargs: Any) -> Any:
        return self.call("delete_account", kwargs)
