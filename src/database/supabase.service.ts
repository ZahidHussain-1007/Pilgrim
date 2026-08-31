import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable()
export class SupabaseService {
  private readonly client: SupabaseClient | null;

  constructor(config: ConfigService) {
    const url = config.get<string>('SUPABASE_URL');
    const key = config.get<string>('SUPABASE_SERVICE_ROLE_KEY');
    
    console.log('--- DIAGNOSTIC: SUPABASE CONFIGURATION ---');
    console.log('SUPABASE_URL exists:', !!url);
    console.log('SUPABASE_ANON_KEY exists:', !!config.get<string>('SUPABASE_ANON_KEY'));
    console.log('SUPABASE_SERVICE_ROLE_KEY exists:', !!key);
    console.log('SESSION_SECRET exists:', !!config.get<string>('SESSION_SECRET'));
    console.log('FASTAPI_URL:', config.get<string>('FASTAPI_URL'));
    console.log('------------------------------------------');
    
    this.client = url && key ? createClient(url, key, { auth: { persistSession: false } }) : null;
  }

  get db() {
    if (!this.client) throw new ServiceUnavailableException('Supabase is not configured.');
    return this.client;
  }

  get configured() { return this.client !== null; }
}