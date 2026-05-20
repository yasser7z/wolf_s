class Player {
  constructor(data = {}) {
    this.id = data.id || null;
    this.username = data.username || 'مجهول';
    this.alive = data.alive ?? true;
    this.role = data.role || null;
    this.votedFor = data.votedFor || null;
    this.joinedAt = data.joinedAt || Date.now();
    this.isHost = data.isHost || false;
    this.stats = {
      nightActions: 0,
      votesCast: 0,
      timesSaved: 0,
      timesKilled: 0,
    };
  }

  setRole(role) {
    this.role = role;
    if (role && role.setOwner) {
      role.setOwner(this);
    }
  }

  kill() {
    this.alive = false;
    this.stats.timesKilled += 1;
  }

  save() {
    this.stats.timesSaved += 1;
  }

  vote(targetId) {
    this.votedFor = targetId;
    this.stats.votesCast += 1;
  }

  reset() {
    this.votedFor = null;
  }

  isWolf() {
    return this.role && this.role.name === 'ذئب';
  }

  isVillager() {
    return this.role && this.role.team === 'القرية';
  }

  toJSON() {
    return {
      id: this.id,
      username: this.username,
      alive: this.alive,
      role: this.role ? { name: this.role.name, team: this.role.team } : null,
      votedFor: this.votedFor,
    };
  }
}

module.exports = Player;
