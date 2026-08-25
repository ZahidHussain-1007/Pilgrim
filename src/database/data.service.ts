import { Injectable, NotFoundException } from '@nestjs/common';
import { AuthService, SessionUser } from '../auth/auth.service';
import { SupabaseService } from './supabase.service';

@Injectable()
export class DataService {
  constructor(private readonly supabase: SupabaseService, private readonly auth: AuthService) {}

  private async profileId(session: SessionUser) {
    const profile = await this.auth.getProfile(session.googleId);
    return profile.id;
  }

  async getProfile(session: SessionUser) {
    return this.auth.getProfile(session.googleId);
  }

  async listConversations(session: SessionUser) {
    const profileId = await this.profileId(session);
    const { data, error } = await this.supabase.db.from('conversations').select('*').eq('profile_id', profileId).order('updated_at', { ascending: false });
    if (error) throw error;
    return data;
  }

  async createConversation(session: SessionUser, input: { title?: string; language: string }) {
    const profileId = await this.profileId(session);
    const { data, error } = await this.supabase.db.from('conversations').insert({ profile_id: profileId, title: input.title || null, language: input.language }).select().single();
    if (error) throw error;
    return data;
  }

  async getMessages(session: SessionUser, conversationId: string) {
    const conversation = await this.getOwnedConversation(session, conversationId);
    const { data, error } = await this.supabase.db.from('messages').select('*').eq('conversation_id', conversation.id).order('created_at', { ascending: true });
    if (error) throw error;
    return data;
  }

  async deleteConversation(session: SessionUser, conversationId: string) {
    await this.getOwnedConversation(session, conversationId);
    const { error } = await this.supabase.db.from('conversations').delete().eq('id', conversationId);
    if (error) throw error;
    return { ok: true };
  }

  async listFavorites(session: SessionUser) {
    const profileId = await this.profileId(session);
    const { data, error } = await this.supabase.db.from('favorites').select('*').eq('profile_id', profileId).order('created_at', { ascending: false });
    if (error) throw error;
    return data;
  }

  async addFavorite(session: SessionUser, input: { itemType: string; itemKey: string; itemData: unknown }) {
    const profileId = await this.profileId(session);
    const { data, error } = await this.supabase.db.from('favorites').upsert({ profile_id: profileId, item_type: input.itemType, item_key: input.itemKey, item_data: input.itemData }, { onConflict: 'profile_id,item_type,item_key' }).select().single();
    if (error) throw error;
    return data;
  }

  async removeFavorite(session: SessionUser, itemType: string, itemKey: string) {
    const profileId = await this.profileId(session);
    const { error } = await this.supabase.db.from('favorites').delete().eq('profile_id', profileId).eq('item_type', itemType).eq('item_key', itemKey);
    if (error) throw error;
    return { ok: true };
  }

  async submitFeedback(session: SessionUser, messageId: string, rating: number, comment?: string) {
    const profileId = await this.profileId(session);
    const { data: message, error: messageError } = await this.supabase.db.from('messages').select('id, role, conversation_id, conversations!inner(profile_id)').eq('id', messageId).eq('conversations.profile_id', profileId).eq('role', 'assistant').single();
    if (messageError || !message) throw new NotFoundException('Assistant message not found.');
    const { data, error } = await this.supabase.db.from('feedback').insert({ profile_id: profileId, message_id: message.id, rating, comment: comment || null }).select().single();
    if (error) throw error;
    return data;
  }

  async getOwnedConversation(session: SessionUser, conversationId: string) {
    const profileId = await this.profileId(session);
    const { data, error } = await this.supabase.db.from('conversations').select('id, profile_id').eq('id', conversationId).eq('profile_id', profileId).single();
    if (error || !data) throw new NotFoundException('Conversation not found.');
    return data;
  }
}