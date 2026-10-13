from hsa.deck_variants import compatible_deck_variants


def fixtures():
    metadata = {card: {'collectible': True, 'cardClass': 'WARLOCK', 'rarity': 'COMMON'}
                for card in ('A', 'B', 'C', 'NEW', 'ANCHOR', 'TOKEN')}
    metadata['ANCHOR']['rarity'] = 'LEGENDARY'
    metadata['TOKEN']['collectible'] = False
    candidates = [{'id': 'base', 'class': 'WARLOCK',
                   'counts': {'A': 2, 'B': 2, 'C': 1, 'ANCHOR': 1, 'TOKEN': 1}}]
    return candidates, metadata


def test_variants_preserve_revealed_copies_size_and_special_packages():
    candidates, metadata = fixtures()
    result = compatible_deck_variants(candidates, {'A': 2, 'NEW': 2}, 'WARLOCK', metadata)
    assert result['mode'] == 'synthetic_variants'
    assert result['replacements'] == 2
    assert not result['truncated']
    assert len(result['candidates']) == 2
    for candidate in result['candidates']:
        assert sum(candidate['counts'].values()) == 7
        assert candidate['counts']['A'] == 2
        assert candidate['counts']['NEW'] == 2
        assert candidate['counts']['ANCHOR'] == candidate['counts']['TOKEN'] == 1
    assert candidates[0]['counts'].get('NEW') is None


def test_no_substitution_before_contradiction_and_no_unbounded_fallback():
    candidates, metadata = fixtures()
    assert compatible_deck_variants(candidates, {'A': 1}, 'WARLOCK', metadata)['mode'] == 'manifest'
    assert not compatible_deck_variants(candidates, {'NEW': 2}, 'WARLOCK', metadata,
                                        max_replacements=1)['candidates']
    assert not compatible_deck_variants(candidates, {'NEW': 3}, 'WARLOCK', metadata)['candidates']
    assert not compatible_deck_variants(candidates, {'NEW': 1}, 'MAGE', metadata)['candidates']


def test_truncation_is_explicit_and_missing_metadata_is_not_invented():
    candidates, metadata = fixtures()
    result = compatible_deck_variants(candidates, {'NEW': 1}, 'WARLOCK', metadata,
                                     max_variants=1)
    assert len(result['candidates']) == 1 and result['truncated']
    del metadata['NEW']
    assert not compatible_deck_variants(candidates, {'NEW': 1}, 'WARLOCK', metadata)['candidates']


def test_start_of_game_cards_are_not_removed_as_flex_slots():
    candidates, metadata = fixtures()
    for card in ('A', 'B', 'C'):
        metadata[card]['text'] = '<b>Start of Game:</b> Change deck construction.'
    assert not compatible_deck_variants(candidates, {'NEW': 1}, 'WARLOCK', metadata)['candidates']


def test_observed_starting_size_rejects_wrong_size_without_hidden_identities():
    candidates, metadata = fixtures()
    candidates.append({'id': 'larger', 'class': 'WARLOCK', 'counts': {'A': 20}})
    result = compatible_deck_variants(candidates, {}, 'WARLOCK', metadata, starting_size=7)
    assert [c['id'] for c in result['candidates']] == ['base']
