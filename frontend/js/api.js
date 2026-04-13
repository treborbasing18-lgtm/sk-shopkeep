const API_BASE = '/api';

class ApiService {
  static _csrfToken = null;

  static async ensureCsrf() {
    if (this._csrfToken) return;
    try {
      const res = await fetch(`${API_BASE}/auth/csrf-token`, { credentials: 'include' });
      const data = await res.json();
      this._csrfToken = data.csrf_token || null;
    } catch (e) {
      console.warn('CSRF fetch failed:', e);
    }
  }

  static async request(endpoint, options = {}) {
    await this.ensureCsrf();

    const method = (options.method || 'GET').toUpperCase();
    const headers = { 'Content-Type': 'application/json' };
    if (this._csrfToken && !['GET','HEAD','OPTIONS'].includes(method)) {
      headers['X-CSRF-Token'] = this._csrfToken;
    }

    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      credentials: 'include',
      headers,
      ...options,
      headers: { ...headers, ...(options.headers || {}) }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
  }

  // Auth
  static checkFirstRun()           { return this.request('/auth/setup/status'); }
  static setup(username, password) { return this.request('/auth/setup', { method: 'POST', body: JSON.stringify({ username, password }) }); }
  static login(username, password) { return this.request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }); }
  static logout()                  { return this.request('/auth/logout', { method: 'POST' }); }
  static getCurrentUser()          { return this.request('/auth/me'); }

  // Products
  static getProducts()             { return this.request('/products'); }
  static getProduct(id)            { return this.request(`/products/${id}`); }
  static createProduct(data)       { return this.request('/products', { method: 'POST', body: JSON.stringify(data) }); }
  static updateProduct(id, data)   { return this.request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
  static deleteProduct(id)         { return this.request(`/products/${id}`, { method: 'DELETE' }); }

  // Sales
  static getSales(limit)           { return this.request(`/sales${limit ? '?limit=' + limit : ''}`); }
  static createSale(data)          { return this.request('/sales', { method: 'POST', body: JSON.stringify(data) }); }
  static getSalesStats()           { return this.request('/sales/stats'); }

  // Users
  static getUsers()                { return this.request('/users'); }
  static createUser(data)          { return this.request('/users', { method: 'POST', body: JSON.stringify(data) }); }
  static deleteUser(id)            { return this.request(`/users/${id}`, { method: 'DELETE' }); }

  // Reports
  static getReportSummary()        { return this.request('/reports/summary'); }
  static getSalesSummary(from, to) {
    const params = new URLSearchParams();
    if (from) params.set('date_from', from);
    if (to)   params.set('date_to', to);
    return this.request(`/reports/sales-summary?${params}`);
  }
  static getInventoryValue()       { return this.request('/reports/inventory-value'); }
  static getTopProducts(limit=10)  { return this.request(`/reports/top-products?limit=${limit}`); }

  // Logs
  static getLogs(params = {}) {
    const q = new URLSearchParams();
    if (params.page)      q.set('page', params.page);
    if (params.per_page)  q.set('per_page', params.per_page);
    if (params.action)    q.set('action', params.action);
    if (params.user_id)   q.set('user_id', params.user_id);
    if (params.date_from) q.set('date_from', params.date_from);
    if (params.date_to)   q.set('date_to', params.date_to);
    return this.request(`/logs?${q}`);
  }

  // Backup
  static createBackup()            { return this.request('/backup/create', { method: 'POST' }); }
  static listBackups()             { return this.request('/backup/list'); }
  static downloadBackupUrl()       { return `${API_BASE}/backup/download`; }
}
