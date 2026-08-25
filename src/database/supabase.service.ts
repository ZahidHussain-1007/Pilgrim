import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable()
export class SupabaseService {
  private readonly client: SupabaseClient | null;

  constructor(config: ConfigService) {
    const url = config.get<string>('SUPABASE_URL');
    const key = config.get<string>('SUPABASE_SERVICE_ROLE_KEY');
    this.client = url && key ? createClient(url, key, { auth: { persistSession: false } }) : null;
  }

  get db() {
    if (!this.client) throw new ServiceUnavailableException('Supabase is not configured.');
    return this.client;
  }

  get configured() { return this.client !== null; }
}