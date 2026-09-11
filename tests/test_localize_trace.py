from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "localize_search_trace_zhcn.py"
SPEC = importlib.util.spec_from_file_location("localize_search_trace_zhcn", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
LOCALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCALIZER)


def test_generated_from_pool_event_is_readable_chinese() -> None:
    event = {
        "kind": "generated_from_pool",
        "player": 1,
        "card": "EDR_889",
        "source": "CATA_556",
        "entity": 74,
    }
    names = {"EDR_889": "鲜花商贩", "CATA_556": "载蛋雏龙"}

    assert LOCALIZER.event_text(event, names) == (
        "玩家2从随机牌池获得鲜花商贩[EDR_889]并置入手牌"
        "（来源：载蛋雏龙[CATA_556]）"
    )
