const { Collection } = require('discord.js');
const fs = require('fs');
const path = require('path');
const CooldownManager = require('../game/systems/CooldownManager');
const logger = require('../utils/logger');

let cooldowns = null;

function initCooldowns() {
  cooldowns = new CooldownManager({ defaultCooldown: 2000 });
  return cooldowns;
}

async function loadPrefixCommands(client) {
  client.prefixCommands = new Collection();
  const commandsPath = path.join(__dirname, '../commands/prefix');
  const files = fs.readdirSync(commandsPath).filter(f => f.endsWith('.js'));

  for (const file of files) {
    try {
      const cmd = require(path.join(commandsPath, file));
      if (cmd.name) {
        client.prefixCommands.set(cmd.name, cmd);
        if (cmd.aliases) {
          cmd.aliases.forEach(a => client.prefixCommands.set(a, cmd));
        }
        logger.info(`📝 بريفكس: ${cmd.name}`);
      }
    } catch (err) {
      logger.error(`❌ فشل تحميل ${file}:`, err.message);
    }
  }

  logger.success(`✅ ${client.prefixCommands.size} أمر بريفكس`);
}

async function loadSlashCommands(client) {
  client.slashCommands = new Collection();
  const commandsPath = path.join(__dirname, '../commands/slash');
  const files = fs.readdirSync(commandsPath).filter(f => f.endsWith('.js'));

  for (const file of files) {
    try {
      const cmd = require(path.join(commandsPath, file));
      if (cmd.data?.name) {
        client.slashCommands.set(cmd.data.name, cmd);
        logger.info(`📝 سلاش: ${cmd.data.name}`);
      }
    } catch (err) {
      logger.error(`❌ فشل تحميل ${file}:`, err.message);
    }
  }

  logger.success(`✅ ${client.slashCommands.size} أمر سلاش`);
}

async function registerSlashCommands(client) {
  const commands = client.slashCommands.map(c => c.data);
  if (!commands.length) return;

  try {
    if (process.env.GUILD_ID) {
      const guild = client.guilds.cache.get(process.env.GUILD_ID);
      if (guild) {
        await guild.commands.set(commands);
        logger.success(`✅ ${commands.length} أمر سلاش في ${guild.name}`);
      }
    } else {
      await client.application.commands.set(commands);
      logger.success(`✅ ${commands.length} أمر سلاش عالمياً`);
    }
  } catch (err) {
    logger.error('❌ فشل تسجيل السلاش:', err.message);
  }
}

function handlePrefixCommand(message, client, sessionManager) {
  const prefix = '-';
  if (!message.content.startsWith(prefix)) return;

  const args = message.content.slice(prefix.length).trim().split(/ +/);
  const cmdName = args.shift()?.toLowerCase();
  if (!cmdName) return;

  const cmd = client.prefixCommands.get(cmdName);
  if (!cmd) return;

  if (cooldowns) {
    const result = cooldowns.consume(message.author.id, `prefix:${cmdName}`, cmd.cooldown || 2000);
    if (!result.allowed) return;
  }

  cmd.execute(message, args, client, sessionManager).catch(err => {
    logger.error(`❌ أمر ${cmdName}:`, err.message);
    message.reply('❌ حدث خطأ').catch(() => {});
  });
}

async function handleSlashCommand(interaction, client, sessionManager) {
  const cmd = client.slashCommands.get(interaction.commandName);
  if (!cmd) {
    return interaction.reply({ content: '❌ الأمر غير موجود.', ephemeral: true });
  }

  cmd.execute(interaction, client, sessionManager).catch(async (err) => {
    logger.error(`❌ سلاش ${interaction.commandName}:`, err.message);
    const reply = { content: '❌ حدث خطأ.', ephemeral: true };
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp(reply);
    } else {
      await interaction.reply(reply);
    }
  });
}

module.exports = {
  loadPrefixCommands,
  loadSlashCommands,
  registerSlashCommands,
  handlePrefixCommand,
  handleSlashCommand,
  initCooldowns,
};
