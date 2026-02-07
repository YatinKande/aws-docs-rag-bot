const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = {
    async chat(query: string, selectedSource: string = 'auto', selectedDb: string = 'faiss'): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                selected_source: selectedSource,
                selected_db: selectedDb
            }),
        });
        return response.json();
    },

    async getApiKeys(): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/api-keys/`);
        return response.json();
    },

    async getDocuments(): Promise<any[]> {
        const response = await fetch(`${API_BASE_URL}/documents/`);
        return response.json();
    },

    async createApiKey(provider: string, nickname: string, credentials: any): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/api-keys/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, nickname, credentials }),
        });
        return response.json();
    },

    async deleteApiKey(id: string): Promise<void> {
        await fetch(`${API_BASE_URL}/api-keys/${id}`, {
            method: 'DELETE',
        });
    },

    async uploadDocument(file: File, database: string): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/documents/upload?database=${database}`, {
            method: 'POST',
            body: formData,
        });
        return response.json();
    }
};
