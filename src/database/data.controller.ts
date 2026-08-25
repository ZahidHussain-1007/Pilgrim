import { Body, Controller, Delete, Get, Param, Post, Req, UnauthorizedException } from '@nestjs/common';
import { IsIn, IsInt, IsOptional, IsString, IsUUID, Max, MaxLength, Min } from 'class-validator';
import { AuthService, SessionUser } from '../auth/auth.service';
import { DataService } from './data.service';

class ConversationDto {
  @IsOptional() @IsString() @MaxLength(200) title?: string;
  @IsIn(['en', 'te', 'hi']) language!: 'en' | 'te' | 'hi';
}

class FavoriteDto {
  @IsIn(['temple', 'hotel', 'restaurant', 'emergency', 'travel']) itemType!: string;
  @IsString() @MaxLength(500) itemKey!: string;
  itemData!: unknown;
}

class FeedbackDto {
  @IsUUID() messageId!: string;
  @IsInt() @Min(1) @Max(5) rating!: number;
  @IsOptional() @IsString() @MaxLength(5000) comment?: string;
}

@Controller('api')
export class DataController {
  constructor(private readonly data: DataService, private readonly auth: AuthService) {}

  private session(request: { cookies?: Record<string, string> }): SessionUser {
    const session = this.auth.readSession(request.cookies?.pilgrim_session);
    if (!session) throw new UnauthorizedException('Sign in required.');
    return session;
  }

  @Get('profile') profile(@Req() request: { cookies?: Record<string, string> }) { return this.data.getProfile(this.session(request)); }
  @Get('conversations') conversations(@Req() request: { cookies?: Record<string, string> }) { return this.data.listConversations(this.session(request)); }
  @Post('conversations') createConversation(@Req() request: { cookies?: Record<string, string> }, @Body() body: ConversationDto) { return this.data.createConversation(this.session(request), body); }
  @Get('conversations/:id/messages') messages(@Req() request: { cookies?: Record<string, string> }, @Param('id') id: string) { return this.data.getMessages(this.session(request), id); }
  @Delete('conversations/:id') deleteConversation(@Req() request: { cookies?: Record<string, string> }, @Param('id') id: string) { return this.data.deleteConversation(this.session(request), id); }
  @Get('favorites') favorites(@Req() request: { cookies?: Record<string, string> }) { return this.data.listFavorites(this.session(request)); }
  @Post('favorites') addFavorite(@Req() request: { cookies?: Record<string, string> }, @Body() body: FavoriteDto) { return this.data.addFavorite(this.session(request), body); }
  @Delete('favorites/:itemType/:itemKey') removeFavorite(@Req() request: { cookies?: Record<string, string> }, @Param('itemType') itemType: string, @Param('itemKey') itemKey: string) { return this.data.removeFavorite(this.session(request), itemType, itemKey); }
  @Post('feedback') feedback(@Req() request: { cookies?: Record<string, string> }, @Body() body: FeedbackDto) { return this.data.submitFeedback(this.session(request), body.messageId, body.rating, body.comment); }
}