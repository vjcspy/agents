/**
 * pm2 ecosystem config for all devtools services.
 *
 * Usage:
 *   pm2 start ecosystem.config.cjs
 *   pm2 stop all
 *   pm2 restart aweave-server
 *   pm2 logs
 *   pm2 delete all
 */

const path = require('path');

module.exports = {
  apps: [
    {
      name: 'aweave-server',
      cwd: path.join(__dirname, 'common/server'),
      script: 'dist/main.js',
      env: {
        NODE_ENV: 'production',
        SERVER_PORT: 3456,
        SERVER_HOST: '127.0.0.1',
      },
      autorestart: true,
      max_restarts: 5,
      restart_delay: 1000,
      watch: false,
    },
    {
      name: 'debate-web',
      cwd: path.join(__dirname, 'common/debate-web'),
      script: 'node_modules/next/dist/bin/next',
      args: 'start --port 3457',
      env: {
        NODE_ENV: 'production',
        PORT: 3457,
        NEXT_PUBLIC_DEBATE_SERVER_URL: 'http://127.0.0.1:3456',
      },
      autorestart: true,
      max_restarts: 5,
      restart_delay: 1000,
      watch: false,
    },
  ],
};
