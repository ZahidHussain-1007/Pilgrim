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
import { SupabaseService } from './database/supabase.service';
import { DataController } from './database/data.controller';
import { DataService } from './database/data.service';

@Module({
  imports: [ConfigModule.forRoot({
    isGlobal: true,
    envFilePath: ['.env'].map((path) => resolve(process.cwd(), path)).filter(existsSync),
  }), ServeStaticModule.forRoot({ rootPath: join(__dirname, '..', 'public') })],
  controllers: [AuthController, ChatController, DataController],
  providers: [SupabaseService, AuthService, GoogleStrategy, ChatService, DataService],
})
export class AppModule {}
