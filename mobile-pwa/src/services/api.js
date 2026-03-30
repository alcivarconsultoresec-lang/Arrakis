/**
 * Ω JARBIS Enterprise - API Client
 * Cliente para comunicación con el backend FastAPI
 */

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = null;
    this.refreshToken = null;
    this.pendingRequests = [];
    this.isRefreshing = false;
  }

  // ============================================================================
  // AUTH
  // ============================================================================

  setToken(token, refreshToken = null) {
    this.token = token;
    this.refreshToken = refreshToken;
    localStorage.setItem('jarbis_token', token);
    if (refreshToken) {
      localStorage.setItem('jarbis_refresh_token', refreshToken);
    }
  }

  getToken() {
    return this.token || localStorage.getItem('jarbis_token');
  }

  getRefreshToken() {
    return this.refreshToken || localStorage.getItem('jarbis_refresh_token');
  }

  clearAuth() {
    this.token = null;
    this.refreshToken = null;
    localStorage.removeItem('jarbis_token');
    localStorage.removeItem('jarbis_refresh_token');
  }

  // ============================================================================
  // REQUEST HANDLER
  // ============================================================================

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Manejar error 401 (token expirado)
      if (response.status === 401 && !options.retry) {
        return await this.handleUnauthorized(endpoint, options);
      }

      // Manejar error offline
      if (response.status === 503) {
        const data = await response.json().catch(() => ({}));
        if (data.offline) {
          // Guardar en cola para sync posterior
          await this.queueRequest(endpoint, options);
        }
        throw new Error('Sin conexión. Tu solicitud se enviará más tarde.');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(error.detail || 'Error en la solicitud');
      }

      return await response.json();
    } catch (error) {
      console.error('[API] Request failed:', error);
      throw error;
    }
  }

  async handleUnauthorized(endpoint, options) {
    if (this.isRefreshing) {
      // Esperar a que se complete el refresh
      return new Promise((resolve) => {
        this.pendingRequests.push({ endpoint, options, resolve });
      });
    }

    this.isRefreshing = true;

    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        this.clearAuth();
        window.location.href = '/login';
        throw new Error('No hay sesión activa');
      }

      // Refresh token
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearAuth();
        window.location.href = '/login';
        throw new Error('Sesión expirada');
      }

      const data = await response.json();
      this.setToken(data.access_token, data.refresh_token);

      // Repetir requests pendientes
      this.pendingRequests.forEach(({ endpoint: e, options: o, resolve }) => {
        resolve(this.request(e, { ...o, retry: true }));
      });
      this.pendingRequests = [];

      return await this.request(endpoint, { ...options, retry: true });
    } finally {
      this.isRefreshing = false;
    }
  }

  // ============================================================================
  // OFFLINE QUEUE
  // ============================================================================

  async queueRequest(endpoint, options) {
    const queue = JSON.parse(localStorage.getItem('jarbis_offline_queue') || '[]');
    queue.push({
      id: Date.now(),
      endpoint,
      options,
      timestamp: new Date().toISOString(),
    });

    // Mantener solo últimos 50 requests
    if (queue.length > 50) {
      queue.shift();
    }

    localStorage.setItem('jarbis_offline_queue', JSON.stringify(queue));

    // Intentar sync cuando haya conexión
    if ('serviceWorker' in navigator && 'sync' in window.registration) {
      await window.registration.sync.register('sync-messages');
    }
  }

  async processOfflineQueue() {
    const queue = JSON.parse(localStorage.getItem('jarbis_offline_queue') || '[]');
    const failed = [];

    for (const item of queue) {
      try {
        await this.request(item.endpoint, item.options);
      } catch (error) {
        failed.push(item);
      }
    }

    localStorage.setItem('jarbis_offline_queue', JSON.stringify(failed));
    return failed.length === 0;
  }

  // ============================================================================
  // ENDPOINTS - MOBILE CHAT
  // ============================================================================

  async sendMessage(message, options = {}) {
    return this.request('/mobile/chat', {
      method: 'POST',
      body: JSON.stringify({ message, ...options }),
    });
  }

  async getChatHistory(limit = 20) {
    return this.request(`/mobile/history?limit=${limit}`);
  }

  async clearChatHistory() {
    return this.request('/mobile/history', { method: 'DELETE' });
  }

  // ============================================================================
  // ENDPOINTS - RECETAS
  // ============================================================================

  async getRecipes() {
    return this.request('/recipes');
  }

  async getRecipeById(id) {
    return this.request(`/recipes/${id}`);
  }

  async getRecipeCostBreakdown(id) {
    return this.request(`/recipes/${id}/cost-breakdown`);
  }

  async createRecipe(recipe) {
    return this.request('/recipes', {
      method: 'POST',
      body: JSON.stringify(recipe),
    });
  }

  async updateRecipe(id, recipe) {
    return this.request(`/recipes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(recipe),
    });
  }

  async deleteRecipe(id) {
    return this.request(`/recipes/${id}`, { method: 'DELETE' });
  }

  // ============================================================================
  // ENDPOINTS - INVENTARIO
  // ============================================================================

  async getInventory(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    return this.request(`/inventory?${params}`);
  }

  async getInventoryRecommendations() {
    return this.request('/inventory/recommendations');
  }

  async createInventoryItem(item) {
    return this.request('/inventory', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updateInventoryItem(id, item) {
    return this.request(`/inventory/${id}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    });
  }

  async logMovement(movement) {
    return this.request('/inventory/movement', {
      method: 'POST',
      body: JSON.stringify(movement),
    });
  }

  async createPurchaseOrder(order) {
    return this.request('/inventory/purchase-orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  // ============================================================================
  // ENDPOINTS - EVENTOS
  // ============================================================================

  async calculateEventQuote(eventData) {
    return this.request('/events/calculate-quote', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async getEventTemplates() {
    return this.request('/events/templates');
  }

  async createEvent(event) {
    return this.request('/events', {
      method: 'POST',
      body: JSON.stringify(event),
    });
  }

  // ============================================================================
  // ENDPOINTS - FINANZAS
  // ============================================================================

  async getFinancialDashboard(period = 'month') {
    return this.request(`/financial/dashboard?period=${period}`);
  }

  async getFinancialRecords(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    return this.request(`/financial/records?${params}`);
  }

  async createFinancialRecord(record) {
    return this.request('/financial/records', {
      method: 'POST',
      body: JSON.stringify(record),
    });
  }

  async getWasteAnalysis(period = 'month') {
    return this.request(`/financial/waste-analysis?period=${period}`);
  }

  async getProfitTrend(months = 6) {
    return this.request(`/financial/profit-trend?months=${months}`);
  }

  async exportFinancialReport(format = 'csv', startDate, endDate) {
    const params = new URLSearchParams({ format });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return this.request(`/financial/export?${params}`);
  }

  // ============================================================================
  // ENDPOINTS - POS
  // ============================================================================

  async connectPOS(provider, credentials) {
    return this.request('/pos/connect', {
      method: 'POST',
      body: JSON.stringify({ provider, credentials }),
    });
  }

  async disconnectPOS(provider) {
    return this.request(`/pos/disconnect/${provider}`, { method: 'POST' });
  }

  async getPOSStatus() {
    return this.request('/pos/status');
  }

  async syncPOSSales(startDate, endDate) {
    return this.request('/pos/sync', {
      method: 'POST',
      body: JSON.stringify({ start_date: startDate, end_date: endDate }),
    });
  }

  // ============================================================================
  // ENDPOINTS - AUTH
  // ============================================================================

  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(response.access_token, response.refresh_token);
    return response;
  }

  async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.clearAuth();
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getProfile() {
    return this.request('/auth/profile');
  }

  // ============================================================================
  // UTILIDADES
  // ============================================================================

  async checkConnection() {
    try {
      await this.request('/health');
      return true;
    } catch {
      return false;
    }
  }
}

// Exportar instancia singleton
export const api = new ApiClient();
export default api;
