import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import axios from 'axios';
import { SupabaseService } from '../database/supabase.service';

@Injectable()
export class ChatService {
  constructor(private readonly supabase: SupabaseService) {}

  async ask(payload: { query: string; temple?: string | null; language: 'en' | 'te' | 'hi' }, profileId: string, conversationId?: string) {
    let activeConversationId = conversationId;
    if (activeConversationId) {
      const { data: conversation, error } = await this.supabase.db.from('conversations').select('id').eq('id', activeConversationId).eq('profile_id', profileId).single();
      if (error || !conversation) throw new Error('Conversation does not belong to the current user.');
    } else {
      const { data, error } = await this.supabase.db.from('conversations').insert({ profile_id: profileId, title: payload.query.slice(0, 80), language: payload.language }).select('id').single();
      if (error) throw error;
      activeConversationId = data.id;
    }
    const { data: userMessage, error: userMessageError } = await this.supabase.db.from('messages').insert({ conversation_id: activeConversationId, role: 'user', content: payload.query }).select('id').single();
    if (userMessageError) throw userMessageError;
    try {
      const { data } = await axios.post(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat`, payload, { timeout: 45_000 });
      const { data: assistantMessage, error: assistantMessageError } = await this.supabase.db.from('messages').insert({ conversation_id: activeConversationId, role: 'assistant', content: data.reply, agent_used: data.agent_used || null, source_metadata: data.source_metadata || {} }).select('id').single();
      if (assistantMessageError) throw assistantMessageError;
      return { ...data, conversationId: activeConversationId, userMessageId: userMessage.id, assistantMessageId: assistantMessage.id };
    } catch {
      throw new ServiceUnavailableException('The PilgrimAI RAG service is unavailable.');
    }
  }
}
