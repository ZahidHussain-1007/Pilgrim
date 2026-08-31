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
      const targetUrl = `${process.env.FASTAPI_URL || 'http://127.0.0.1:8000'}/chat`;
      const requestPayload = { ...payload, session_id: activeConversationId };
      
      ({ data } = await axios.post(targetUrl, requestPayload, { timeout: 45_000 }));
    } catch (error) {
      console.error('FASTAPI REQUEST FAILED:');
      let debugInfo = String(error);
      if (axios.isAxiosError(error)) {
        console.error('Message:', error.message);
        console.error('Code:', error.code);
        console.error('Response Status:', error.response?.status);
        console.error('Response Data:', error.response?.data);
        debugInfo = `Axios Error: ${error.code} - ${error.message}. URL: ${error.config?.url}`;
      } else {
        console.error('Error:', error);
      }
      
      const { InternalServerErrorException } = require('@nestjs/common');
      throw new InternalServerErrorException(`Backend Integration Failure: ${debugInfo}`);
    }
    const { data: assistantMessage, error: assistantMessageError } = await this.supabase.db.from('messages').insert({ conversation_id: activeConversationId, role: 'assistant', content: data.answer, agent_used: null, source_metadata: { sources: data.sources || [], language: data.language } }).select('id').single();
    if (assistantMessageError) throw assistantMessageError;
    return { ...data, conversationId: activeConversationId, userMessageId: userMessage.id, assistantMessageId: assistantMessage.id };
  }
}
