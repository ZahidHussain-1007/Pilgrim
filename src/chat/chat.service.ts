import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class ChatService {
  async ask(payload: object) {
    try {
      const { data } = await axios.post(`${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat`, payload, { timeout: 45_000 });
      return data;
    } catch {
      throw new ServiceUnavailableException('The PilgrimAI RAG service is unavailable.');
    }
  }
}
