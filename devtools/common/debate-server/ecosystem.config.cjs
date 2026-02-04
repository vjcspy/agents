/**
 * pm2 ecosystem config for debate services.
 * 
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 stop debate-server debate-web
 *   pm2 delete debate-server debate-web
 *   pm2 logs
 */

const path = require('path');

module.exports = {
  apps: [
    {
      name: 'debate-server',
      cwd: __dirname,
      script: 'pnpm',
      args: 'start',
      interpreter: 'none', // Required for pnpm
      env: {
        NODE_ENV: 'production',
        DEBATE_SERVER_PORT: 3456,
      },
      autorestart: true,
      max_restarts: 3,
      restart_delay: 1000,
      watch: false,
    },
    {
      name: 'debate-web',
      cwd: path.join(__dirname, '../debate-web'),
      script: 'pnpm',
      args: 'start',
      interpreter: 'none', // Required for pnpm
      env: {
        NODE_ENV: 'production',
        PORT: 3457,
        NEXT_PUBLIC_DEBATE_SERVER_URL: 'http://127.0.0.1:3456',
      },
      autorestart: true,
      max_restarts: 3,
      restart_delay: 1000,
      watch: false,
    },
  ],
};
