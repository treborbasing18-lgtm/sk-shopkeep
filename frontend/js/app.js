class ShopKeepApp {
  constructor() {
    this.state = { products: [], sales: [], stats: null };
    this.currentView = 'dashboard';
    this.init();
  }

  async init() {
    try {
        const statusRes = await fetch('/api/auth/setup/status');
        const status = await statusRes.json();
        
        if (status.needs_setup) {
            this.showSetup();
            return;
        }
    } catch (error) {
        console.error('Failed to check setup status:', error);
    }
    
    const isAuth = await auth.checkAuth();
    if (isAuth) {
        await this.loadInitialData();
        this.showApp();
    } else {
        this.showLogin();
    }
}

  async loadInitialData() {
    try {
      const [productsRes, salesRes, statsRes] = await Promise.all([
        ApiService.getProducts(), ApiService.getSales(), ApiService.getSalesStats()
      ]);
      this.state.products = productsRes.products || [];
      this.state.sales = salesRes.sales || [];
      this.state.stats = statsRes;
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  }

  showLogin() {
    document.body.innerHTML = `
        <div class="auth-container">
            <div class="auth-box">
                <h2>SK ShopKeep</h2>
                <p>Sign in to your account</p>
                <div id="login-error" class="error-message"></div>
                <form id="login-form">
                    <input type="text" id="username" placeholder="Username" required autocomplete="off">
                    <input type="password" id="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            await auth.login(username, password);
            await this.loadInitialData();
            this.showApp();
        } catch (error) {
            document.getElementById('login-error').textContent = error.message;
        }
    });
}

  showSetup() {
    document.body.innerHTML = `
        <div class="auth-container">
            <div class="auth-box" style="max-width: 420px;">
                <h2>Welcome to SK ShopKeep</h2>
                <p style="margin-bottom: 20px;">Create your administrator account to get started</p>
                <div id="setup-error" class="error-message"></div>
                <form id="setup-form">
                    <div class="form-group">
                        <label for="setup-username">Admin Username</label>
                        <input type="text" id="setup-username" placeholder="Choose a username" required minlength="3" autocomplete="off">
                        <small style="color: #666; font-size: 11px;">At least 3 characters</small>
                    </div>
                    <div class="form-group">
                        <label for="setup-password">Password</label>
                        <input type="password" id="setup-password" placeholder="Choose a strong password" required minlength="6">
                        <small style="color: #666; font-size: 11px;">At least 6 characters</small>
                    </div>
                    <div class="form-group">
                        <label for="setup-confirm">Confirm Password</label>
                        <input type="password" id="setup-confirm" placeholder="Re-enter your password" required>
                    </div>
                    <button type="submit" style="width: 100%; margin-top: 16px;">Create Admin Account</button>
                </form>
                <p style="font-size: 11px; color: #999; margin-top: 20px; text-align: center;">
                    This will be the main administrator account.<br>You can add more users later.
                </p>
            </div>
        </div>
    `;
    
    document.getElementById('setup-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('setup-username').value.trim();
        const password = document.getElementById('setup-password').value;
        const confirm  = document.getElementById('setup-confirm').value;
        
        const errorEl = document.getElementById('setup-error');
        
        if (password !== confirm) {
            errorEl.textContent = 'Passwords do not match';
            return;
        }
        
        if (username.length < 3) {
            errorEl.textContent = 'Username must be at least 3 characters';
            return;
        }
        
        if (password.length < 6) {
            errorEl.textContent = 'Password must be at least 6 characters';
            return;
        }
        
        try {
            const response = await fetch('/api/auth/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                errorEl.textContent = data.error;
                return;
            }
            
            // Auto-login after successful setup
            await auth.login(username, password);
            await this.loadInitialData();
            this.showApp();
        } catch (error) {
            errorEl.textContent = 'An error occurred during setup';
        }
    });
}

  showApp() {
    document.body.innerHTML = `
      <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header"><h3>SK ShopKeep</h3></div>
            <ul class="nav-menu">
                <li class="nav-item ${this.currentView === 'dashboard' ? 'active' : ''}" data-view="dashboard">Dashboard</li>
                <li class="nav-item ${this.currentView === 'inventory' ? 'active' : ''}" data-view="inventory">Inventory</li>
                <li class="nav-item ${this.currentView === 'sales' ? 'active' : ''}" data-view="sales">Record Sale</li>
                ${auth.isAdmin ? `
                    <li class="nav-item" id="users-btn" style="cursor: pointer;">👥 Users</li>
                ` : ''}
            </ul>
            <div class="sidebar-footer">
                <div class="user-info">${auth.user?.username} (${auth.user?.role})</div>
                <button id="logout-btn" class="btn-secondary">Sign Out</button>
            </div>
        </div>
        <div class="main-content">
          <div class="stats-grid">
            <div class="stat-card">
              <div>Products</div>
              <div class="stat-value">${this.state.products.length}</div>
            </div>
            <div class="stat-card">
              <div>Revenue</div>
              <div class="stat-value">₱${(this.state.stats?.total_revenue || 0).toFixed(2)}</div>
            </div>
          </div>
          <div class="card">
            <h3>Products</h3>
            <div id="products-list"></div>
          </div>
        </div>
      </div>
    `;
    this.renderProducts();
    document.getElementById('users-btn')?.addEventListener('click', () => {
        this.showUserManagement();
    });
    document.getElementById('logout-btn').addEventListener('click', async () => {
      await auth.logout();
      this.showLogin();
    });
  }

  renderProducts() {
    const container = document.getElementById('products-list');
    if (this.state.products.length === 0) {
      container.innerHTML = '<p>No products yet. Add your first product!</p>';
      return;
    }
    container.innerHTML = this.state.products.map(p => `
      <div style="padding:10px;border-bottom:1px solid #eee;display:flex;justify-content:space-between">
        <span><strong>${p.name}</strong> - ${p.category} - ₱${p.price} (${p.quantity} in stock)</span>
        <button onclick="app.sellProduct('${p.id}')" ${p.quantity === 0 ? 'disabled' : ''}>Sell</button>
      </div>
    `).join('');
  }

  showAddProductModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Add Product</h3>
        <form id="product-form">
          <div class="form-group"><input id="pname" placeholder="Name" required></div>
          <div class="form-group"><input id="pcat" placeholder="Category" required></div>
          <div class="form-group"><input id="pprice" type="number" placeholder="Price" min="0" step="0.01" required></div>
          <div class="form-group"><input id="pqty" type="number" placeholder="Quantity" min="0" value="0"></div>
          <button type="submit" class="btn-primary">Save</button>
          <button type="button" onclick="this.closest('.modal').remove()">Cancel</button>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
    modal.querySelector('form').onsubmit = async (e) => {
      e.preventDefault();
      const data = {
        name: document.getElementById('pname').value,
        category: document.getElementById('pcat').value,
        price: parseFloat(document.getElementById('pprice').value),
        quantity: parseInt(document.getElementById('pqty').value) || 0
      };
      await ApiService.createProduct(data);
      await this.loadInitialData();
      modal.remove();
      this.showApp();
    };
  }

  async sellProduct(productId) {
    const qty = prompt('Enter quantity:');
    if (!qty) return;
    try {
      await ApiService.createSale({ product_id: productId, quantity: parseInt(qty) });
      await this.loadInitialData();
      this.showApp();
    } catch (error) {
      alert(error.message);
    }
  }

  showUserManagement() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <h3>User Management</h3>
            <div id="users-list" style="margin-bottom: 20px; max-height: 300px; overflow-y: auto;">
                Loading users...
            </div>
            <div style="border-top: 1px solid #e5e5e5; padding-top: 16px; margin-top: 8px;">
                <h4 style="margin-bottom: 12px;">Add New User</h4>
                <form id="add-user-form">
                    <div class="form-group">
                        <label for="new-username">Username</label>
                        <input type="text" id="new-username" placeholder="Username" required minlength="3">
                    </div>
                    <div class="form-group">
                        <label for="new-password">Password</label>
                        <input type="password" id="new-password" placeholder="Password" required minlength="6">
                    </div>
                    <div class="form-group">
                        <label for="new-role">Role</label>
                        <select id="new-role">
                            <option value="staff">Staff</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
                    <div id="add-user-error" class="error-message"></div>
                    <div class="modal-actions">
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                        <button type="submit" class="btn-primary">Add User</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    this.loadUsersList();
    
    modal.querySelector('#add-user-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('new-username').value.trim();
        const password = document.getElementById('new-password').value;
        const role = document.getElementById('new-role').value;
        
        try {
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password, role })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to create user');
            }
            
            this.loadUsersList();
            modal.querySelector('#add-user-form').reset();
            document.getElementById('add-user-error').textContent = '';
        } catch (error) {
            document.getElementById('add-user-error').textContent = error.message;
        }
    });
}

async loadUsersList() {
    try {
        const response = await fetch('/api/users', { credentials: 'include' });
        const data = await response.json();
        
        const container = document.getElementById('users-list');
        const currentUserId = auth.user?.id;
        
        container.innerHTML = data.users.map(user => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee;">
                <div>
                    <strong>${this.escape(user.username)}</strong>
                    <span style="margin-left: 8px; font-size: 11px; color: #666;">${user.role}</span>
                    ${user.id === currentUserId ? '<span style="margin-left: 8px; font-size: 10px; color: #BA7517;">(You)</span>' : ''}
                </div>
                ${user.id !== currentUserId ? `
                    <button class="btn-small btn-danger" onclick="app.deleteUser('${user.id}', '${user.username}')">Remove</button>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        document.getElementById('users-list').innerHTML = '<p style="color: #791F1F;">Failed to load users</p>';
    }
}

async deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to remove "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to delete user');
        }
        
        this.loadUsersList();
    } catch (error) {
        alert(error.message);
    }
}

escape(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
}

let app;
document.addEventListener('DOMContentLoaded', () => { app = new ShopKeepApp(); });
