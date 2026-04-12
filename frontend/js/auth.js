class AuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
  }

  async checkAuth() {
    try {
      const data = await ApiService.getCurrentUser();
      this.user = data.user;
      this.isAuthenticated = true;
      return true;
    } catch {
      this.user = null;
      this.isAuthenticated = false;
      return false;
    }
  }

  async login(username, password) {
    const data = await ApiService.login(username, password);
    this.user = data.user;
    this.isAuthenticated = true;
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
    return data;
  }
}

const auth = new AuthManager();
