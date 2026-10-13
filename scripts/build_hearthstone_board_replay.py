#!/usr/bin/env python3
"""Build a compact, self-contained Hearthstone-style viewer for match traces."""
from __future__ import annotations

import json
from pathlib import Path
import sys


def slim_player(player: dict) -> dict:
    return {
        "player": player["player"],
        "health": player["health"],
        "armor": player["armor"],
        "mana": player["mana"],
        "deck_count": player["deck_count"],
        "weapon": player["weapon"],
        "hand": [{k: card.get(k) for k in ("id", "entity", "name", "cost")} for card in player["hand"]],
        "board": [{k: card.get(k) for k in ("id", "name", "attack", "health", "keywords")} for card in player["board"]],
        "locations": player["locations"],
    }


def infer_class(deck_label: str) -> str:
    """Infer the displayed Hearthstone class from a deck label."""
    s = deck_label.casefold()
    groups = {
        "牧师": ("任务牧", "控制牧", "脏牧", "quest priest", "control priest", "raza priest"),
        "术士": ("drake warlock", "拉法姆术", "先驱术", "恶魔术", "piglock", "harold piglock"),
        "德鲁伊": ("快攻德", "主厨德", "艾萨拉德", "aggro druid"),
        "萨满祭司": ("穆格萨", "兆示萨", "mogu shaman"),
        "法师": ("魔网法", "打脸法", "任务法", "托奇法", "法力风暴法", "mage"),
        "死亡骑士": ("邪dk", "蛋dk", "先驱dk", "death knight", "dk"),
        "恶魔猎手": ("虚灵瞎", "raza dh", "demon hunter", "dh"),
        "盗贼": ("潜行贼", "兆示贼", "艾雅贼", "二费贼", "迦罗娜贼", "rogue"),
        "圣骑士": ("光铸骑", "paladin"),
        "猎人": ("龙猎", "伙伴猎", "dragon hunter", "hunter"),
        "战士": ("龙战", "龙海盗战", "海盗战", "蛋战", "洛戈什战", "兆示战", "任务战", "dragon warrior", "warrior"),
    }
    for cls, needles in groups.items():
        if any(needle.casefold() in s for needle in needles):
            return cls
    return "未知职业"


def infer_classes(label: str) -> dict:
    parts = [part.strip() for part in label.split(" vs ", 1)]
    if len(parts) == 2:
        return {"p1": infer_class(parts[0]), "p2": infer_class(parts[1])}
    return {"p1": infer_class(label), "p2": "未知职业"}


def read_match(path: Path, label: str) -> dict:
    trace = json.loads(path.read_text(encoding="utf-8"))
    return {
        "label": label,
        "classes": infer_classes(label),
        "seed": trace["seed"],
        "winner": trace["winner"],
        "invalid_actions": trace["invalid_actions"],
        "steps": [{
            "step": row["step"],
            "turn": row["turn_before"],
            "actor": row["actor"],
            "action": row["description"],
            "before": {"turn": row["state_before"]["turn"], "active_player": row["state_before"]["active_player"], "pending_choice": row["state_before"].get("pending_choice"), "players": [slim_player(p) for p in row["state_before"]["players"]]},
            "after": {"turn": row["state_after"]["turn"], "active_player": row["state_after"]["active_player"], "pending_choice": row["state_after"].get("pending_choice"), "players": [slim_player(p) for p in row["state_after"]["players"]]},
        } for row in trace["steps"]],
    }


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: build_hearthstone_board_replay.py OUTPUT.html LABEL=TRACE.json [...]")
    output = Path(sys.argv[1])
    matches = []
    for spec in sys.argv[2:]:
        label, raw_path = spec.split("=", 1)
        matches.append(read_match(Path(raw_path), label))
    data = json.dumps(matches, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    fragment = r'''<div id="hs-replay">
  <header class="toolbar">
    <div class="heading"><span class="eyebrow">MATCH REPLAY</span><h1>多卡组对局复盘</h1></div>
    <label class="picker">模型版本<select id="match-picker" aria-label="选择模型版本"></select></label>
  </header>
  <section class="controls" aria-label="回放控制">
    <button id="prev" type="button" aria-label="上一步">◀</button>
    <div class="stepbox"><strong id="step-label"></strong><input id="step-range" type="range" min="1" max="1" value="1" aria-label="选择回放步骤"></div>
    <button id="next" type="button" aria-label="下一步">▶</button>
    <label class="phase-picker">显示<select id="phase"><option value="after">动作后</option><option value="before">动作前</option></select></label>
    <button id="opponent-toggle" type="button" aria-pressed="true">隐藏对手手牌</button>
  </section>
  <div class="summary" id="summary" aria-live="polite"></div>
  <main class="table" aria-label="炉石对战桌面复盘">
    <section class="side enemy" id="p2">
      <div class="hand-zone"><div class="zone-label">P2 手牌 <span class="hand-count"></span></div><div class="hand-cards"></div></div>
      <div class="hero-line"><div class="hero-portrait">P2</div><div class="hero-meta"><b class="hero-class"></b><span class="resource"></span><span class="deck"></span><span class="weapon"></span></div><div class="health-orb"></div><div class="armor-orb"></div></div>
      <div class="minion-row"></div>
      <div class="location-row"></div>
    </section>
    <div class="centerline"><span id="center-turn"></span><span class="lantern">✦</span></div>
    <section class="side friendly" id="p1">
      <div class="location-row"></div>
      <div class="minion-row"></div>
      <div class="hero-line"><div class="hero-portrait">P1</div><div class="hero-meta"><b class="hero-class"></b><span class="resource"></span><span class="deck"></span><span class="weapon"></span></div><div class="health-orb"></div><div class="armor-orb"></div></div>
      <div class="hand-zone"><div class="zone-label">P1 手牌 <span class="hand-count"></span></div><div class="hand-cards"></div></div>
    </section>
  </main>
  <footer class="actionline"><span class="action-icon">➤</span><div><small>本步操作</small><strong id="action"></strong></div><span class="outcome" id="outcome"></span></footer>
</div>
<script>
(() => {
  const matches = __MATCH_DATA__;
  const root = document.getElementById('hs-replay');
  const picker = root.querySelector('#match-picker');
  const range = root.querySelector('#step-range');
  const phase = root.querySelector('#phase');
  const toggle = root.querySelector('#opponent-toggle');
  let matchIndex = 0, stepIndex = 0, showOpponentHand = true;
  matches.forEach((m, i) => { const o = document.createElement('option'); o.value = i; o.textContent = m.label; picker.append(o); });
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function makeCard(card, type) {
    const el = document.createElement('div'); el.className = `game-card ${type}`;
    if (type === 'minion') {
      el.innerHTML = `<span class="card-name">${esc(card.name)}</span><span class="stats"><i>${esc(card.attack ?? 0)}</i><i>${esc(card.health ?? 0)}</i></span>`;
      const kws = (card.keywords || []).filter(Boolean);
      if (kws.length) { const kw = document.createElement('small'); kw.className = 'keywords'; kw.textContent = kws.join(' · '); el.append(kw); }
    } else el.innerHTML = `<span class="gem">${esc(card.cost ?? 0)}</span><span class="card-name">${esc(card.name)}</span>`;
    el.setAttribute('aria-label', type === 'minion' ? `${card.name}, ${card.attack}/${card.health}` : `${card.name}, ${card.cost}费`);
    return el;
  }
  function renderHand(container, player, hidden, selected) {
    container.innerHTML = '';
    if (hidden) {
      for (let i=0;i<player.hand.length;i++){ const back=document.createElement('div'); back.className='card-back'; back.textContent='✦'; back.setAttribute('aria-label','对手手牌'); container.append(back); }
    } else if (!player.hand.length) container.innerHTML = '<span class="empty">空手牌</span>';
    else player.hand.forEach(c => {
      const card = makeCard(c,'hand-card');
      if (selected.has(c.entity)) {
        card.classList.add('mulligan-selected');
        const badge = document.createElement('small'); badge.className='mulligan-badge';
        badge.textContent='换'; card.append(badge);
      }
      container.append(card);
    });
  }
  function renderSide(id, player, hideHand, pending) {
    const side = root.querySelector(`#${id}`);
    side.querySelector('.hand-count').textContent = `(${player.hand.length})`;
    const selected = new Set(
      pending?.kind === 'MULLIGAN' && pending.player === player.player
        ? (pending.options || []).filter(c => c.replace).map(c => c.entity) : []
    );
    renderHand(side.querySelector('.hand-cards'), player, hideHand, selected);
    side.querySelector('.health-orb').textContent = player.health;
    side.querySelector('.armor-orb').textContent = `盾 ${player.armor}`;
    side.querySelector('.resource').textContent = `法力 ${player.mana[0]}/${player.mana[1]}`;
    side.querySelector('.deck').textContent = `牌库 ${player.deck_count}`;
    side.querySelector('.weapon').textContent = player.weapon ? `武器 ${player.weapon.name} ${player.weapon.attack}/${player.weapon.durability}` : '无武器';
    const row = side.querySelector('.minion-row'); row.innerHTML = '';
    if (!player.board.length) row.innerHTML = '<span class="empty">空场</span>';
    else player.board.forEach(c => row.append(makeCard(c,'minion')));
    const loc = side.querySelector('.location-row'); loc.innerHTML = '';
    (player.locations || []).forEach(l => {const badge=document.createElement('span'); badge.className='location'; badge.textContent=`${l.name || l.id} · 耐久${l.durability} · 冷却${l.cooldown}`; loc.append(badge);});
  }
  function render() {
    const match = matches[matchIndex], step = match.steps[stepIndex];
    const state = step[phase.value];
    range.max = match.steps.length; range.value = stepIndex + 1;
    const turnText = step.turn === 0 ? '开局换牌' : `第 ${step.turn} 回合`;
    root.querySelector('#step-label').textContent = `第 ${stepIndex+1} / ${match.steps.length} 步 · ${turnText}`;
    const winnerText = match.winner == null ? '未分胜负（达到回放上限）' : `P${match.winner+1} 获胜`;
    root.querySelector('#summary').innerHTML = `<span>${esc(match.label)}</span><span>Seed ${match.seed}</span><span>${winnerText}</span><span>非法动作 ${match.invalid_actions}</span>`;
    root.querySelector('#center-turn').textContent = state.turn === 0
      ? `开局换牌 · 当前行动 P${state.active_player}`
      : `第 ${state.turn} 回合 · 当前行动 P${state.active_player}`;
    root.querySelector('#action').textContent = step.action;
    root.querySelector('#outcome').textContent = phase.value === 'after' ? '动作结算后' : '动作执行前';
    renderSide('p2', state.players[1], !showOpponentHand, state.pending_choice);
    renderSide('p1', state.players[0], false, state.pending_choice);
    root.querySelector('#p1 .hero-class').textContent = match.classes.p1;
    root.querySelector('#p2 .hero-class').textContent = match.classes.p2;
    root.querySelector('#prev').disabled = stepIndex === 0;
    root.querySelector('#next').disabled = stepIndex === match.steps.length - 1;
  }
  picker.addEventListener('change', () => {matchIndex=Number(picker.value); stepIndex=0; render();});
  range.addEventListener('input', () => {stepIndex=Number(range.value)-1; render();});
  phase.addEventListener('change', render);
  root.querySelector('#prev').addEventListener('click', () => {stepIndex=Math.max(0,stepIndex-1); render();});
  root.querySelector('#next').addEventListener('click', () => {stepIndex=Math.min(matches[matchIndex].steps.length-1,stepIndex+1); render();});
  toggle.addEventListener('click', () => {showOpponentHand=!showOpponentHand; toggle.textContent=showOpponentHand?'隐藏对手手牌':'显示对手手牌'; toggle.setAttribute('aria-pressed',String(showOpponentHand)); render();});
  render();
})();
</script>'''.replace("__MATCH_DATA__", data)
    page = """<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>龙战镜像对局回放</title><style>
:root{color-scheme:dark;--bg:#111916;--table:#24483a;--wood:#5d3c27;--ink:#f4edd9;--soft:#c5d1c9;--gold:#e5bb61;--red:#b84d49;--blue:#4d79ae;--green:#416e56;--border:#9d8052}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 50% 40%,#1e3129,#101512 70%);color:var(--ink);font:14px/1.45 system-ui,"Microsoft YaHei",sans-serif}#hs-replay{max-width:1100px;margin:auto;padding:14px}.toolbar,.controls,.summary,.actionline{display:flex;align-items:center;gap:12px}.toolbar{justify-content:space-between;margin-bottom:10px}.heading h1{font-size:20px;font-weight:600;margin:0}.eyebrow{color:var(--gold);letter-spacing:.12em;font-size:11px}.picker,.phase-picker{display:flex;align-items:center;gap:7px;color:var(--soft)}select,button{background:#26342d;color:var(--ink);border:1px solid #607568;border-radius:7px;padding:8px 10px;font:inherit}button{cursor:pointer;min-width:40px}button:disabled{opacity:.4;cursor:default}.controls{flex-wrap:wrap;background:#1a2520;border:1px solid #405248;border-radius:10px;padding:9px}.stepbox{flex:1;min-width:180px;display:flex;align-items:center;gap:12px}.stepbox input{flex:1;accent-color:var(--gold)}.summary{flex-wrap:wrap;gap:8px 18px;padding:8px 4px;color:#d7c795}.table{position:relative;overflow:hidden;min-height:570px;border:10px solid var(--wood);border-radius:26px;background:radial-gradient(ellipse at center,#446c51 0,#315944 45%,#244638 100%);box-shadow:inset 0 0 0 2px #9d8052,inset 0 0 50px #12261e,0 10px 24px #0008;padding:12px 18px;display:flex;flex-direction:column;justify-content:space-between}.side{display:flex;flex-direction:column;gap:8px;min-height:235px}.enemy{justify-content:flex-start}.friendly{justify-content:flex-end}.hand-zone{min-height:76px}.zone-label{color:#e4d8b8;font-size:12px;margin:0 0 4px 4px}.hand-count{color:#f3c55f}.hand-cards{display:flex;justify-content:center;align-items:flex-end;min-height:67px;padding:1px 3px}.game-card{position:relative;display:flex;align-items:center;justify-content:center;text-align:center;color:#fff5d7;text-shadow:0 1px 2px #000;font-weight:600;background:linear-gradient(150deg,#4d6c68,#243d39 62%,#192a29);border:2px solid #b69a65;box-shadow:0 2px 5px #0009;border-radius:9px}.hand-card{width:72px;height:64px;margin-left:-9px;padding:10px 5px 7px;transform:rotate(var(--rot,0deg));font-size:11px}.hand-card:nth-child(odd){--rot:-2deg}.hand-card:nth-child(even){--rot:2deg}.card-name{line-height:1.1;max-height:3.3em;overflow:hidden}.gem{position:absolute;top:-5px;left:-5px;background:var(--blue);border:2px solid #bcd6ee;color:white;border-radius:50%;width:22px;height:22px;display:grid;place-items:center;font-size:12px;z-index:1}.card-back{width:35px;height:52px;margin-left:-8px;border:2px solid #ceb270;border-radius:8px;background:repeating-linear-gradient(45deg,#344b70,#344b70 4px,#1f3352 4px,#1f3352 8px);display:grid;place-items:center;color:#f5d68b}.hero-line{display:flex;align-items:center;justify-content:center;gap:9px;min-height:60px}.hero-portrait{width:48px;height:48px;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle at 35% 25%,#e5c681,#765229 55%,#292017);border:3px solid #ceb879;font-weight:700;box-shadow:0 2px 7px #0009}.hero-meta{display:flex;flex-direction:column;color:#f2e7ca;font-size:12px;min-width:112px}.hero-meta b{font-size:13px}.health-orb,.armor-orb{min-width:38px;height:36px;padding:0 7px;border-radius:20px;display:grid;place-items:center;border:2px solid #e2c796;background:var(--red);font-weight:700}.armor-orb{background:#637b8e;font-size:11px}.minion-row{display:flex;align-items:center;justify-content:center;gap:9px;min-height:94px;flex-wrap:wrap}.minion{width:88px;height:78px;padding:12px 7px 17px;font-size:12px;background:linear-gradient(150deg,#78936c,#3d5942 58%,#253b2c)}.stats{position:absolute;left:0;right:0;bottom:-7px;display:flex;justify-content:space-between}.stats i{font-style:normal;background:var(--blue);border:2px solid #c9dff0;border-radius:50%;width:25px;height:25px;display:grid;place-items:center}.stats i:last-child{background:#a83c38;border-color:#f1b2a4}.keywords{position:absolute;bottom:17px;left:2px;right:2px;color:#f0d995;font-size:9px}.location-row{display:flex;justify-content:center;gap:6px;flex-wrap:wrap;min-height:20px}.location{background:#8a6c39;color:#fff0c4;border:1px solid #e2ca87;border-radius:14px;padding:2px 9px;font-size:11px}.empty{color:#b8c9ba;font-style:italic;font-size:12px}.centerline{height:35px;display:flex;align-items:center;justify-content:center;gap:14px;color:#e6d7a9;text-shadow:0 1px 4px #000}.centerline:before,.centerline:after{content:"";height:1px;flex:1;background:linear-gradient(90deg,transparent,#d1b66b,transparent)}.lantern{color:var(--gold)}.actionline{margin-top:12px;background:#1b2520;border:1px solid #536354;border-radius:10px;padding:10px 14px}.action-icon{font-size:18px;color:var(--gold)}.actionline div{display:flex;flex-direction:column;min-width:0}.actionline small{color:#c4cabb}.actionline strong{font-weight:600}.outcome{margin-left:auto;color:#d4c28e;white-space:nowrap}@media(max-width:600px){#hs-replay{padding:8px}.toolbar{align-items:flex-start}.table{padding:8px 6px;min-height:530px;border-width:6px}.side{min-height:225px}.hero-line{gap:5px}.hero-meta{min-width:84px;font-size:11px}.health-orb,.armor-orb{min-width:32px;height:31px}.game-card.hand-card{width:61px;font-size:10px;margin-left:-13px}.minion{width:72px}.controls{gap:7px}.phase-picker{font-size:12px}}
.mulligan-selected{border-color:#ed7b68!important;box-shadow:0 0 0 2px #e8695e,0 2px 5px #0009!important}.mulligan-badge{position:absolute;right:-6px;top:-7px;background:#ae3f36;color:#fff;padding:1px 5px;border-radius:8px;font-size:11px}
</style></head><body>""" + fragment + "</body></html>"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"wrote {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    raise SystemExit(main())
