const API_BASE = '/api';

class ApiService {
  static async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      credentials: 'include',
      headers: {'Content-Type': 'application/json'},
      ...options
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
  }

  static checkFirstRun() { return this.request('/auth/setup/status'); }
  static setup(username, password) { return this.request('/auth/setup', {method: 'POST', body: JSON.stringify({username, password})}); }
  static login(username, password) { return this.request('/auth/login', {method: 'POST', body: JSON.stringify({username, password})}); }
  static logout() { return this.request('/auth/logout', {method: 'POST'}); }
  static getCurrentUser() { return this.request('/auth/me'); }
  static getProducts() { return this.request('/products'); }
  static createProduct(data) { return this.request('/products', {method: 'POST', body: JSON.stringify(data)}); }
  static deleteProduct(id) { return this.request(`/products/${id}`, {method: 'DELETE'}); }
  static getSales() { return this.request('/sales'); }
  static createSale(data) { return this.request('/sales', {method: 'POST', body: JSON.stringify(data)}); }
  static getSalesStats() { return this.request('/sales/stats'); }
}
