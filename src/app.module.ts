import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ServeStaticModule } from '@nestjs/serve-static';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { AuthController } from './auth/auth.controller';
import { AuthService } from './auth/auth.service';
import { GoogleStrategy } from './auth/google.strategy';
import { ChatController } from './chat/chat.controller';
import { ChatService } from './chat/chat.service';

@Module({
  imports: [ConfigModule.forRoot({
    isGlobal: true,
    envFilePath: ['.env'].map((path) => resolve(process.cwd(), path)).filter(existsSync),
  }), ServeStaticModule.forRoot({ rootPath: join(__dirname, '..', 'public') })],
  controllers: [AuthController, ChatController],
  providers: [AuthService, GoogleStrategy, ChatService],
})
export class AppModule {}
