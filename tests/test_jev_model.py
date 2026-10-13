import torch

from hsa.torch_model import JointEntityPolicyValueNet


def test_jev_v6_forward_and_action_mask():
    vocab = 11
    semantic = 4
    state_size = 376 + 4 * vocab + 4 * semantic
    action_size = 56 + 2 * vocab + 2 * semantic
    model = JointEntityPolicyValueNet(
        state_size,
        action_size,
        hidden_size=32,
        action_hidden_size=16,
        entity_layers=1,
        entity_heads=4,
        card_vocab_size=vocab,
        card_embedding_size=8,
    )
    states = torch.randn(2, state_size)
    actions = torch.randn(2, 3, action_size)
    mask = torch.tensor([[True, True, False], [True, False, False]])

    logits, values, action_q = model.forward_with_action_values(
        states, actions, mask
    )

    assert logits.shape == (2, 3)
    assert values.shape == (2,)
    assert action_q.shape == (2, 3)
    assert torch.all(logits[~mask] == -1.0e4)
    assert torch.all(action_q[~mask] == 0.0)
    assert model.metadata()["architecture"] == "policy-value-jev-v6-action-q-v1"
    assert model.metadata()["entity_count"] == 45


def test_jev_requires_schema_v6():
    vocab = 11
    state_size = 376 + 4 * vocab
    action_size = 56 + 2 * vocab
    try:
        JointEntityPolicyValueNet(
            state_size,
            action_size,
            hidden_size=32,
            action_hidden_size=16,
            entity_layers=1,
            entity_heads=4,
            card_vocab_size=vocab,
            card_embedding_size=8,
        )
    except ValueError as error:
        assert "schema-v6" in str(error)
    else:
        raise AssertionError("schema-v5 input should be rejected")


def test_jev_v7_attaches_identity_and_semantics_to_entity_tokens():
    vocab = 11
    semantic = 4
    entity_slots = 42
    state_size = 376 + 4 * vocab + 4 * semantic + entity_slots
    action_size = 56 + 2 * vocab + 2 * semantic
    lookup = torch.randn(vocab + 2, semantic)
    lookup[0].zero_()
    model = JointEntityPolicyValueNet(
        state_size,
        action_size,
        hidden_size=32,
        action_hidden_size=16,
        entity_layers=1,
        entity_heads=4,
        card_vocab_size=vocab,
        card_embedding_size=8,
        entity_card_slot_count=entity_slots,
        entity_card_semantic_lookup=lookup,
    )
    states = torch.randn(2, state_size)
    states[:, -entity_slots:] = torch.randint(0, vocab + 2, (2, entity_slots))
    actions = torch.randn(2, 3, action_size)

    logits, values, action_q = model.forward_with_action_values(states, actions)

    assert logits.shape == (2, 3)
    assert values.shape == (2,)
    assert action_q.shape == (2, 3)
    assert model.metadata()["architecture"] == "policy-value-jev-v7-action-q-v1"
    assert model.metadata()["entity_count"] == 49
    assert model.metadata()["entity_card_slot_count"] == 42
    assert not any(
        isinstance(module, torch.nn.TransformerEncoderLayer)
        for module in model.modules()
    )
