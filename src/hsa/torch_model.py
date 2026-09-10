"""Small policy/value network built from Ascend-friendly PyTorch operators."""

from __future__ import annotations

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


class TorchPolicyValueModel:
    """Inference adapter implementing the framework-neutral model protocol."""

    name = "torch-policy-value-mlp-v1"

    def __init__(self, model: PolicyValueNet, device: torch.device):
        self.model = model.to(device).eval()
        self.device = device

    @classmethod
    def from_checkpoint(
        cls, path: str, device: str | torch.device = "cpu"
    ) -> "TorchPolicyValueModel":
        if str(device).startswith("npu"):
            import torch_npu  # noqa: F401
        device = torch.device(device)
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        metadata = checkpoint["report"]["model"]
        model = PolicyValueNet(
            int(metadata["state_size"]), int(metadata["action_size"]),
            int(metadata["hidden_size"]), int(metadata["action_hidden_size"]),
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        return cls(model, device)

    def predict(self, game, actions) -> PolicyValueOutput:
        if not actions:
            return PolicyValueOutput((), 0.0)
        states = torch.tensor(
            [encode_state(game, game.current)],
            dtype=torch.float32, device=self.device,
        )
        action_tensor = torch.tensor(
            [[encode_action(game, action) for action in actions]],
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
