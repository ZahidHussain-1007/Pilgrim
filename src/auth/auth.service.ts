import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient } from '@supabase/supabase-js';
import { sign, verify } from 'jsonwebtoken';

export type GoogleUser = { googleId: string; email: string; name: string; avatarUrl: string | null };

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(private readonly config: ConfigService) {}

  async saveGoogleUser(user: GoogleUser) {
    const url = this.config.get<string>('SUPABASE_URL');
    const key = this.config.get<string>('SUPABASE_SERVICE_ROLE_KEY');
    if (!url || !key) {
      this.logger.warn('Supabase is not configured; Google profile was not persisted.');
      return;
    }

    const supabase = createClient(url, key, { auth: { persistSession: false } });
    const { error } = await supabase.from('profiles').upsert({
      google_id: user.googleId,
      email: user.email,
      full_name: user.name,
      avatar_url: user.avatarUrl,
      updated_at: new Date().toISOString(),
    }, { onConflict: 'google_id' });

    if (error) throw error;
  }

  createSession(user: GoogleUser) {
    return sign({ googleId: user.googleId, email: user.email, name: user.name }, this.config.getOrThrow<string>('SESSION_SECRET'), { expiresIn: '7d' });
  }

  readSession(token?: string) {
    if (!token) return null;
    try {
      const session = verify(token, this.config.getOrThrow<string>('SESSION_SECRET'));
      if (typeof session !== 'object' || !('name' in session) || !('email' in session)) return null;
      return { name: String(session.name), email: String(session.email) };
    } catch {
      return null;
    }
  }
}
