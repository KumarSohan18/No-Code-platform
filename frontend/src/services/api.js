const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
    };

    // Only set Content-Type for JSON requests, not for FormData
    if (!(options.body instanceof FormData)) {
      config.headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };
    } else {
      // For FormData, let browser set Content-Type with boundary
      config.headers = {
        ...options.headers,
      };
    }

    try {
      console.log('Making API request:', url, config);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health endpoints
  async healthCheck() {
    return this.request('/health');
  }

  async detailedHealthCheck() {
    return this.request('/health/detailed');
  }

  // Workflow endpoints
  async createWorkflow(workflowData) {
    return this.request('/workflows', {
      method: 'POST',
      body: JSON.stringify(workflowData),
    });
  }

  async getWorkflows() {
    return this.request('/workflows');
  }

  async getWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`);
  }

  async updateWorkflow(workflowId, workflowData) {
    return this.request(`/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(workflowData),
    });
  }

  async validateWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}/validate`, {
      method: 'POST',
    });
  }

  async deleteWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`, {
      method: 'DELETE',
    });
  }

  // Chat endpoints
  async createChatSession(workflowId) {
    return this.request(`/chat/sessions`, {
      method: 'POST',
      body: JSON.stringify({ workflow_id: workflowId }),
    });
  }

  async getChatSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`);
  }

  async sendMessage(sessionId, message) {
    return this.request(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async getChatMessages(sessionId, limit = 50) {
    return this.request(`/chat/sessions/${sessionId}/messages?limit=${limit}`);
  }

  async deleteChatSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async executeWorkflow(workflowId, inputData, sessionId = null) {
    return this.request('/chat/execute', {
      method: 'POST',
      body: JSON.stringify({
        workflow_id: workflowId,
        input_data: inputData,
        session_id: sessionId,
      }),
    });
  }

  // Document endpoints
  async uploadDocument(file, collection = 'default') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', collection);

    return this.request('/documents/upload', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  async processDocument(documentId, collection = 'default') {
    return this.request(`/documents/${documentId}/process?collection=${collection}`, {
      method: 'POST',
    });
  }

  async listDocuments(page = 1, size = 10, processedOnly = false) {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
      processed_only: processedOnly.toString(),
    });
    return this.request(`/documents?${params}`);
  }

  async getDocument(documentId) {
    return this.request(`/documents/${documentId}`);
  }

  async deleteDocument(documentId) {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async searchDocuments(query, collection = 'default', topK = 5, threshold = 0.7) {
    return this.request('/documents/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        collection,
        top_k: topK,
        threshold,
      }),
    });
  }

  async listCollections() {
    return this.request('/documents/collections');
  }
}

export default new ApiService();
