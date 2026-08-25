import { Body, Controller, Post } from '@nestjs/common';
import { IsIn, IsOptional, IsString, MaxLength } from 'class-validator';
import { ChatService } from './chat.service';

class ChatRequestDto {
  @IsString()
  @MaxLength(2000)
  query!: string;

  @IsOptional()
  @IsString()
  temple?: string | null;

  @IsIn(['en', 'te', 'hi'])
  language!: 'en' | 'te' | 'hi';
}

@Controller('api')
export class ChatController {
  constructor(private readonly chat: ChatService) {}

  @Post('chat')
  ask(@Body() body: ChatRequestDto) {
    return this.chat.ask(body);
  }
}
