import { NestFactory } from '@nestjs/core';
import { WsAdapter } from '@nestjs/platform-ws';
import { AppModule } from './app.module';
import { AppExceptionFilter } from './shared/filters/app-exception.filter';
import { AuthGuard } from './shared/guards/auth.guard';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // WebSocket adapter (ws library)
  app.useWebSocketAdapter(new WsAdapter(app));

  // CORS for debate-web and other clients
  app.enableCors({
    origin: '*',
    methods: 'GET,POST,DELETE,OPTIONS',
    allowedHeaders: 'Content-Type,Authorization',
  });

  // Global exception filter (formats errors to { success, error } envelope)
  app.useGlobalFilters(new AppExceptionFilter());

  // Global auth guard (optional bearer token)
  app.useGlobalGuards(new AuthGuard());

  const port = parseInt(process.env.SERVER_PORT || '3456', 10);
  const host = process.env.SERVER_HOST || '127.0.0.1';

  await app.listen(port, host);
  console.log(`Server listening on http://${host}:${port}`);
}

bootstrap();
