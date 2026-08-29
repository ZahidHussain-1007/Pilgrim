import { BadGatewayException, GatewayTimeoutException, Injectable, ServiceUnavailableException } from '@nestjs/common';
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
    let data: { answer: string; sources: unknown[]; language: 'en' | 'te' | 'hi' };
    try {
      ({ data } = await axios.post(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/chat`, payload, { timeout: 45_000 }));
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 502) {
        throw new BadGatewayException('The PilgrimAI RAG service returned an invalid response.');
      }
      if (axios.isAxiosError(error) && error.response?.status === 504) {
        throw new GatewayTimeoutException('The PilgrimAI RAG service timed out.');
      }
      throw new ServiceUnavailableException('The PilgrimAI RAG service is unavailable.');
    }
    const { data: assistantMessage, error: assistantMessageError } = await this.supabase.db.from('messages').insert({ conversation_id: activeConversationId, role: 'assistant', content: data.answer, agent_used: null, source_metadata: { sources: data.sources || [], language: data.language } }).select('id').single();
    if (assistantMessageError) throw assistantMessageError;
    return { ...data, conversationId: activeConversationId, userMessageId: userMessage.id, assistantMessageId: assistantMessage.id };
  }
}
