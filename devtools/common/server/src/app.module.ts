import { Module } from '@nestjs/common';
import { DebateModule } from '@aweave/nestjs-debate';

@Module({
  imports: [DebateModule],
})
export class AppModule {}
