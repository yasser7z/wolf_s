import random
from config import ROLES, MIN_PLAYERS, MAX_PLAYERS


class PlayerData:
    def __init__(self, member_id, display_name):
        self.member_id = member_id
        self.display_name = display_name
        self.role_name = None
        self.alive = True
        self.protected = False
        self.night_action_target = None
        self.vote_target = None
        self.used_ability = False
        self.dm_failed = False


class WerewolfGame:
    def __init__(self, channel_id, creator_id):
        self.channel_id = channel_id
        self.creator_id = creator_id
        self.players = {}
        self.player_order = []
        self.phase = "lobby"
        self.day_number = 0
        self.votes = {}
        self.wolf_target = None
        self.doctor_target = None
        self.seductress_target = None
        self.detective_target = None
        self.guard_target = None
        self.king_target = None
        self.last_victim = None
        self.exposed_wolf = None
        self.night_deaths = []
        self.seductress_dead = False
        self.wolf_killed_by_seductress = False
        self.king_day_used = False
        self.lobby_message_id = None
        self.game_message_id = None
        self.timer_task = None
        self.game_over = False
        self.night_action_players = {}
        self.voted_players = set()

    def add_player(self, member_id, display_name):
        if member_id in self.players:
            return False
        if len(self.players) >= MAX_PLAYERS:
            return False
        self.players[member_id] = PlayerData(member_id, display_name)
        self.player_order.append(member_id)
        return True

    def remove_player(self, member_id):
        if member_id not in self.players:
            return False
        if self.phase != "lobby":
            return False
        self.players.pop(member_id, None)
        if member_id in self.player_order:
            self.player_order.remove(member_id)
        return True

    def get_alive_players(self):
        return {mid: p for mid, p in self.players.items() if p.alive}

    def get_alive_players_list(self):
        return [p for p in self.players.values() if p.alive]

    def get_dead_players(self):
        return {mid: p for mid, p in self.players.items() if not p.alive}

    def get_wolves(self):
        return {mid: p for mid, p in self.players.items() if p.role_name == "wolf" and p.alive}

    def get_all_wolves(self):
        return {mid: p for mid, p in self.players.items() if p.role_name == "wolf"}

    def get_player_by_role(self, role_name):
        for mid, p in self.players.items():
            if p.role_name == role_name and p.alive:
                return p
        return None

    def distribute_roles(self):
        num_players = len(self.players)
        if num_players < MIN_PLAYERS:
            return False

        if num_players <= 8:
            num_wolves = 2
        elif num_players <= 11:
            num_wolves = 3
        else:
            num_wolves = 4

        role_pool = ["wolf"] * num_wolves

        specials = ["detective", "doctor", "seductress", "guard", "king", "mayor", "zeki_mom", "villager"]
        remaining = num_players - len(role_pool)

        for role in specials:
            if remaining > 0:
                role_pool.append(role)
                remaining -= 1

        while remaining > 0:
            role_pool.append("villager")
            remaining -= 1

        random.shuffle(role_pool)

        for i, member_id in enumerate(self.player_order):
            if member_id in self.players:
                self.players[member_id].role_name = role_pool[i]

        return True

    def reset_night_actions(self):
        self.wolf_target = None
        self.doctor_target = None
        self.seductress_target = None
        self.detective_target = None
        self.guard_target = None
        self.last_victim = None
        self.exposed_wolf = None
        self.night_deaths = []
        self.seductress_dead = False
        self.wolf_killed_by_seductress = False

        for p in self.players.values():
            p.protected = False

    def process_night(self):
        self.night_deaths = []
        self.exposed_wolf = None

        guard_player = None
        doctor_player = None
        seductress_player = None

        for p in self.players.values():
            if p.role_name == "seductress" and self.seductress_target:
                seductress_player = p

        wolf_alive = len(self.get_wolves()) > 0

        if self.guard_target:
            player = self.players.get(self.guard_target)
            if player and player.alive:
                player.protected = True

        if self.doctor_target:
            player = self.players.get(self.doctor_target)
            if player and player.alive:
                player.protected = True

        if self.seductress_target and seductress_player and seductress_player.alive:
            target_player = self.players.get(self.seductress_target)
            if target_player and target_player.alive:
                if target_player.role_name == "wolf":
                    seductress_player.alive = False
                    target_player.alive = False
                    self.seductress_dead = True
                    self.wolf_killed_by_seductress = True
                    self.night_deaths.append(seductress_player.member_id)
                    self.night_deaths.append(target_player.member_id)
                elif self.wolf_target and target_player.member_id == self.wolf_target:
                    target_player.protected = True

        if wolf_alive and self.wolf_target and not self.wolf_killed_by_seductress:
            target = self.players.get(self.wolf_target)
            if target and target.alive:
                if not target.protected:
                    target.alive = False
                    self.night_deaths.append(target.member_id)
                    if target.role_name == "zeki_mom":
                        wolves = list(self.get_wolves().keys())
                        if wolves:
                            self.exposed_wolf = random.choice(wolves)

    def process_votes(self):
        vote_count = {}
        voters = {}

        for voter_id, target_id in self.votes.items():
            voter = self.players.get(voter_id)
            if not voter or not voter.alive:
                continue
            target = self.players.get(target_id)
            if not target or not target.alive:
                continue
            weight = 2 if voter.role_name == "mayor" else 1
            vote_count[target_id] = vote_count.get(target_id, 0) + weight
            if target_id not in voters:
                voters[target_id] = []
            voters[target_id].append(voter_id)

        if not vote_count:
            return None, {}

        if self.king_target:
            total = sum(vote_count.values())
            target = self.players.get(self.king_target)
            if target and target.alive:
                vote_count = {self.king_target: total}

        max_votes = max(vote_count.values())
        candidates = [mid for mid, v in vote_count.items() if v == max_votes]

        if len(candidates) != 1:
            return None, vote_count

        eliminated_id = candidates[0]
        return eliminated_id, vote_count

    def check_win(self):
        alive = self.get_alive_players()
        wolves = self.get_wolves()

        if len(wolves) == 0:
            return "village"

        total_alive = len(alive)
        if len(wolves) * 2 >= total_alive + (1 if len(wolves) > 1 else 0):
            if len(wolves) >= total_alive - len(wolves):
                return "wolves"

        if len(wolves) >= total_alive:
            return "wolves"

        return None

    def get_night_action_roles(self):
        action_roles = []
        for role_name, role_data in ROLES.items():
            if role_data["night_action"]:
                action_roles.append(role_name)
        return action_roles

    def get_players_needing_dm(self):
        result = {}
        for mid, p in self.players.items():
            if not p.alive:
                continue
            if p.role_name == "villager" or p.role_name == "mayor" or p.role_name == "zeki_mom":
                continue
            if p.role_name == "king":
                continue
            if p.role_name in ("detective", "guard") and p.used_ability:
                continue
            result[mid] = p
        return result

    def get_player_display_list(self, exclude_id=None):
        result = []
        for mid, p in self.players.items():
            if p.alive and mid != exclude_id:
                result.append(p)
        return result

    def alive_count_str(self):
        alive = self.get_alive_players()
        total = len(self.players)
        return f"{len(alive)}/{total}"

    def cleanup(self):
        self.players.clear()
        self.player_order.clear()
        self.votes.clear()
        self.night_deaths.clear()
        self.phase = "lobby"
        self.day_number = 0
        self.game_over = False
        self.wolf_target = None
        self.doctor_target = None
        self.seductress_target = None
        self.detective_target = None
        self.guard_target = None
        self.king_target = None
        self.last_victim = None
        self.exposed_wolf = None
        self.seductress_dead = False
        self.wolf_killed_by_seductress = False
        self.king_day_used = False
        self.night_action_players = {}
        self.voted_players = set()
