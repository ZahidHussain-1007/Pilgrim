import { Body, Controller, Post, Req, UnauthorizedException } from '@nestjs/common';
import { IsIn, IsOptional, IsString, IsUUID, MaxLength } from 'class-validator';
import { ChatService } from './chat.service';
import { AuthService } from '../auth/auth.service';

class ChatRequestDto {
  @IsString()
  @MaxLength(2000)
  query!: string;

  @IsOptional()
  @IsString()
  temple?: string | null;

  @IsOptional()
  @IsUUID()
  conversationId?: string;

  @IsIn(['en', 'te', 'hi'])
  language!: 'en' | 'te' | 'hi';
}

@Controller('api')
export class ChatController {
  constructor(private readonly chat: ChatService, private readonly auth: AuthService) {}

  @Post('chat')
  async ask(@Body() body: ChatRequestDto, @Req() request: { cookies?: Record<string, string> }) {
    console.log('--- DIAGNOSTIC: CONTROLLER HIT ---');
    console.log('Received Body:', JSON.stringify(body));
    const session = this.auth.readSession(request.cookies?.pilgrim_session);
    console.log('Session decoded:', session ? 'Valid' : 'None');
    if (!session) throw new UnauthorizedException('Sign in required to save chat history.');
    const profile = await this.auth.getProfile(session.googleId);
    console.log('Profile User ID:', profile.id);
    const { conversationId, ...payload } = body;
    return this.chat.ask(payload, profile.id, conversationId);
  }
}
