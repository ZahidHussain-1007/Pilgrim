import { Controller, Get, Post, Req, Res, UnauthorizedException, UseGuards } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { ConfigService } from '@nestjs/config';
import { Request, Response } from 'express';
import { AuthService, GoogleUser } from './auth.service';

@Controller('auth')
export class AuthController {
  constructor(private readonly auth: AuthService, private readonly config: ConfigService) {}

  @Get('google')
  @UseGuards(AuthGuard('google'))
  googleLogin() {}

  @Get('google/callback')
  @UseGuards(AuthGuard('google'))
  async googleCallback(@Req() request: Request & { user: GoogleUser }, @Res() response: Response) {
    await this.auth.saveGoogleUser(request.user);
    const frontend = this.config.get<string>('FRONTEND_URL') || 'http://localhost:5173';
    response.cookie('pilgrim_session', this.auth.createSession(request.user), {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: 7 * 24 * 60 * 60 * 1000,
    });
    response.redirect(`${frontend}/?login=success`);
  }

  @Get('me')
  me(@Req() request: Request & { cookies?: Record<string, string> }) {
    const user = this.auth.readSession(request.cookies?.pilgrim_session);
    return { user };
  }

  @Get('profile')
  async profile(@Req() request: Request & { cookies?: Record<string, string> }) {
    const session = this.auth.readSession(request.cookies?.pilgrim_session);
    if (!session) throw new UnauthorizedException('Sign in required.');
    return { profile: await this.auth.getProfile(session.googleId) };
  }

  @Post('logout')
  logout(@Res({ passthrough: true }) response: Response) {
    response.clearCookie('pilgrim_session');
    return { ok: true };
  }
}
