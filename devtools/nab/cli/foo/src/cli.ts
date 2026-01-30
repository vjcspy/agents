#!/usr/bin/env node
import { Command } from 'commander';

const program = new Command();

program
  .name('foo')
  .description('Foo build and deployment tools')
  .version('0.1.0');

program
  .command('build')
  .description('Build the project')
  .option('-w, --watch', 'Watch mode')
  .option('-p, --production', 'Production build')
  .action((options) => {
    console.log('Building project...');
    if (options.watch) {
      console.log('  Mode: watch');
    }
    if (options.production) {
      console.log('  Mode: production');
    }
    console.log('Build complete!');
  });

program
  .command('deploy')
  .description('Deploy to an environment')
  .argument('<env>', 'Target environment (dev, staging, prod)')
  .option('-f, --force', 'Force deployment')
  .action((env, options) => {
    console.log(`Deploying to ${env}...`);
    if (options.force) {
      console.log('  Force mode enabled');
    }
    console.log('Deployment complete!');
  });

program
  .command('status')
  .description('Show deployment status')
  .action(() => {
    console.log('Foo Status');
    console.log('='.repeat(40));
    console.log('Environment: development');
    console.log('Last deploy: N/A');
    console.log('Version: 0.1.0');
  });

program.parse();
