"""
game_engine.py — Werewolf Bot v3.0
===================================
Pure game logic with zero discord imports.
Manages:
  • Lobby → Night → Day → Voting → GameOver state machine
  • Player registry & role distribution (random.shuffle)
  • Night action resolution (wolf, doctor, seductress, etc.)
  • Day voting tally (mayor weight, king flip, tie-break)
  • Win-condition checking

The engine is stateless across games — each GameSession
creates a fresh GameEngine instance.
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from config import SPECIAL_ROLES


# ═══════════════════════════════════════════════════════════════
# ENUMS & DATA CLASSES
# ═══════════════════════════════════════════════════════════════

class GameState(Enum):
    """Finite-state-machine stages for a single game session."""
    LOBBY     = "lobby"
    NIGHT     = "night"
    DAY       = "day"
    VOTING    = "voting"
    GAME_OVER = "game_over"


class PlayerData:
    """
    Runtime data for one player in the current game.
    Every field is reset when a new GameEngine is created.
    """
    __slots__ = (
        "id", "name", "role", "alive",
        "detective_used", "guardian_used", "king_used",
        "doctor_target", "seductress_target",
        "vote_target", "wolf_vote",
        "detective_target", "guardian_target", "king_flip_target",
    )

    def __init__(self, member_id: int, name: str):
        self.id   = member_id
        self.name = name

        # Assigned during role distribution
        self.role: Optional[str] = None
        self.alive = True

        # Per-role ability flags
        self.detective_used = False   # 🔍 once per game
        self.guardian_used  = False   # 🛡️ once per game
        self.king_used      = False   # 👑 once per game

        # Per-round night targets (reset each night)
        self.doctor_target:      Optional[int] = None  # ⚕️
        self.seductress_target:  Optional[int] = None  # 💃

        # Day-vote target (reset each day)
        self.vote_target: Optional[int] = None

        # Night-action temporary storage (cleared after resolution)
        self.wolf_vote:         Optional[int] = None
        self.detective_target:  Optional[int] = None
        self.guardian_target:   Optional[int] = None
        self.king_flip_target:  Optional[int] = None


class NightResult:
    """Returned by resolve_night(). Contains all events that happened."""
    def __init__(self):
        self.killed:             List[int] = []            # IDs of dead players
        self.detective_result:   Optional[Tuple[int, int, bool]] = None  # (det_id, tgt_id, is_wolf)
        self.exposed_wolf:       Optional[int] = None      # Um Fadi's exposed wolf
        self.message:            str = ""                  # Human-readable events


class VoteResult:
    """Returned by resolve_voting(). Contains tally and elimination."""
    def __init__(self):
        self.eliminated:   Optional[int] = None
        self.vote_counts:  Dict[int, int] = {}
        self.message:      str = ""
        self.tie:          bool = False


# ═══════════════════════════════════════════════════════════════
# GAME ENGINE  (pure logic, no I/O)
# ═══════════════════════════════════════════════════════════════

class GameEngine:
    """
    Stateless-pure game engine.  One instance per game session.
    All player state lives in self.players (dict of PlayerData).
    Night / vote resolution is deterministic given fixed inputs.
    """

    def __init__(self):
        self.state: GameState = GameState.LOBBY
        self.players: Dict[int, PlayerData] = {}
        self.order: List[int] = []           # join-order (also iteration order)
        self.day_number: int = 0
        self.wolf_votes: Dict[int, int] = {}          # wolf_id → target_id
        self.night_actions_done: Set[int] = set()     # players who already acted

    # ─── Player Management ────────────────────────────────────────────────

    @property
    def living_ids(self) -> List[int]:
        """IDs of all players who are still alive, in join order."""
        return [pid for pid in self.order if self.players[pid].alive]

    @property
    def dead_ids(self) -> List[int]:
        """IDs of players who died during the game, in join order."""
        return [pid for pid in self.order if not self.players[pid].alive]

    @property
    def living_wolves(self) -> List[int]:
        """IDs of alive players whose role is 'wolf'."""
        return [pid for pid in self.living_ids if self.players[pid].role == "wolf"]

    def add_player(self, member_id: int, name: str) -> bool:
        """Register a new player.  Returns False if already present or lobby full."""
        if member_id in self.players:
            return False
        self.players[member_id] = PlayerData(member_id, name)
        self.order.append(member_id)
        return True

    def remove_player(self, member_id: int) -> bool:
        """Unregister a player (lobby only).  Returns False if not found."""
        if member_id not in self.players:
            return False
        del self.players[member_id]
        if member_id in self.order:
            self.order.remove(member_id)
        return True

    def player_count(self) -> int:
        return len(self.players)

    def get_player(self, member_id: int) -> Optional[PlayerData]:
        return self.players.get(member_id)

    # ─── Role Distribution Algorithm ──────────────────────────────────────
    #
    # How it works:
    #   1. Shuffle all player IDs with random.shuffle (unbiased).
    #   2. Pick N wolves based on total player count.
    #   3. Select as many unique special roles as remaining slots allow.
    #   4. Fill leftovers with villagers.
    #   5. Shuffle the role list one more time so role order
    #      does NOT mirror shuffled-player order.
    #   6. Zip IDs → roles and assign.
    #
    # This guarantees every player gets exactly one role,
    # every game has the intended wolf:village ratio, and
    # no role is accidentally skipped or duplicated.
    # ──────────────────────────────────────────────────────────────────────

    def assign_roles(self) -> bool:
        """Distribute roles across all registered players. Returns True on success."""
        n = self.player_count()
        if n < 6:
            return False

        # Step 1 — randomise player order
        ids = list(self.players.keys())
        random.shuffle(ids)

        # Step 2 — wolf count scales with lobby size
        if n <= 7:
            num_wolves = 1
        elif n <= 10:
            num_wolves = 2
        else:
            num_wolves = 3

        # Step 3 — special roles (up to available slots)
        num_special = min(len(SPECIAL_ROLES), n - num_wolves)

        # Step 4 — build role list
        roles: List[str] = ["wolf"] * num_wolves
        selected = random.sample(SPECIAL_ROLES, num_special)
        roles.extend(selected)

        # Step 5 — fill with villagers
        remaining = n - len(roles)
        roles.extend(["villager"] * remaining)

        # Step 6 — shuffle so role order decouples from player order
        random.shuffle(roles)

        # Step 7 — assign
        for pid, role_name in zip(ids, roles):
            self.players[pid].role = role_name

        self.order = ids
        return True

    # ─── Night Actions ────────────────────────────────────────────────────

    def get_night_action_players(self) -> List[int]:
        """IDs of living players who MUST submit a night action this round."""
        result = []
        for pid in self.living_ids:
            p = self.players[pid]
            if p.role == "wolf":
                result.append(pid)
            elif p.role == "doctor":
                result.append(pid)
            elif p.role == "seductress":
                result.append(pid)
            elif p.role == "detective" and not p.detective_used:
                result.append(pid)
            elif p.role == "guardian" and not p.guardian_used:
                result.append(pid)
        return result

    def all_night_actions_done(self) -> bool:
        """True when every required player has submitted their action."""
        required = set(self.get_night_action_players())
        return required.issubset(self.night_actions_done)

    def complete_night_action(self, member_id: int):
        self.night_actions_done.add(member_id)

    # Target setters — each records the action and marks it done

    def set_wolf_vote(self, wolf_id: int, target_id: int):
        self.players[wolf_id].wolf_vote = target_id
        self.wolf_votes[wolf_id] = target_id
        self.complete_night_action(wolf_id)

    def set_doctor_target(self, doctor_id: int, target_id: int):
        self.players[doctor_id].doctor_target = target_id
        self.complete_night_action(doctor_id)

    def set_seductress_target(self, sid: int, target_id: int):
        self.players[sid].seductress_target = target_id
        self.complete_night_action(sid)

    def set_detective_target(self, did: int, target_id: int):
        self.players[did].detective_target = target_id
        self.complete_night_action(did)

    def set_guardian_target(self, gid: int, target_id: int):
        self.players[gid].guardian_target = target_id
        self.complete_night_action(gid)

    # ─── Night Resolution ─────────────────────────────────────────────────
    #
    # Priority order (hard-coded, do not reorder):
    #   1. 🐺 Wolves vote → kill_target
    #   2. 💃 Seductress — if she chose a wolf, both die.
    #      If wolves targeted her target, she dies instead.
    #   3. ⚕️ Doctor — if he healed the kill_target, cancel kill.
    #   4. 🛡️ Guardian — if he shielded the kill_target, cancel kill.
    #   5. Apply wolf kill.
    #   6. 👵 Um Fadi — if killed, expose a random wolf.
    #   7. Execute all kills (mark .alive = False).
    #   8. 🔍 Detective — reveal target's faction to detective.
    # ──────────────────────────────────────────────────────────────────────

    def resolve_night(self) -> NightResult:
        """Resolve all night actions. Returns a NightResult with events."""
        result = NightResult()

        # ── 1. Wolf kill target (majority vote, tie → random) ──────
        kill_target: Optional[int] = None
        if self.wolf_votes:
            counts: Dict[int, int] = {}
            for wid, tid in self.wolf_votes.items():
                if wid in self.living_ids:
                    counts[tid] = counts.get(tid, 0) + 1
            if counts:
                mv = max(counts.values())
                top = [t for t, c in counts.items() if c == mv]
                kill_target = random.choice(top)

        # ── 2. Gather role references ──────────────────────────────
        sed_id = next((p for p in self.living_ids if self.players[p].role == "seductress"), None)
        doc_id = next((p for p in self.living_ids if self.players[p].role == "doctor"), None)
        gua_id = next(
            (p for p in self.living_ids
             if self.players[p].role == "guardian" and not self.players[p].guardian_used),
            None,
        )

        sed_tgt = self.players[sed_id].seductress_target if sed_id else None
        doc_tgt = self.players[doc_id].doctor_target if doc_id else None
        gua_tgt = self.players[gua_id].guardian_target if gua_id else None

        # ── 3. Seductress ──────────────────────────────────────────
        if sed_id and sed_tgt and sed_tgt in self.living_ids:
            if self.players[sed_tgt].role == "wolf":
                result.killed.extend([sed_id, sed_tgt])
                result.message += (
                    f"💃 {self.players[sed_id].name} اختارت ذئباً وماتت معه!\n"
                )
                if kill_target == sed_tgt:
                    kill_target = None
            elif kill_target == sed_tgt:
                result.killed.append(sed_id)
                result.message += (
                    f"💃 {self.players[sed_id].name} ضحت بنفسها لتحمي "
                    f"{self.players[sed_tgt].name}!\n"
                )
                kill_target = None

        # ── 4. Doctor ──────────────────────────────────────────────
        if kill_target and doc_tgt == kill_target:
            result.message += f"⚕️ الطبيب أنقذ {self.players[kill_target].name}!\n"
            kill_target = None

        # ── 5. Guardian ────────────────────────────────────────────
        if kill_target and gua_tgt == kill_target:
            result.message += f"🛡️ الحارس حمى {self.players[kill_target].name}!\n"
            if gua_id:
                self.players[gua_id].guardian_used = True
            kill_target = None

        # ── 6. Apply wolf kill ─────────────────────────────────────
        if kill_target and kill_target not in result.killed:
            result.killed.append(kill_target)

        # ── 7. Um Fadi — expose wolf before death ──────────────────
        um_id = next(
            (p for p in self.order
             if self.players[p].role == "um_fadi" and self.players[p].alive),
            None,
        )
        if um_id and um_id in result.killed:
            living_wolves = [w for w in self.living_wolves if w != um_id]
            if living_wolves:
                exposed = random.choice(living_wolves)
                result.exposed_wolf = exposed
                result.message += (
                    f"👵 أم فادي فضحت {self.players[exposed].name} 🐺!\n"
                )

        # ── 8. Execute kills ───────────────────────────────────────
        for tid in result.killed:
            if tid in self.players:
                self.players[tid].alive = False

        # ── 9. Detective investigation ─────────────────────────────
        det_id = next(
            (p for p in self.living_ids
             if self.players[p].role == "detective"
             and not self.players[p].detective_used
             and self.players[p].detective_target),
            None,
        )
        if det_id:
            tgt = self.players[det_id].detective_target
            self.players[det_id].detective_used = True
            result.detective_result = (
                det_id, tgt, self.players[tgt].role == "wolf"
            )

        # ── Cleanup per-round state ────────────────────────────────
        self.wolf_votes.clear()
        self.night_actions_done.clear()
        for pid in self.living_ids:
            p = self.players[pid]
            if p.role != "doctor":
                p.doctor_target = None
            if p.role != "seductress":
                p.seductress_target = None

        return result

    # ─── Day Voting ───────────────────────────────────────────────────────

    def set_vote(self, voter_id: int, target_id: int):
        self.players[voter_id].vote_target = target_id

    def set_king_flip(self, king_id: int, target_id: int):
        """King uses his one-time power to redirect all votes to one player."""
        self.players[king_id].king_flip_target = target_id
        self.players[king_id].king_used = True

    def resolve_voting(self) -> VoteResult:
        """
        Count votes, apply mayor bonus (×2), apply king flip,
        eliminate the player with the most votes (random if tied).
        """
        result = VoteResult()
        counts: Dict[int, int] = {}

        for pid in self.living_ids:
            p = self.players[pid]
            if p.vote_target and p.vote_target in self.living_ids:
                weight = 2 if p.role == "mayor" else 1
                counts[p.vote_target] = counts.get(p.vote_target, 0) + weight

        # King flip — redirect ALL votes to one target
        king = next(
            (p for p in [self.players[pid] for pid in self.living_ids]
             if p.role == "king" and p.king_used and p.king_flip_target
             and p.king_flip_target in self.living_ids),
            None,
        )
        if king:
            total = sum(counts.values()) if counts else len(
                [p for p in self.living_ids if self.players[p].vote_target]
            )
            counts = {king.king_flip_target: max(total, 1)}
            result.message += f"👑 {king.name} استخدم سلطته وقلب الأصوات!\n"

        result.vote_counts = counts

        if not counts:
            result.message = "لم يصوت أحد اليوم!"
            return result

        mv = max(counts.values())
        top = [t for t, c in counts.items() if c == mv]

        if len(top) > 1:
            result.tie = True
            result.eliminated = random.choice(top)
            result.message += (
                f"⚖️ تعادل! {self.players[result.eliminated].name} أُخرج عشوائياً."
            )
        else:
            result.eliminated = top[0]
            result.message += f"🚨 {self.players[result.eliminated].name} خرج بأعلى الأصوات!"

        if result.eliminated:
            self.players[result.eliminated].alive = False

        for p in self.players.values():
            p.vote_target = None

        return result

    # ─── Win Condition ────────────────────────────────────────────────────

    def check_win(self) -> Optional[str]:
        """
        Check if either team has won.
        Returns 'wolf', 'village', or None (game continues).

        • Wolves win when living_wolves ≥ (total_living - living_wolves)
        • Village wins when living_wolves == 0
        """
        alive = self.living_ids
        wolves = sum(1 for p in alive if self.players[p].role == "wolf")
        villagers = len(alive) - wolves

        if wolves == 0:
            return "village"
        if wolves >= villagers:
            return "wolf"
        return None

    def reset_night_state(self):
        """Call at the end of each day before the next night."""
        self.wolf_votes.clear()
        self.night_actions_done.clear()
