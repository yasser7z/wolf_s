class BaseRole {
  constructor(data) {
    this.id = data.id || 'unknown';
    this.name = data.name || 'مجهول';
    this.team = data.team || 'محايد';
    this.description = data.description || 'لا يوجد وصف';
    this.emoji = data.emoji || '❓';
    this.priority = data.priority || 0;
    this.maxUses = data.maxUses || null;
    this.usesLeft = data.maxUses || null;
    this.nightAction = data.nightAction ?? true;
    this.canSelfTarget = data.canSelfTarget ?? false;
    this.visible = data.visible ?? true;

    this._metadata = data.metadata || {};
  }

  canUseAbility() {
    return this.usesLeft === null || this.usesLeft > 0;
  }

  useAbility() {
    if (this.usesLeft !== null && this.usesLeft > 0) {
      this.usesLeft -= 1;
    }
  }

  resetUses() {
    this.usesLeft = this.maxUses;
  }

  getTargets(alivePlayers, allPlayers) {
    return alivePlayers.filter(p => {
      if (p.id === this._owner?.id && !this.canSelfTarget) return false;
      return true;
    });
  }

  onNightAction(actionQueue, player, target) { }
  onDayAction(actionQueue, player, target) { }
  onKilled(killer) { }
  onHealed(healer) { }
  onVote(voter) { }

  setOwner(player) {
    this._owner = player;
  }

  getInfo() {
    return {
      id: this.id,
      name: this.name,
      team: this.team,
      description: this.description,
      emoji: this.emoji,
      priority: this.priority,
      usesLeft: this.usesLeft,
    };
  }

  toJSON() {
    return {
      id: this.id,
      name: this.name,
      team: this.team,
      priority: this.priority,
      usesLeft: this.usesLeft,
    };
  }
}

module.exports = BaseRole;
