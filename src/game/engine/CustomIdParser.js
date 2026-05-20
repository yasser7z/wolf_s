/**
 * Parse structured customId strings like:
 *   night:wolf:kill:123456789
 *   vote:cast:123456789
 *   king:execute:menu
 */

class CustomIdParser {
  /**
   * Parse a customId into structured parts.
   * @returns {{ namespace, role, action, targetId, raw }}
   */
  static parse(customId) {
    if (!customId) return null;
    const parts = customId.split(':');
    const raw = customId;

    if (parts.length < 2) return { namespace: parts[0], role: null, action: null, targetId: null, raw };

    const namespace = parts[0];
    const role = parts.length >= 3 ? parts[1] : null;
    const action = parts.length >= 3 ? parts[2] : parts[1];
    const targetId = parts.length >= 4 ? parts.slice(3).join(':') : null;

    return { namespace, role, action, targetId, raw };
  }

  static build(namespace, role, action, targetId) {
    const parts = [namespace];
    if (role) parts.push(role);
    if (action) parts.push(action);
    if (targetId) parts.push(targetId);
    return parts.join(':');
  }

  static isNightAction(id) { return id.startsWith('night:'); }
  static isVoteAction(id) { return id.startsWith('vote:'); }
  static isKingAction(id) { return id.startsWith('king:'); }
  static isPanelAction(id) { return id.startsWith('panel:'); }
  static isLobbyAction(id) { return id.startsWith('lobby:'); }
}

module.exports = CustomIdParser;
