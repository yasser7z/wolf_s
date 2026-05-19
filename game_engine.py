import random
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from config import ROLE_INFO, SPECIAL_ROLES


class GameState(Enum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    GAME_OVER = "game_over"


class PlayerData:
    __slots__ = ('id', 'name', 'role', 'alive', 'detective_used', 'guardian_used',
                 'king_used', 'doctor_target', 'seductress_target', 'vote_target',
                 'wolf_vote', 'detective_target', 'guardian_target', 'king_flip_target')

    def __init__(self, member_id: int, name: str):
        self.id = member_id
        self.name = name
        self.role: Optional[str] = None
        self.alive = True
        self.detective_used = False
        self.guardian_used = False
        self.king_used = False
        self.doctor_target: Optional[int] = None
        self.seductress_target: Optional[int] = None
        self.vote_target: Optional[int] = None
        self.wolf_vote: Optional[int] = None
        self.detective_target: Optional[int] = None
        self.guardian_target: Optional[int] = None
        self.king_flip_target: Optional[int] = None


class NightResult:
    def __init__(self):
        self.killed: List[int] = []
        self.detective_result: Optional[Tuple[int, int, bool]] = None
        self.exposed_wolf: Optional[int] = None
        self.message: str = ""


class VoteResult:
    def __init__(self):
        self.eliminated: Optional[int] = None
        self.vote_counts: Dict[int, int] = {}
        self.message: str = ""
        self.tie: bool = False


class GameEngine:
    def __init__(self):
        self.state = GameState.LOBBY
        self.players: Dict[int, PlayerData] = {}
        self.order: List[int] = []
        self.day_number = 0
        self.wolf_votes: Dict[int, int] = {}
        self.night_actions_done: Set[int] = set()

    @property
    def living_ids(self) -> List[int]:
        return [pid for pid in self.order if self.players[pid].alive]

    @property
    def dead_ids(self) -> List[int]:
        return [pid for pid in self.order if not self.players[pid].alive]

    @property
    def living_wolves(self) -> List[int]:
        return [pid for pid in self.living_ids if self.players[pid].role == "wolf"]

    def add_player(self, member_id: int, name: str) -> bool:
        if member_id in self.players:
            return False
        if len(self.players) >= 20:
            return False
        self.players[member_id] = PlayerData(member_id, name)
        self.order.append(member_id)
        return True

    def remove_player(self, member_id: int) -> bool:
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

    def assign_roles(self) -> bool:
        n = self.player_count()
        if n < 6:
            return False

        ids = list(self.players.keys())
        random.shuffle(ids)

        if n <= 7:
            num_wolves = 1
        elif n <= 10:
            num_wolves = 2
        else:
            num_wolves = 3

        num_special = min(len(SPECIAL_ROLES), n - num_wolves)
        roles = ["wolf"] * num_wolves
        selected = random.sample(SPECIAL_ROLES, num_special)
        roles.extend(selected)

        remaining = n - len(roles)
        roles.extend(["villager"] * remaining)
        random.shuffle(roles)

        for pid, role_name in zip(ids, roles):
            self.players[pid].role = role_name

        self.order = ids
        return True

    def get_night_action_players(self) -> List[int]:
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
        required = set(self.get_night_action_players())
        return required.issubset(self.night_actions_done)

    def complete_night_action(self, member_id: int):
        self.night_actions_done.add(member_id)

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

    def resolve_night(self) -> NightResult:
        result = NightResult()

        # Wolf kill target
        kill_target = None
        if self.wolf_votes:
            counts = {}
            for wid, tid in self.wolf_votes.items():
                if wid in self.living_ids:
                    counts[tid] = counts.get(tid, 0) + 1
            if counts:
                mv = max(counts.values())
                top = [t for t, c in counts.items() if c == mv]
                kill_target = random.choice(top)

        # IDs by role
        sed_id = next((p for p in self.living_ids if self.players[p].role == "seductress"), None)
        doc_id = next((p for p in self.living_ids if self.players[p].role == "doctor"), None)
        gua_id = next((p for p in self.living_ids if self.players[p].role == "guardian" and not self.players[p].guardian_used), None)

        sed_tgt = self.players[sed_id].seductress_target if sed_id else None
        doc_tgt = self.players[doc_id].doctor_target if doc_id else None
        gua_tgt = self.players[gua_id].guardian_target if gua_id else None

        # Seductress check
        if sed_id and sed_tgt and sed_tgt in self.living_ids:
            if self.players[sed_tgt].role == "wolf":
                result.killed.extend([sed_id, sed_tgt])
                result.message += f"💃 {self.players[sed_id].name} اختارت ذئباً وماتت معه!\n"
                if kill_target == sed_tgt:
                    kill_target = None
            elif kill_target == sed_tgt:
                result.killed.append(sed_id)
                result.message += f"💃 {self.players[sed_id].name} ضحت بنفسها لتحمي {self.players[sed_tgt].name}!\n"
                kill_target = None

        # Doctor
        if kill_target and doc_tgt == kill_target:
            result.message += f"⚕️ الطبيب أنقذ {self.players[kill_target].name}!\n"
            kill_target = None

        # Guardian
        if kill_target and gua_tgt == kill_target:
            result.message += f"🛡️ الحارس حمى {self.players[kill_target].name}!\n"
            if gua_id:
                self.players[gua_id].guardian_used = True
            kill_target = None

        # Apply wolf kill
        if kill_target and kill_target not in result.killed:
            result.killed.append(kill_target)

        # Um Fadi check
        um_id = next((p for p in self.order if self.players[p].role == "um_fadi" and self.players[p].alive), None)
        if um_id and um_id in result.killed:
            living_wolves = [w for w in self.living_wolves if w != um_id]
            if living_wolves:
                exposed = random.choice(living_wolves)
                result.exposed_wolf = exposed
                result.message += f"👵 أم فادي فضحت {self.players[exposed].name} 🐺!\n"

        # Execute kills
        for tid in result.killed:
            if tid in self.players:
                self.players[tid].alive = False

        # Detective
        det_id = next((p for p in self.living_ids if self.players[p].role == "detective" and not self.players[p].detective_used and self.players[p].detective_target), None)
        if det_id:
            tgt = self.players[det_id].detective_target
            self.players[det_id].detective_used = True
            result.detective_result = (det_id, tgt, self.players[tgt].role == "wolf")

        self.wolf_votes.clear()
        self.night_actions_done.clear()

        for pid in self.living_ids:
            p = self.players[pid]
            if p.role != "doctor":
                p.doctor_target = None
            if p.role != "seductress":
                p.seductress_target = None

        return result

    def set_vote(self, voter_id: int, target_id: int):
        self.players[voter_id].vote_target = target_id

    def set_king_flip(self, king_id: int, target_id: int):
        self.players[king_id].king_flip_target = target_id
        self.players[king_id].king_used = True

    def resolve_voting(self) -> VoteResult:
        result = VoteResult()
        counts = {}

        for pid in self.living_ids:
            p = self.players[pid]
            if p.vote_target and p.vote_target in self.living_ids:
                weight = 2 if p.role == "mayor" else 1
                counts[p.vote_target] = counts.get(p.vote_target, 0) + weight

        # King flip
        king = next((p for p in [self.players[pid] for pid in self.living_ids] if p.role == "king" and p.king_used and p.king_flip_target), None)
        if king and king.king_flip_target in self.living_ids:
            total = sum(counts.values()) if counts else len([p for p in self.living_ids if self.players[p].vote_target])
            counts = {king.king_flip_target: total}
            result.message += f"👑 {king.name} استخدم سلطته وقلب الأصوات على {self.players[king.king_flip_target].name}!\n"

        result.vote_counts = counts

        if not counts:
            result.message = "لم يصوت أحد اليوم!"
            return result

        mv = max(counts.values())
        top = [t for t, c in counts.items() if c == mv]

        if len(top) > 1:
            result.tie = True
            result.eliminated = random.choice(top)
            result.message += f"⚖️ تعادل! {self.players[result.eliminated].name} أُخرج عشوائياً."
        else:
            result.eliminated = top[0]
            result.message += f"🚨 {self.players[result.eliminated].name} خرج بأعلى الأصوات!"

        if result.eliminated:
            self.players[result.eliminated].alive = False

        for p in self.players.values():
            p.vote_target = None

        return result

    def check_win(self) -> Optional[str]:
        alive = self.living_ids
        wolves = sum(1 for p in alive if self.players[p].role == "wolf")
        villagers = len(alive) - wolves
        if wolves == 0:
            return "village"
        if wolves >= villagers:
            return "wolf"
        return None

    def reset_night_state(self):
        self.wolf_votes.clear()
        self.night_actions_done.clear()
