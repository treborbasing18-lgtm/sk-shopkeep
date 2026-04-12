class AuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.isAdmin = false;
  }

  async checkAuth() {
    try {
      const data = await ApiService.getCurrentUser();
      this.user = data.user;
      this.isAuthenticated = true;
      this.isAdmin = this.user.role === 'admin';
      return true;
    } catch {
      this.user = null;
      this.isAuthenticated = false;
      this.isAdmin = false;
      return false;
    }
  }

  async login(username, password) {
    const data = await ApiService.login(username, password);
    this.user = data.user;
    this.isAuthenticated = true;
    this.isAdmin = this.user.role === 'admin';
    return data;
  }

  async logout() {
    await ApiService.logout();
    this.user = null;
    this.isAuthenticated = false;
  }

  async setup(username, password) {
    const data = await ApiService.setup(username, password);
    this.user = data.user;
    this.isAuthenticated = true;
    this.isAdmin = this.user.role === 'admin';
    return data;
  }
}

const auth = new AuthManager();
