"""Small policy/value network built from Ascend-friendly PyTorch operators."""

from __future__ import annotations

import math
import sys
import types

import torch
from torch import Tensor, nn

from .encoding import (
    CARD_SEMANTIC_FEATURE_SIZE, compatible_feature_schema,
    configure_card_vocab, encode_action, encode_state, feature_schema,
)
from .policy_value import PolicyValueOutput


def _install_torch_npu_checkpoint_compat() -> None:
    """Install a narrow pickle shim for trusted NPU-formatted checkpoints.

    Ascend saves ordinary CPU storages with an NPU format annotation. CUDA
    hosts do not have ``torch_npu``, so retain the tensor storage while
    discarding only that device-specific annotation.
    """
    torch_npu = types.ModuleType("torch_npu")
    utils = types.ModuleType("torch_npu.utils")
    storage = types.ModuleType("torch_npu.utils.storage")
    npu = types.ModuleType("torch_npu.npu")
    format_module = types.ModuleType("torch_npu.npu._format")

    class Format:
        def __init__(self, code: int):
            self.code = code

    def rebuild_npu_tensor(
        tensor_storage, storage_offset, size, stride, requires_grad,
        backward_hooks, _format,
    ):
        return torch._utils._rebuild_tensor_v2(
            tensor_storage, storage_offset, size, stride, requires_grad,
            backward_hooks,
        )

    storage._rebuild_npu_tensor = rebuild_npu_tensor
    format_module.Format = Format
    torch_npu.utils = utils
    torch_npu.npu = npu
    utils.storage = storage
    npu._format = format_module
    sys.modules.update({
        "torch_npu": torch_npu,
        "torch_npu.utils": utils,
        "torch_npu.utils.storage": storage,
        "torch_npu.npu": npu,
        "torch_npu.npu._format": format_module,
    })


def load_checkpoint(path: str) -> dict:
    """Load a trusted checkpoint on its native device or a CUDA-only host."""
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except ModuleNotFoundError as error:
        if error.name != "torch_npu":
            raise
    _install_torch_npu_checkpoint_compat()
    return torch.load(path, map_location="cpu", weights_only=False)


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


class StructuredResidualPolicyValueNet(nn.Module):
    """Card-embedding residual model that scales beyond a closed deck slice.

    Schema-v4/v5 state histograms and action card identities share one learned
    embedding table (implemented as a bias-free Linear for dense one-hot NPU
    inputs). Schema v5 adds the actor's remaining-deck histogram and current
    turn damage progress, while v4 checkpoints retain their original layout.
    """

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 512,
        action_hidden_size: int = 256,
        residual_blocks: int = 4,
        card_vocab_size: int = 281,
        card_embedding_size: int = 128,
    ):
        super().__init__()
        if residual_blocks < 1:
            raise ValueError("residual_blocks must be positive")
        v4_state_size = 374 + 3 * card_vocab_size
        v5_state_size = 376 + 4 * card_vocab_size
        v6_semantic_width = state_size - v5_state_size
        if state_size == v4_state_size:
            self.state_schema_version = 4
            histogram_count = 3
            dynamic_state_size = 350
            semantic_state_size = 0
        elif state_size == v5_state_size:
            self.state_schema_version = 5
            histogram_count = 4
            dynamic_state_size = 352
            semantic_state_size = 0
        elif v6_semantic_width > 0 and v6_semantic_width % 4 == 0:
            self.state_schema_version = 6
            histogram_count = 4
            dynamic_state_size = 352
            semantic_state_size = v6_semantic_width
            self.card_semantic_feature_size = v6_semantic_width // 4
        else:
            raise ValueError("structured model requires state schema v4, v5, or v6")
        if self.state_schema_version < 6:
            self.card_semantic_feature_size = 0
        expected_action_size = 56 + 2 * card_vocab_size
        if self.state_schema_version >= 6:
            expected_action_size += 2 * self.card_semantic_feature_size
        if action_size != expected_action_size:
            raise ValueError("structured model action width does not match state schema")
        self.state_size = state_size
        self.action_size = action_size
        self.hidden_size = hidden_size
        self.action_hidden_size = action_hidden_size
        self.residual_blocks = residual_blocks
        self.card_vocab_size = card_vocab_size
        self.card_embedding_size = card_embedding_size
        self.state_histogram_count = histogram_count
        self.dynamic_state_size = dynamic_state_size
        self.semantic_state_size = semantic_state_size
        self.card_embedding = nn.Linear(
            card_vocab_size, card_embedding_size, bias=False
        )
        if semantic_state_size:
            self.semantic_state_projection = nn.Sequential(
                nn.Linear(semantic_state_size, card_embedding_size),
                nn.LayerNorm(card_embedding_size),
                nn.GELU(),
            )
        else:
            self.semantic_state_projection = None
        self.state_stem = nn.Sequential(
            nn.Linear(
                24 + histogram_count * card_embedding_size + dynamic_state_size
                + (card_embedding_size if semantic_state_size else 0),
                hidden_size,
            ),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )
        self.state_blocks = nn.ModuleList(
            [_ResidualBlock(hidden_size) for _ in range(residual_blocks)]
        )
        self.state_final_norm = nn.LayerNorm(hidden_size)
        self.action_tower = nn.Sequential(
            nn.Linear(
                56 + 2 * card_embedding_size
                + (2 * self.card_semantic_feature_size if self.state_schema_version >= 6 else 0),
                action_hidden_size,
            ),
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

        self.action_value_head = nn.Sequential(
            nn.Linear(action_hidden_size * 4, action_hidden_size),
            nn.LayerNorm(action_hidden_size),
            nn.GELU(),
            nn.Linear(action_hidden_size, 1),
            nn.Tanh(),
        )

    def _encode_state(self, states: Tensor) -> Tensor:
        vocab = self.card_vocab_size
        global_features = states[:, :24]
        histogram_start = 24
        histograms = [
            states[:, histogram_start + role * vocab:
                   histogram_start + (role + 1) * vocab]
            for role in range(self.state_histogram_count)
        ]
        dynamic_features = states[
            :, histogram_start + self.state_histogram_count * vocab:
               histogram_start + self.state_histogram_count * vocab + self.dynamic_state_size
        ]
        embedded_cards = [self.card_embedding(items) for items in histograms]
        parts = [global_features, *embedded_cards, dynamic_features]
        if self.semantic_state_size:
            semantic_features = states[:, -self.semantic_state_size:]
            parts.append(self.semantic_state_projection(semantic_features))
        features = self.state_stem(torch.cat(parts, dim=-1))
        for block in self.state_blocks:
            features = block(features)
        return self.state_final_norm(features)

    def _encode_actions(self, actions: Tensor) -> Tensor:
        vocab = self.card_vocab_size
        source_prefix = actions[..., :23]
        source_card = actions[..., 23:23 + vocab]
        source_position_start = 23 + vocab
        source_position = actions[
            ..., source_position_start:source_position_start + 10
        ]
        target_prefix_start = source_position_start + 10
        target_prefix = actions[
            ..., target_prefix_start:target_prefix_start + 12
        ]
        target_card_start = target_prefix_start + 12
        target_card = actions[
            ..., target_card_start:target_card_start + vocab
        ]
        target_tail = actions[..., target_card_start + vocab:]
        return self.action_tower(torch.cat((
            source_prefix,
            self.card_embedding(source_card),
            source_position,
            target_prefix,
            self.card_embedding(target_card),
            target_tail,
        ), dim=-1))

    def forward_with_action_values(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor]:
        if states.ndim != 2 or states.shape[-1] != self.state_size:
            raise ValueError("states must have shape [batch, state_size]")
        if actions.ndim != 3 or actions.shape[-1] != self.action_size:
            raise ValueError("actions must have shape [batch, legal, action_size]")
        state_features = self._encode_state(states)
        action_features = self._encode_actions(actions)
        policy_state = self.policy_state(state_features).unsqueeze(1)
        policy_state = policy_state.expand(-1, actions.shape[1], -1)
        joint = torch.cat((
            action_features, policy_state, action_features * policy_state,
            torch.abs(action_features - policy_state),
        ), dim=-1)
        logits = self.policy_head(joint).squeeze(-1)
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
        action_values = self.action_value_head(joint).squeeze(-1)
        if action_mask is not None:
            action_values = action_values.masked_fill(~action_mask, 0.0)
        return logits, self.value_head(state_features).squeeze(-1), action_values

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        logits, values, _action_values = self.forward_with_action_values(
            states, actions, action_mask
        )
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        return {
            "architecture": (
                "policy-value-structured-residual-v6-semantic-action-q-v1"
                if self.state_schema_version >= 6
                else "policy-value-structured-residual-v5-action-q-v1"
            ),
            "state_size": self.state_size,
            "action_size": self.action_size,
            "hidden_size": self.hidden_size,
            "action_hidden_size": self.action_hidden_size,
            "residual_blocks": self.residual_blocks,
            "card_vocab_size": self.card_vocab_size,
            "card_embedding_size": self.card_embedding_size,
            "card_semantic_feature_size": self.card_semantic_feature_size,
        }


class _PortableEntityAttentionBlock(nn.Module):
    """Transformer block expressed with portable primitive operators.

    PyTorch's stock TransformerEncoderLayer may select the fused
    ``aten::_transformer_encoder_layer_fwd`` fast path.  torch-npu currently
    sends that operator back to the CPU, making the entire JEV encoder the
    training bottleneck.  Explicit Q/K/V projections, batched matmuls,
    softmax, LayerNorm and GELU stay on Ascend while preserving full
    self-attention over the fixed entity sequence.
    """

    def __init__(self, hidden_size: int, heads: int):
        super().__init__()
        if heads < 1 or hidden_size % heads:
            raise ValueError("hidden size must be divisible by attention heads")
        self.hidden_size = hidden_size
        self.heads = heads
        self.head_size = hidden_size // heads
        self.scale = self.head_size ** -0.5
        self.qkv = nn.Linear(hidden_size, hidden_size * 3)
        self.attention_output = nn.Linear(hidden_size, hidden_size)
        self.attention_norm = nn.LayerNorm(hidden_size)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.GELU(),
            nn.Linear(hidden_size * 4, hidden_size),
        )
        self.feed_forward_norm = nn.LayerNorm(hidden_size)

    def forward(self, tokens: Tensor) -> Tensor:
        batch, token_count, _ = tokens.shape
        qkv = self.qkv(tokens).reshape(
            batch, token_count, 3, self.heads, self.head_size
        ).permute(2, 0, 3, 1, 4)
        query, key, value = qkv.unbind(0)
        scores = torch.matmul(query, key.transpose(-2, -1)) * self.scale
        weights = torch.softmax(scores, dim=-1)
        attended = torch.matmul(weights, value).transpose(1, 2).reshape(
            batch, token_count, self.hidden_size
        )
        tokens = self.attention_norm(
            tokens + self.attention_output(attended)
        )
        return self.feed_forward_norm(tokens + self.feed_forward(tokens))


class JointEntityPolicyValueNet(nn.Module):
    """Static-shape joint-entity encoder for schema-v6/v7 states.

    The existing schema already separates heroes, four card zones, hand
    slots, board slots, and location slots.  This model promotes those groups
    to 45 entity tokens and lets a small Transformer learn their interactions
    before the policy/value/action-Q heads.  Keeping the token count fixed is
    deliberate: it avoids dynamic-shape recompilation on Ascend NPUs.

    Schema v7 attaches an identity embedding and shared effect-semantic lookup
    to every hand, board, location, weapon and Hero Power entity.
    """

    V6_ENTITY_COUNT = 45
    V7_ENTITY_COUNT = 49

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 512,
        action_hidden_size: int = 256,
        entity_layers: int = 2,
        entity_heads: int = 8,
        card_vocab_size: int = 281,
        card_embedding_size: int = 128,
        entity_card_slot_count: int = 0,
        entity_card_semantic_lookup: Tensor | list[list[float]] | None = None,
    ):
        super().__init__()
        if entity_layers < 1:
            raise ValueError("entity_layers must be positive")
        if entity_heads < 1 or hidden_size % entity_heads:
            raise ValueError("hidden_size must be divisible by entity_heads")
        v5_state_size = 376 + 4 * card_vocab_size
        semantic_width = state_size - v5_state_size - entity_card_slot_count
        if semantic_width <= 0 or semantic_width % 4:
            raise ValueError("JEV requires schema-v6 semantic state features")
        semantic_size = semantic_width // 4
        expected_action_size = 56 + 2 * card_vocab_size + 2 * semantic_size
        if action_size != expected_action_size:
            raise ValueError("JEV action width does not match schema-v6 state")

        self.state_size = state_size
        self.action_size = action_size
        self.hidden_size = hidden_size
        self.action_hidden_size = action_hidden_size
        self.entity_layers = entity_layers
        self.entity_heads = entity_heads
        self.card_vocab_size = card_vocab_size
        self.card_embedding_size = card_embedding_size
        self.card_semantic_feature_size = semantic_size
        self.entity_card_slot_count = entity_card_slot_count
        if entity_card_slot_count not in (0, 42):
            raise ValueError("JEV entity card slot count must be 0 or 42")
        self.entity_count = (
            self.V7_ENTITY_COUNT if entity_card_slot_count else self.V6_ENTITY_COUNT
        )

        self.card_embedding = nn.Linear(
            card_vocab_size, card_embedding_size, bias=False
        )
        self.global_projection = nn.Sequential(
            nn.Linear(26, hidden_size), nn.LayerNorm(hidden_size), nn.GELU(),
        )
        self.hero_projection = nn.Linear(8, hidden_size)
        self.zone_projection = nn.Sequential(
            nn.Linear(card_embedding_size + semantic_size, hidden_size),
            nn.LayerNorm(hidden_size), nn.GELU(),
        )
        self.hand_projection = nn.Linear(4, hidden_size)
        self.board_projection = nn.Linear(19, hidden_size)
        self.location_projection = nn.Linear(2, hidden_size)
        self.entity_type_embedding = nn.Embedding(8, hidden_size)
        self.entity_position_embedding = nn.Parameter(
            torch.zeros(1, self.entity_count, hidden_size)
        )
        entity_types = (
            [0] + [1] * 2 + [2] * 4 + [3] * 10 + [4] * 14 + [5] * 14
        )
        if entity_card_slot_count:
            entity_types += [6] * 2 + [7] * 2
        self.register_buffer(
            "entity_types", torch.tensor(entity_types, dtype=torch.long),
            persistent=False,
        )
        if entity_card_slot_count:
            if entity_card_semantic_lookup is None:
                raise ValueError("schema-v7 JEV requires entity semantic lookup")
            lookup = torch.as_tensor(
                entity_card_semantic_lookup, dtype=torch.float32
            )
            if lookup.shape != (card_vocab_size + 2, semantic_size):
                raise ValueError("entity semantic lookup shape does not match schema")
            self.register_buffer("entity_card_semantic_lookup", lookup)
            self.entity_card_embedding = nn.Embedding(
                card_vocab_size + 2, card_embedding_size
            )
            self.entity_semantic_projection = nn.Linear(
                semantic_size, card_embedding_size, bias=False
            )
            self.entity_card_projection = nn.Sequential(
                nn.Linear(card_embedding_size, hidden_size),
                nn.LayerNorm(hidden_size), nn.GELU(),
            )
        self.entity_encoder = nn.ModuleList(
            _PortableEntityAttentionBlock(hidden_size, entity_heads)
            for _ in range(entity_layers)
        )
        self.entity_final_norm = nn.LayerNorm(hidden_size)

        self.action_tower = nn.Sequential(
            nn.Linear(
                56 + 2 * card_embedding_size + 2 * semantic_size,
                action_hidden_size,
            ),
            nn.LayerNorm(action_hidden_size), nn.GELU(),
            nn.Linear(action_hidden_size, action_hidden_size), nn.GELU(),
        )
        self.policy_state = nn.Linear(hidden_size, action_hidden_size)
        joint_size = action_hidden_size * 4
        self.policy_head = nn.Sequential(
            nn.Linear(joint_size, action_hidden_size * 2),
            nn.LayerNorm(action_hidden_size * 2), nn.GELU(),
            nn.Linear(action_hidden_size * 2, action_hidden_size), nn.GELU(),
            nn.Linear(action_hidden_size, 1),
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LayerNorm(hidden_size // 2), nn.GELU(),
            nn.Linear(hidden_size // 2, hidden_size // 4), nn.GELU(),
            nn.Linear(hidden_size // 4, 1), nn.Tanh(),
        )
        self.action_value_head = nn.Sequential(
            nn.Linear(joint_size, action_hidden_size),
            nn.LayerNorm(action_hidden_size), nn.GELU(),
            nn.Linear(action_hidden_size, 1), nn.Tanh(),
        )

    def _encode_state(self, states: Tensor) -> Tensor:
        vocab = self.card_vocab_size
        semantic = self.card_semantic_feature_size
        histogram_start = 24
        histograms = states[
            :, histogram_start:histogram_start + 4 * vocab
        ].reshape(states.shape[0], 4, vocab)
        dynamic_start = histogram_start + 4 * vocab
        dynamic = states[:, dynamic_start:dynamic_start + 352]
        semantic_start = dynamic_start + 352
        semantics = states[:, semantic_start:semantic_start + 4 * semantic].reshape(
            states.shape[0], 4, semantic
        )

        global_token = self.global_projection(torch.cat((
            states[:, :24], dynamic[:, 350:352],
        ), dim=-1)).unsqueeze(1)
        hero_tokens = self.hero_projection(
            dynamic[:, :16].reshape(states.shape[0], 2, 8)
        )
        zone_tokens = self.zone_projection(torch.cat((
            self.card_embedding(histograms), semantics,
        ), dim=-1))
        hand_tokens = self.hand_projection(
            dynamic[:, 16:56].reshape(states.shape[0], 10, 4)
        )
        board_tokens = self.board_projection(
            dynamic[:, 56:322].reshape(states.shape[0], 14, 19)
        )
        location_tokens = self.location_projection(
            dynamic[:, 322:350].reshape(states.shape[0], 14, 2)
        )
        extra_tokens = []
        if self.entity_card_slot_count:
            identity_start = semantic_start + 4 * semantic
            identities = states[
                :, identity_start:identity_start + self.entity_card_slot_count
            ].long().clamp_(0, self.card_vocab_size + 1)
            card_features = self.entity_card_embedding(identities)
            card_features = card_features + self.entity_semantic_projection(
                self.entity_card_semantic_lookup[identities]
            )
            card_features = self.entity_card_projection(card_features)
            hand_tokens = hand_tokens + card_features[:, :10]
            board_tokens = board_tokens + card_features[:, 10:24]
            location_tokens = location_tokens + card_features[:, 24:38]
            extra_tokens = [card_features[:, 38:40], card_features[:, 40:42]]
        tokens = torch.cat((
            global_token, hero_tokens, zone_tokens, hand_tokens,
            board_tokens, location_tokens, *extra_tokens,
        ), dim=1)
        tokens = (
            tokens
            + self.entity_type_embedding(self.entity_types).unsqueeze(0)
            + self.entity_position_embedding
        )
        encoded = tokens
        for block in self.entity_encoder:
            encoded = block(encoded)
        return self.entity_final_norm(encoded[:, 0])

    def _encode_actions(self, actions: Tensor) -> Tensor:
        vocab = self.card_vocab_size
        source_prefix = actions[..., :23]
        source_card = actions[..., 23:23 + vocab]
        source_position_start = 23 + vocab
        source_position = actions[
            ..., source_position_start:source_position_start + 10
        ]
        target_prefix_start = source_position_start + 10
        target_prefix = actions[
            ..., target_prefix_start:target_prefix_start + 12
        ]
        target_card_start = target_prefix_start + 12
        target_card = actions[
            ..., target_card_start:target_card_start + vocab
        ]
        target_tail = actions[..., target_card_start + vocab:]
        return self.action_tower(torch.cat((
            source_prefix, self.card_embedding(source_card), source_position,
            target_prefix, self.card_embedding(target_card), target_tail,
        ), dim=-1))

    def forward_with_action_values(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor]:
        state_features = self._encode_state(states)
        action_features = self._encode_actions(actions)
        policy_state = self.policy_state(state_features).unsqueeze(1)
        policy_state = policy_state.expand(-1, actions.shape[1], -1)
        joint = torch.cat((
            action_features, policy_state, action_features * policy_state,
            torch.abs(action_features - policy_state),
        ), dim=-1)
        logits = self.policy_head(joint).squeeze(-1)
        action_values = self.action_value_head(joint).squeeze(-1)
        if action_mask is not None:
            logits = logits.masked_fill(~action_mask, -1.0e4)
            action_values = action_values.masked_fill(~action_mask, 0.0)
        values = self.value_head(state_features).squeeze(-1)
        return logits, values, action_values

    def forward(
        self,
        states: Tensor,
        actions: Tensor,
        action_mask: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        logits, values, _ = self.forward_with_action_values(
            states, actions, action_mask
        )
        return logits, values

    def metadata(self) -> dict[str, int | str]:
        return {
            "architecture": (
                "policy-value-jev-v7-action-q-v1"
                if self.entity_card_slot_count
                else "policy-value-jev-v6-action-q-v1"
            ),
            "state_size": self.state_size,
            "action_size": self.action_size,
            "hidden_size": self.hidden_size,
            "action_hidden_size": self.action_hidden_size,
            "entity_layers": self.entity_layers,
            "entity_heads": self.entity_heads,
            "card_vocab_size": self.card_vocab_size,
            "card_embedding_size": self.card_embedding_size,
            "card_semantic_feature_size": self.card_semantic_feature_size,
            "entity_count": self.entity_count,
            "entity_card_slot_count": self.entity_card_slot_count,
        }


class TorchPolicyValueModel:
    """Inference adapter implementing the framework-neutral model protocol."""

    name = "torch-policy-value-mlp-v1"

    def __init__(
        self, model: PolicyValueNet, device: torch.device,
        *, value_trained: bool = True, action_value_trained: bool = False,
        state_schema_version: int = 1,
        root_perspective_value: bool = False,
    ):
        self.model = model.to(device).eval()
        self.name = str(model.metadata()["architecture"])
        self.device = device
        self.value_trained = value_trained
        self.action_value_trained = action_value_trained
        self.state_schema_version = state_schema_version
        self.root_perspective_value = root_perspective_value

    @classmethod
    def from_checkpoint(
        cls, path: str, device: str | torch.device = "cpu"
    ) -> "TorchPolicyValueModel":
        if str(device).startswith("npu"):
            import torch_npu  # noqa: F401
        device = torch.device(device)
        checkpoint = load_checkpoint(path)
        metadata = checkpoint["report"]["model"]
        feature = checkpoint["report"].get("feature_schema", {})
        configure_card_vocab(
            feature.get("card_vocab_mode", "legacy"),
            vocabulary=feature.get("card_vocab_ids"),
        )
        current_schema = feature_schema(int(feature.get("schema_version", 1)))
        if int(feature.get("schema_version", 1)) >= 7:
            # The semantic table is frozen inside the checkpoint; runtime
            # compatibility depends on its recorded digest, not on rebuilding
            # it from a potentially newer card catalogue.
            current_schema["entity_card_semantic_sha256"] = feature.get(
                "entity_card_semantic_sha256"
            )
        if feature and not compatible_feature_schema(feature, current_schema):
            raise ValueError("checkpoint feature schema differs from its restored vocabulary")
        architecture = metadata.get("architecture", "policy-value-mlp-v1")
        model_class = {
            "policy-value-mlp-v1": PolicyValueNet,
            "policy-value-interaction-mlp-v2": InteractionPolicyValueNet,
            "policy-value-bilinear-mlp-v3": BilinearPolicyValueNet,
            "policy-value-residual-mlp-v4": ResidualPolicyValueNet,
            "policy-value-structured-residual-v5": StructuredResidualPolicyValueNet,
            "policy-value-structured-residual-v5-action-q-v1": StructuredResidualPolicyValueNet,
            "policy-value-structured-residual-v6-semantic-action-q-v1": StructuredResidualPolicyValueNet,
            "policy-value-jev-v6-action-q-v1": JointEntityPolicyValueNet,
            "policy-value-jev-v7-action-q-v1": JointEntityPolicyValueNet,
        }.get(architecture)
        if model_class is None:
            raise ValueError(f"unsupported model architecture: {architecture}")
        model_args = [
            int(metadata["state_size"]), int(metadata["action_size"]),
            int(metadata["hidden_size"]), int(metadata["action_hidden_size"]),
        ]
        if model_class is ResidualPolicyValueNet:
            model_args.append(int(metadata.get("residual_blocks", 4)))
        elif model_class is StructuredResidualPolicyValueNet:
            model_args.extend((
                int(metadata.get("residual_blocks", 4)),
                int(metadata["card_vocab_size"]),
                int(metadata.get("card_embedding_size", 128)),
            ))
        elif model_class is JointEntityPolicyValueNet:
            model_args.extend((
                int(metadata.get("entity_layers", 2)),
                int(metadata.get("entity_heads", 8)),
                int(metadata["card_vocab_size"]),
                int(metadata.get("card_embedding_size", 128)),
                int(metadata.get("entity_card_slot_count", 0)),
                feature.get("entity_card_semantic_lookup"),
            ))
        model = model_class(*model_args)
        action_head_missing = False
        if model_class in (StructuredResidualPolicyValueNet, JointEntityPolicyValueNet):
            loaded = model.load_state_dict(
                checkpoint["model_state_dict"], strict=False
            )
            allowed_missing = {
                key for key in loaded.missing_keys
                if key.startswith("action_value_head.")
            }
            if set(loaded.missing_keys) != allowed_missing or loaded.unexpected_keys:
                raise ValueError(
                    "checkpoint weights differ beyond the optional action-value head: "
                    f"missing={loaded.missing_keys}, unexpected={loaded.unexpected_keys}"
                )
            action_head_missing = bool(allowed_missing)
        else:
            model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        return cls(
            model, device,
            value_trained=bool(checkpoint["report"].get("value_trained", True)),
            action_value_trained=(
                bool(checkpoint["report"].get("action_value_trained", False))
                and not action_head_missing
            ),
            state_schema_version=int(
                feature.get("schema_version", 1)
            ),
            root_perspective_value=bool(
                checkpoint["report"].get("root_perspective_value_trained", False)
            ),
        )

    def predict(self, game, actions) -> PolicyValueOutput:
        return self.predict_batch(((game, actions),))[0]

    def predict_value(self, game, observer: int) -> float:
        """Predict the value from a fixed player's observation.

        Information-set search must compare leaves from one root player's
        perspective.  Re-evaluating from whichever player happens to act at a
        leaf and negating it assumes both players' private observations yield
        perfectly antisymmetric estimates, which is not true for an
        imperfect-information model.
        """
        if observer not in (0, 1):
            raise ValueError("observer must be player 0 or 1")
        state = torch.tensor(
            [encode_state(
                game, observer, schema_version=self.state_schema_version,
            )],
            dtype=torch.float32,
            device=self.device,
        )
        # The value head is state-only; a single masked dummy action satisfies
        # the shared forward interface without affecting value prediction.
        actions = torch.zeros(
            (1, 1, self.model.action_size),
            dtype=torch.float32,
            device=self.device,
        )
        mask = torch.ones((1, 1), dtype=torch.bool, device=self.device)
        with torch.inference_mode():
            output = self.model(state, actions, mask)
        return float(output[1].item())

    def predict_batch(self, requests) -> tuple[PolicyValueOutput, ...]:
        """Evaluate variable-sized legal-action sets in one model forward pass.

        Search is presently sequential, but actor/learner scheduling can gather
        leaf requests from several trees.  Padding only occurs within that
        gathered batch and the mask ensures impossible padded actions never
        receive probability mass.  Keeping the ordinary ``predict`` method as
        a one-item wrapper preserves the existing policy interface.
        """
        requests = tuple(requests)
        outputs = [PolicyValueOutput((), 0.0) for _ in requests]
        nonempty = [
            (index, game, tuple(actions))
            for index, (game, actions) in enumerate(requests)
            if actions
        ]
        if not nonempty:
            return tuple(outputs)
        max_actions = max(len(actions) for _, _, actions in nonempty)
        # Build compact CPU buffers first, then transfer each tensor once.
        # Creating one NPU tensor per legal-action set turns a large batch into
        # dozens of tiny H2D transfers and host/device synchronizations.
        states_cpu = torch.tensor(
            [
                encode_state(
                    game, game.current,
                    schema_version=self.state_schema_version,
                )
                for _, game, _ in nonempty
            ],
            dtype=torch.float32,
        )
        action_tensor_cpu = torch.zeros(
            (len(nonempty), max_actions, self.model.action_size),
            dtype=torch.float32,
        )
        mask_cpu = torch.zeros(
            (len(nonempty), max_actions), dtype=torch.bool
        )
        for batch_index, (_, game, actions) in enumerate(nonempty):
            encoded = torch.tensor(
                [
                    encode_action(
                        game, action,
                        schema_version=self.state_schema_version,
                    )
                    for action in actions
                ],
                dtype=torch.float32,
            )
            action_tensor_cpu[batch_index, :len(actions)] = encoded
            mask_cpu[batch_index, :len(actions)] = True
        states = states_cpu.to(self.device)
        action_tensor = action_tensor_cpu.to(self.device)
        mask = mask_cpu.to(self.device)
        # Inference mode also disables autograd version-counter bookkeeping;
        # this path never returns tensors that will participate in training.
        with torch.inference_mode():
            if (self.action_value_trained and isinstance(
                self.model, (StructuredResidualPolicyValueNet,
                             JointEntityPolicyValueNet),
            )):
                logits, values, action_values = self.model.forward_with_action_values(
                    states, action_tensor, mask
                )
            else:
                logits, values = self.model(states, action_tensor, mask)
                action_values = None
            # Return policy and value in one D2H transfer. Separate ``cpu``
            # calls serialize two small NPU synchronizations per root batch.
            output_tensor = torch.cat(
                (torch.softmax(logits, dim=1), values.unsqueeze(1))
                + (() if action_values is None else (action_values,)),
                dim=1,
            )
            results = output_tensor.cpu().tolist()
        for batch_index, (index, _, actions) in enumerate(nonempty):
            result = results[batch_index]
            outputs[index] = PolicyValueOutput(
                tuple(result[:len(actions)]),
                float(result[max_actions]),
                (() if action_values is None else tuple(
                    result[max_actions + 1:max_actions + 1 + len(actions)]
                )),
            )
        return tuple(outputs)
