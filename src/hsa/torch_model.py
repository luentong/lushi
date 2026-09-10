"""Small policy/value network built from Ascend-friendly PyTorch operators."""

from __future__ import annotations

import math

import torch
from torch import Tensor, nn

from .encoding import encode_action, encode_state
from .policy_value import PolicyValueOutput


class PolicyValueNet(nn.Module):
    """Score variable legal-action sets and estimate the acting player's value."""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 256,
        action_hidden_size: int = 128,
    ):
        super().__init__()
        self.state_size = state_size
        self.action_size = action_size
        self.hidden_size = hidden_size
        self.action_hidden_size = action_hidden_size
        self.state_tower = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, hidden_size),
            nn.GELU(),
        )
        self.action_tower = nn.Sequential(
            nn.Linear(action_size, action_hidden_size),
            nn.LayerNorm(action_hidden_size),
            nn.GELU(),
        )
        self.policy_state = nn.Linear(hidden_size, action_hidden_size)
        self.policy_head = nn.Sequential(
            nn.GELU(),
            nn.Linear(action_hidden_size, 1),
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, action_hidden_size),
            nn.GELU(),
            nn.Linear(action_hidden_size, 1),
            nn.Tanh(),
        )

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        if states.ndim != 2 or states.shape[-1] != self.state_size:
            raise ValueError("states must have shape [batch, state_size]")
        if actions.ndim != 3 or actions.shape[-1] != self.action_size:
            raise ValueError("actions must have shape [batch, legal, action_size]")
        state_features = self.state_tower(states)
        action_features = self.action_tower(actions)
        joint = action_features + self.policy_state(state_features).unsqueeze(1)
        logits = self.policy_head(joint).squeeze(-1)
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
        values = self.value_head(state_features).squeeze(-1)
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        return {
            "architecture": "policy-value-mlp-v1",
            "state_size": self.state_size,
            "action_size": self.action_size,
            "hidden_size": self.hidden_size,
            "action_hidden_size": self.action_hidden_size,
        }


class InteractionPolicyValueNet(PolicyValueNet):
    """Policy/value network with explicit state-action interaction features.

    The v1 additive head can only score a nonlinear transform of ``a + s``.
    Concatenating the two embeddings and their element-wise product lets the
    policy learn that the same action can be good or bad in different states.
    All operators used here are supported by the Ascend PyTorch stack.
    """

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 256,
        action_hidden_size: int = 128,
    ):
        super().__init__(
            state_size, action_size, hidden_size, action_hidden_size
        )
        self.policy_head = nn.Sequential(
            nn.Linear(action_hidden_size * 3, action_hidden_size),
            nn.GELU(),
            nn.Linear(action_hidden_size, 1),
        )

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        if states.ndim != 2 or states.shape[-1] != self.state_size:
            raise ValueError("states must have shape [batch, state_size]")
        if actions.ndim != 3 or actions.shape[-1] != self.action_size:
            raise ValueError("actions must have shape [batch, legal, action_size]")
        state_features = self.state_tower(states)
        action_features = self.action_tower(actions)
        policy_state = self.policy_state(state_features).unsqueeze(1)
        policy_state = policy_state.expand(-1, actions.shape[1], -1)
        joint = torch.cat(
            (action_features, policy_state, action_features * policy_state),
            dim=-1,
        )
        logits = self.policy_head(joint).squeeze(-1)
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
        values = self.value_head(state_features).squeeze(-1)
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        metadata = super().metadata()
        metadata["architecture"] = "policy-value-interaction-mlp-v2"
        return metadata


class BilinearPolicyValueNet(PolicyValueNet):
    """Constrained two-tower policy using state/action compatibility."""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 256,
        action_hidden_size: int = 128,
    ):
        super().__init__(
            state_size, action_size, hidden_size, action_hidden_size
        )
        self.policy_head = nn.Identity()
        self.policy_state_norm = nn.LayerNorm(action_hidden_size)
        self.policy_action_norm = nn.LayerNorm(action_hidden_size)
        self.policy_action_bias = nn.Linear(action_hidden_size, 1)

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        if states.ndim != 2 or states.shape[-1] != self.state_size:
            raise ValueError("states must have shape [batch, state_size]")
        if actions.ndim != 3 or actions.shape[-1] != self.action_size:
            raise ValueError("actions must have shape [batch, legal, action_size]")
        state_features = self.state_tower(states)
        action_features = self.action_tower(actions)
        policy_state = self.policy_state_norm(
            self.policy_state(state_features)
        ).unsqueeze(1)
        policy_actions = self.policy_action_norm(action_features)
        compatibility = (policy_actions * policy_state).sum(dim=-1)
        logits = (
            compatibility / math.sqrt(self.action_hidden_size)
            + self.policy_action_bias(action_features).squeeze(-1)
        )
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
        values = self.value_head(state_features).squeeze(-1)
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        metadata = super().metadata()
        metadata["architecture"] = "policy-value-bilinear-mlp-v3"
        return metadata


class _ResidualBlock(nn.Module):
    """Pre-normalized MLP residual block using portable PyTorch operators."""

    def __init__(self, hidden_size: int, expansion: int = 2):
        super().__init__()
        expanded_size = hidden_size * expansion
        self.norm = nn.LayerNorm(hidden_size)
        self.layers = nn.Sequential(
            nn.Linear(hidden_size, expanded_size),
            nn.GELU(),
            nn.Linear(expanded_size, hidden_size),
        )

    def forward(self, features: Tensor) -> Tensor:
        return features + self.layers(self.norm(features))


class ResidualPolicyValueNet(nn.Module):
    """Higher-capacity residual policy/value model for long-lived card pools.

    The action head models four complementary interactions: action features,
    state features, their product, and their absolute difference.  The value
    head is independent after the shared residual state encoder, so terminal
    outcomes can train a genuine state-value estimate rather than merely
    reusing policy logits.  Every operator is available in stock PyTorch and
    torch-npu; no CUDA-only attention or fused extension is required.
    """

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 512,
        action_hidden_size: int = 256,
        residual_blocks: int = 4,
    ):
        super().__init__()
        if residual_blocks < 1:
            raise ValueError("residual_blocks must be positive")
        self.state_size = state_size
        self.action_size = action_size
        self.hidden_size = hidden_size
        self.action_hidden_size = action_hidden_size
        self.residual_blocks = residual_blocks
        self.state_stem = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )
        self.state_blocks = nn.ModuleList(
            [_ResidualBlock(hidden_size) for _ in range(residual_blocks)]
        )
        self.state_final_norm = nn.LayerNorm(hidden_size)
        self.action_tower = nn.Sequential(
            nn.Linear(action_size, action_hidden_size),
            nn.LayerNorm(action_hidden_size),
            nn.GELU(),
            nn.Linear(action_hidden_size, action_hidden_size),
            nn.GELU(),
        )
        self.policy_state = nn.Linear(hidden_size, action_hidden_size)
        self.policy_head = nn.Sequential(
            nn.Linear(action_hidden_size * 4, action_hidden_size * 2),
            nn.LayerNorm(action_hidden_size * 2),
            nn.GELU(),
            nn.Linear(action_hidden_size * 2, action_hidden_size),
            nn.GELU(),
            nn.Linear(action_hidden_size, 1),
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.GELU(),
            nn.Linear(hidden_size // 4, 1),
            nn.Tanh(),
        )

    def _encode_state(self, states: Tensor) -> Tensor:
        features = self.state_stem(states)
        for block in self.state_blocks:
            features = block(features)
        return self.state_final_norm(features)

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        if states.ndim != 2 or states.shape[-1] != self.state_size:
            raise ValueError("states must have shape [batch, state_size]")
        if actions.ndim != 3 or actions.shape[-1] != self.action_size:
            raise ValueError("actions must have shape [batch, legal, action_size]")
        state_features = self._encode_state(states)
        action_features = self.action_tower(actions)
        policy_state = self.policy_state(state_features).unsqueeze(1)
        policy_state = policy_state.expand(-1, actions.shape[1], -1)
        joint = torch.cat(
            (
                action_features,
                policy_state,
                action_features * policy_state,
                torch.abs(action_features - policy_state),
            ),
            dim=-1,
        )
        logits = self.policy_head(joint).squeeze(-1)
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
        values = self.value_head(state_features).squeeze(-1)
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        return {
            "architecture": "policy-value-residual-mlp-v4",
            "state_size": self.state_size,
            "action_size": self.action_size,
            "hidden_size": self.hidden_size,
            "action_hidden_size": self.action_hidden_size,
            "residual_blocks": self.residual_blocks,
        }


class TorchPolicyValueModel:
    """Inference adapter implementing the framework-neutral model protocol."""

    name = "torch-policy-value-mlp-v1"

    def __init__(
        self, model: PolicyValueNet, device: torch.device,
        *, value_trained: bool = True, state_schema_version: int = 1,
    ):
        self.model = model.to(device).eval()
        self.name = str(model.metadata()["architecture"])
        self.device = device
        self.value_trained = value_trained
        self.state_schema_version = state_schema_version

    @classmethod
    def from_checkpoint(
        cls, path: str, device: str | torch.device = "cpu"
    ) -> "TorchPolicyValueModel":
        if str(device).startswith("npu"):
            import torch_npu  # noqa: F401
        device = torch.device(device)
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        metadata = checkpoint["report"]["model"]
        architecture = metadata.get("architecture", "policy-value-mlp-v1")
        model_class = {
            "policy-value-mlp-v1": PolicyValueNet,
            "policy-value-interaction-mlp-v2": InteractionPolicyValueNet,
            "policy-value-bilinear-mlp-v3": BilinearPolicyValueNet,
            "policy-value-residual-mlp-v4": ResidualPolicyValueNet,
        }.get(architecture)
        if model_class is None:
            raise ValueError(f"unsupported model architecture: {architecture}")
        model_args = [
            int(metadata["state_size"]), int(metadata["action_size"]),
            int(metadata["hidden_size"]), int(metadata["action_hidden_size"]),
        ]
        if model_class is ResidualPolicyValueNet:
            model_args.append(int(metadata.get("residual_blocks", 4)))
        model = model_class(*model_args)
        model.load_state_dict(checkpoint["model_state_dict"])
        return cls(
            model, device,
            value_trained=bool(checkpoint["report"].get("value_trained", True)),
            state_schema_version=int(
                checkpoint["report"].get("feature_schema", {}).get(
                    "schema_version", 1
                )
            ),
        )

    def predict(self, game, actions) -> PolicyValueOutput:
        if not actions:
            return PolicyValueOutput((), 0.0)
        states = torch.tensor(
            [encode_state(
                game, game.current,
                schema_version=self.state_schema_version,
            )],
            dtype=torch.float32, device=self.device,
        )
        action_tensor = torch.tensor(
            [[
                encode_action(
                    game, action,
                    schema_version=self.state_schema_version,
                )
                for action in actions
            ]],
            dtype=torch.float32, device=self.device,
        )
        mask = torch.ones(
            (1, len(actions)), dtype=torch.bool, device=self.device
        )
        with torch.no_grad():
            logits, values = self.model(states, action_tensor, mask)
            priors = torch.softmax(logits[0], dim=0).cpu().tolist()
            value = float(values[0].cpu().item())
        return PolicyValueOutput(tuple(priors), value)
