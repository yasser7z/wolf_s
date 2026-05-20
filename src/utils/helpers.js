function formatTime(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function shuffle(array) {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getRoleEmoji(roleName) {
  const emojis = {
    'مدني': '👤',
    'ذئب': '🐺',
    'عراف': '🔮',
    'طبيب': '💉',
    'جاسوس': '🕵️',
    'مشعوذة': '🧙',
    'صياد': '🏹',
    'حارس': '🛡️',
    'محقق': '🔍',
  };
  return emojis[roleName] || '❓';
}

module.exports = { formatTime, shuffle, randomItem, sleep, getRoleEmoji };
