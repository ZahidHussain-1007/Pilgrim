import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { sign, verify } from 'jsonwebtoken';
import { SupabaseService } from '../database/supabase.service';

export type GoogleUser = { googleId: string; email: string; name: string; avatarUrl: string | null };
export type SessionUser = Pick<GoogleUser, 'googleId' | 'email' | 'name'>;

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(private readonly config: ConfigService, private readonly supabase: SupabaseService) {}

  async saveGoogleUser(user: GoogleUser) {
    if (!this.supabase.configured) {
      this.logger.warn('Supabase is not configured; Google profile was not persisted.');
      return;
    }

    const { data: existingProfile, error: lookupError } = await this.supabase.db
      .from('profiles')
      .select('preferred_language')
      .eq('google_id', user.googleId)
      .maybeSingle();
    if (lookupError) {
      this.logger.error(`Unable to look up Google profile ${user.googleId}: ${lookupError.message}`);
      throw lookupError;
    }

    const { error: upsertError } = await this.supabase.db.from('profiles').upsert({
      google_id: user.googleId,
      email: user.email,
      full_name: user.name,
      avatar_url: user.avatarUrl,
      preferred_language: existingProfile?.preferred_language || 'en',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'google_id' });

    if (upsertError) {
      this.logger.error(`Unable to upsert Google profile ${user.googleId}: ${upsertError.message}`);
      throw upsertError;
    }
  }

  createSession(user: GoogleUser) {
    return sign({ googleId: user.googleId, email: user.email, name: user.name }, this.config.getOrThrow<string>('SESSION_SECRET'), { expiresIn: '7d' });
  }

  readSession(token?: string) {
    if (!token) return null;
    try {
      const session = verify(token, this.config.getOrThrow<string>('SESSION_SECRET'));
      if (typeof session !== 'object' || !('name' in session) || !('email' in session)) return null;
      if (!('googleId' in session)) return null;
      return { googleId: String(session.googleId), name: String(session.name), email: String(session.email) };
    } catch {
      return null;
    }
  }

  async getProfile(googleId: string) {
    const safeGoogleId = googleId ? `${googleId.substring(0, 4)}***${googleId.substring(googleId.length - 4)}` : 'missing';
    this.logger.log(`getProfile called. googleId present: ${!!googleId}, safeId: ${safeGoogleId}`);

    const { data, error } = await this.supabase.db
      .from('profiles')
      .select('id, google_id, email, full_name, avatar_url, preferred_language, created_at, updated_at')
      .eq('google_id', googleId)
      .single();

    this.logger.log(`getProfile Supabase query finished. Has data: ${!!data}, Error: ${error?.message || 'none'}`);

    if (error) throw error;
    return data;
  }
}
