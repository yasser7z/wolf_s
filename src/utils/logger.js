const chalk = require('chalk');
const moment = require('moment');

const PREFIX = {
  INFO: chalk.blue('[معلومة]'),
  SUCCESS: chalk.green('[نجاح]'),
  WARN: chalk.yellow('[تحذير]'),
  ERROR: chalk.red('[خطأ]'),
  DEBUG: chalk.magenta('[تصحيح]'),
  GAME: chalk.cyan('[لعبة]'),
};

function timestamp() {
  return chalk.gray(moment().format('HH:mm:ss'));
}

function info(...args) {
  console.log(`${timestamp()} ${PREFIX.INFO}`, ...args);
}

function success(...args) {
  console.log(`${timestamp()} ${PREFIX.SUCCESS}`, ...args);
}

function warn(...args) {
  console.log(`${timestamp()} ${PREFIX.WARN}`, ...args);
}

function error(...args) {
  console.log(`${timestamp()} ${PREFIX.ERROR}`, ...args);
}

function debug(...args) {
  if (process.env.NODE_ENV === 'development') {
    console.log(`${timestamp()} ${PREFIX.DEBUG}`, ...args);
  }
}

function game(...args) {
  console.log(`${timestamp()} ${PREFIX.GAME}`, ...args);
}

module.exports = { info, success, warn, error, debug, game };
