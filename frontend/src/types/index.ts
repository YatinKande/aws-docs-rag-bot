export interface APIKey {
    id: string;
    provider: 'aws' | 'gcp' | 'azure' | 'custom';
    nickname: string;
    status: 'active' | 'invalid' | 'expired';
    last_validated?: string;
    created_at: string;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    source_type?: 'docs' | 'api' | 'hybrid' | 'none';
    source_details?: any[];
}
