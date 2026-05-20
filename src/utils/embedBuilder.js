const { EmbedBuilder } = require('discord.js');

const COLORS = {
  PRIMARY: 0x9B59B6,
  SUCCESS: 0x2ECC71,
  ERROR: 0xE74C3C,
  WARN: 0xF39C12,
  NIGHT: 0x2C3E50,
  DAY: 0xF1C40F,
  LOBBY: 0x3498DB,
};

function createEmbed(options = {}) {
  const embed = new EmbedBuilder()
    .setColor(options.color || COLORS.PRIMARY)
    .setTimestamp();

  if (options.title) embed.setTitle(options.title);
  if (options.description) embed.setDescription(options.description);
  if (options.footer) embed.setFooter({ text: options.footer });
  if (options.author) embed.setAuthor(options.author);
  if (options.thumbnail) embed.setThumbnail(options.thumbnail);
  if (options.image) embed.setImage(options.image);
  if (options.fields) embed.addFields(options.fields);

  return embed;
}

function gameEmbed(title, description, color = COLORS.PRIMARY) {
  return createEmbed({
    title: `🎮 ${title}`,
    description,
    color,
    footer: 'Vale Community',
  });
}

function errorEmbed(description) {
  return createEmbed({
    title: '❌ خطأ',
    description,
    color: COLORS.ERROR,
    footer: 'Vale Community',
  });
}

function successEmbed(description) {
  return createEmbed({
    title: '✅ تم بنجاح',
    description,
    color: COLORS.SUCCESS,
    footer: 'Vale Community',
  });
}

module.exports = { createEmbed, gameEmbed, errorEmbed, successEmbed, COLORS };
