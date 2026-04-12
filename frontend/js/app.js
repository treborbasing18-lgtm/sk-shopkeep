class ShopKeepApp {
  constructor() {
    this.state = { products: [], sales: [], stats: null };
    this.init();
  }

  async init() {
    try {
      const data = await ApiService.checkFirstRun();
      if (data.needs_setup) return this.showSetup();
    } catch {}
    if (await auth.checkAuth()) {
      await this.loadData();
      this.showApp();
    } else {
      this.showLogin();
    }
  }

  async loadData() {
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
          <div id="error" class="error-message"></div>
          <form id="login-form">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
          </form>
        </div>
      </div>
    `;
    document.getElementById('login-form').onsubmit = async (e) => {
      e.preventDefault();
      try {
        await auth.login(
          document.getElementById('username').value,
          document.getElementById('password').value
        );
        await this.loadData();
        this.showApp();
      } catch (error) {
        document.getElementById('error').textContent = error.message;
      }
    };
  }

  showSetup() {
    document.body.innerHTML = `
      <div class="auth-container">
        <div class="auth-box">
          <h2>Create Admin Account</h2>
          <div id="error" class="error-message"></div>
          <form id="setup-form">
            <input type="text" id="username" placeholder="Username" required minlength="3">
            <input type="password" id="password" placeholder="Password" required minlength="6">
            <button type="submit">Create Account</button>
          </form>
        </div>
      </div>
    `;
    document.getElementById('setup-form').onsubmit = async (e) => {
      e.preventDefault();
      try {
        await auth.setup(
          document.getElementById('username').value,
          document.getElementById('password').value
        );
        this.showApp();
      } catch (error) {
        document.getElementById('error').textContent = error.message;
      }
    };
  }

  showApp() {
    document.body.innerHTML = `
      <div class="app-container">
        <div class="sidebar">
          <h2 style="padding:20px">SK ShopKeep</h2>
          <div style="padding:20px">
            <button class="btn-primary" id="add-product-btn">+ Add Product</button>
            <button class="btn-primary" id="logout-btn" style="margin-top:20px">Logout</button>
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
    document.getElementById('add-product-btn').onclick = () => this.showAddProductModal();
    document.getElementById('logout-btn').onclick = async () => {
      await auth.logout();
      this.showLogin();
    };
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
      await this.loadData();
      modal.remove();
      this.showApp();
    };
  }

  async sellProduct(productId) {
    const qty = prompt('Enter quantity:');
    if (!qty) return;
    try {
      await ApiService.createSale({ product_id: productId, quantity: parseInt(qty) });
      await this.loadData();
      this.showApp();
    } catch (error) {
      alert(error.message);
    }
  }
}

let app;
document.addEventListener('DOMContentLoaded', () => { app = new ShopKeepApp(); });
