const {
  EmbedBuilder,
  ActionRowBuilder,
  StringSelectMenuBuilder,
  ButtonBuilder,
  ButtonStyle,
} = require('discord.js');

const NEON_CYAN = 0x00D4FF;
const NEON_PURPLE = 0xBB86FC;
const RED = 0xE74C3C;
const GREEN = 0x2ECC71;
const GOLD = 0xF1C40F;
const DARK = 0x0D1117;

class ControlPanel {
  constructor(session, player) {
    this.session = session;
    this.player = player;
    this.role = player.role;
    this.phase = session.fsm?.getState() || 'unknown';
    this.alive = player.alive;
  }

  build() {
    if (!this.alive) return this._deadPanel();
    switch (this.phase) {
      case 'lobby': return this._lobbyPanel();
      case 'starting': return this._startingPanel();
      case 'night': return this._nightPanel();
      case 'process_night': return this._waitPanel('🌙', 'جاري معالجة إجراءات الليل...');
      case 'day': return this._dayPanel();
      case 'voting': return this._votingPanel();
      case 'process_votes': return this._waitPanel('⚖️', 'جاري فرز الأصوات...');
      case 'check_win': return this._waitPanel('🏆', 'جاري التحقق من شروط الفوز...');
      default: return this._defaultPanel();
    }
  }

  _baseEmbed(description, color = NEON_CYAN) {
    const info = this.role ? this.role.getInfo() : null;
    const status = this.alive ? '🟢 **على قيد الحياة**' : '💀 **ميت**';
    const phaseMap = {
      lobby: '🛡️ صالة انتظار', starting: '📜 توزيع أدوار', night: '🌙 ليل',
      process_night: '🌙 معالجة الليل', day: '☀️ نهار', voting: '🗳️ تصويت',
      process_votes: '⚖️ فرز الأصوات', check_win: '🏆 فحص الفوز', ended: '🏁 انتهت',
    };

    return new EmbedBuilder()
      .setColor(color)
      .setTitle(info ? `${info.emoji} لوحة التحكم — ${info.name}` : '👤 لوحة التحكم')
      .setDescription([
        '```yaml',
        `الحالة     : ${status.split(' ')[0]}`,
        `الطور      : ${phaseMap[this.phase] || this.phase}`,
        info ? `الدور      : ${info.name}` : '',
        info ? `الفريق     : ${info.team}` : '',
        info ? `الوصف      : ${info.description}` : '',
        '```',
        '',
        description,
      ].filter(l => l).join('\n'))
      .setFooter({ text: `Vale Community • ${this.phase}` })
      .setTimestamp();
  }

  _lobbyPanel() {
    const players = this.session.players;
    const list = players.map((p, i) => {
      const host = p.id === this.session.hostId ? '👑' : '';
      return `\`#${String(i + 1).padStart(2, '0')}\` ${host} <@${p.id}>`;
    }).join('\n');

    return {
      embeds: [
        this._baseEmbed(
          `🛡️ **أنت في صالة الانتظار**\n👥 **اللاعبون:** ${players.length}/16\n━━━━━━━━━━━━━━━━\n${list || '_القائمة فارغة_'}`,
          NEON_CYAN,
        ),
      ],
      components: [
        new ActionRowBuilder().addComponents(
          new ButtonBuilder()
            .setCustomId(`panel_leave_${this.player.id}`)
            .setLabel('❌ مغادرة اللعبة')
            .setStyle(ButtonStyle.Danger),
        ),
      ],
    };
  }

  _startingPanel() {
    return {
      embeds: [this._baseEmbed('📜 **جاري توزيع الأدوار...**\n_انتظر قليلاً..._', NEON_PURPLE)],
      components: [],
    };
  }

  _nightPanel() {
    if (!this.role || !this.alive) return this._deadPanel();

    const controls = this._buildNightControls();
    const usedAbilities = this._getUsedAbilities();

    let desc = '🌙 **حل الليل على القرية.**\n';
    if (usedAbilities.length > 0) {
      desc += `\n📊 **حالة قدراتك:**\n${usedAbilities.map(a => `${a.emoji} **${a.name}:** ${a.used ? '❌ مستخدمة' : '✅ متاحة'}`).join('\n')}`;
    }
    if (controls.length === 0) {
      desc += '\n\n💤 _ليس لديك قدرة ليلية._\n_انتظر حتى الصباح._';
    }

    return {
      embeds: [this._baseEmbed(desc, NEON_PURPLE)],
      components: controls,
    };
  }

  _waitPanel(emoji, message) {
    return {
      embeds: [this._baseEmbed(`${emoji} ${message}\n_انتظر قليلاً..._`, GOLD)],
      components: [],
    };
  }

  _dayPanel() {
    let desc = '☀️ **مرحلة المناقشة.**\n_ناقش مع الآخرين وحاول اكتشاف الذئاب._\n\n';
    const alive = this.session.getAlivePlayers();
    desc += `👥 **الأحياء (${alive.length}):**\n${alive.map(p => `<@${p.id}>`).join(', ')}`;

    if (this.player.votedFor) {
      desc += `\n\n🗳️ **صوتك:** <@${this.player.votedFor}>`;
    }

    if (this.role) {
      if (this.role.id === 'King') {
        const canExec = !this.role.hasExecuted;
        desc += `\n👑 **صلاحية الإعدام:** ${canExec ? '✅ متاحة — استخدم \`/إعدام\`' : '❌ مستخدمة'}`;
      }
      if (this.role.id === 'Mayor') {
        desc += `\n🏛️ **وزن صوتك:** 2`;
      }
    }

    return {
      embeds: [this._baseEmbed(desc, GOLD)],
      components: [],
    };
  }

  _votingPanel() {
    const alive = this.session.getAlivePlayers();
    const hasVoted = this.player.votedFor !== null;

    let desc = '🗳️ **مرحلة التصويت.**\n';
    desc += hasVoted
      ? `✅ **لقد صوّت.**\n🗳️ **صوتك:** <@${this.player.votedFor}>`
      : '⏳ **لم تصوّت بعد.**\n_استخدم التصويت العام في القناة._';

    return {
      embeds: [this._baseEmbed(desc, GOLD)],
      components: [],
    };
  }

  _deadPanel() {
    const info = this.role ? this.role.getInfo() : null;
    const roleReveal = info
      ? `📜 **دورك كان:** ${info.emoji} **${info.name}**\n👥 **فريقك:** ${info.team}`
      : '❌ لا تعرف دورك بعد.';

    return {
      embeds: [
        new EmbedBuilder()
          .setColor(RED)
          .setTitle('💀 أنت ميت')
          .setDescription([
            '```yaml',
            `الحالة: ميت`,
            `الطور : ${this.phase}`,
            '```',
            '',
            roleReveal,
            '',
            '_يمكنك مشاهدة باقي اللعبة._',
          ].join('\n'))
          .setFooter({ text: 'Vale Community • أنت متفرج الآن' })
          .setTimestamp(),
      ],
      components: [],
    };
  }

  _defaultPanel() {
    return {
      embeds: [this._baseEmbed('👤 مرحباً بك في لوحة التحكم.', DARK)],
      components: [],
    };
  }

  _buildNightControls() {
    if (!this.role || !this.alive) return [];

    const rows = [];
    const alive = this.session.getAlivePlayers();
    const roleName = this.role.name;

    const makeSelect = (customId, placeholder, options) =>
      new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
          .setCustomId(`${customId}_${this.player.id}`)
          .setPlaceholder(placeholder)
          .addOptions(options),
      );

    switch (roleName) {
      case 'ذئب': {
        const targets = alive.filter(p => p.id !== this.player.id);
        if (targets.length > 0) {
          rows.push(makeSelect('wolf_kill', '🐺 اختر ضحية...', targets.map(t => ({
            label: t.username, value: t.id, emoji: '🎯',
          }))));
        }
        break;
      }
      case 'محقق': {
        if (this.role.uses < this.role.maxUses) {
          const targets = alive.filter(p => p.id !== this.player.id);
          if (targets.length > 0) {
            rows.push(makeSelect('detective_investigate', '🔍 اختر لاعباً للتحقيق...', targets.map(t => ({
              label: t.username, value: t.id, emoji: '🔍',
            }))));
          }
        }
        break;
      }
      case 'طبيب': {
        rows.push(makeSelect('doctor_heal', '💉 اختر من تنقذ...', [
          { label: '⏭️ تخطي', value: 'skip', emoji: '⏭️' },
          ...alive.map(t => ({ label: t.username, value: t.id, emoji: '💊' })),
        ]));
        break;
      }
      case 'حارس': {
        if (this.role.uses < this.role.maxUses) {
          const targets = alive.filter(p => p.id !== this.player.id);
          if (targets.length > 0) {
            rows.push(makeSelect('guard_protect', '🛡️ اختر من تحمي...', targets.map(t => ({
              label: t.username, value: t.id, emoji: '🛡️',
            }))));
          }
        }
        break;
      }
      case 'مغوية': {
        const targets = alive.filter(p => p.id !== this.player.id);
        if (targets.length > 0) {
          rows.push(makeSelect('seductress_visit', '💃 اختر من تزورين...', targets.map(t => ({
            label: t.username, value: t.id, emoji: '💃',
          }))));
        }
        break;
      }
    }
    return rows;
  }

  _getUsedAbilities() {
    if (!this.role) return [];
    const role = this.role;
    const abilities = [];

    abilities.push({ emoji: role.emoji, name: role.name, used: false });

    if (role.maxUses && role.maxUses > 0) {
      abilities.push({ emoji: '🔋', name: 'قدرة خاصة', used: role.uses >= role.maxUses });
    }

    return abilities;
  }

  static async validateAccess(session, userId) {
    if (!session) return { allowed: false, reason: 'لا توجد جلسة نشطة.' };
    const player = session.players.find(p => p.id === userId);
    if (!player) return { allowed: false, reason: 'أنت لست في هذه اللعبة.' };
    return { allowed: true, player };
  }
}

module.exports = ControlPanel;
