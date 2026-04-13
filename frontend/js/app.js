class ShopKeepApp {
  constructor() {
    this.state = { products: [], sales: [], stats: null };
    this.currentView = 'dashboard';
    this.init();
  }

  // ── INIT ─────────────────────────────────────────────────────────────────

  async init() {
    try {
      const status = await ApiService.checkFirstRun();
      if (status.needs_setup) { this.showSetup(); return; }
    } catch (e) { console.error(e); }

    const isAuth = await auth.checkAuth();
    if (isAuth) {
      await this.loadInitialData();
      this.renderShell();
      this.navigateTo('dashboard');
    } else {
      this.showLogin();
    }
  }

  async loadInitialData() {
    try {
      const [pRes, sRes, stRes] = await Promise.all([
        ApiService.getProducts(), ApiService.getSales(50), ApiService.getSalesStats()
      ]);
      this.state.products = pRes.products || [];
      this.state.sales    = sRes.sales    || [];
      this.state.stats    = stRes;
    } catch (e) { console.error('loadInitialData:', e); }
  }

  // ── SHELL ─────────────────────────────────────────────────────────────────

  renderShell() {
    const isAdmin = auth.isAdmin;
    document.body.innerHTML = `
      <div class="app-container">
        <div class="sidebar">
          <div class="sidebar-header">
            <h3>SK ShopKeep</h3>
            <small>v2.0</small>
          </div>
          <ul class="nav-menu">
            <li class="nav-item" data-view="dashboard"><span class="nav-icon">⬛</span> Dashboard</li>
            <li class="nav-item" data-view="inventory"><span class="nav-icon">📦</span> Inventory</li>
            <li class="nav-item" data-view="sales"><span class="nav-icon">🧾</span> Sales</li>
            <li class="nav-item" data-view="reports"><span class="nav-icon">📊</span> Reports</li>
            ${isAdmin ? `
            <li class="nav-item" data-view="logs"><span class="nav-icon">🗒️</span> Audit Log</li>
            <li class="nav-item" data-view="users"><span class="nav-icon">👥</span> Users</li>
            <li class="nav-item" data-view="backup"><span class="nav-icon">💾</span> Backup</li>
            ` : ''}
          </ul>
          <div class="sidebar-footer">
            <div class="user-info">
              <strong>${this.escape(auth.user?.username)}</strong>
              ${auth.user?.role}
            </div>
            <button class="btn-secondary" id="logout-btn">Sign Out</button>
          </div>
        </div>
        <div class="main-content" id="main-content"></div>
      </div>
    `;

    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
      el.addEventListener('click', () => this.navigateTo(el.dataset.view));
    });

    document.getElementById('logout-btn').addEventListener('click', async () => {
      await auth.logout();
      this.showLogin();
    });
  }

  navigateTo(view) {
    this.currentView = view;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.view === view);
    });
    const views = {
      dashboard: () => this.renderDashboard(),
      inventory: () => this.renderInventory(),
      sales:     () => this.renderSales(),
      reports:   () => this.renderReports(),
      logs:      () => this.renderLogs(),
      users:     () => this.renderUsers(),
      backup:    () => this.renderBackup(),
    };
    if (views[view]) views[view]();
  }

  setContent(html) {
    document.getElementById('main-content').innerHTML = html;
  }

  // ── AUTH SCREENS ──────────────────────────────────────────────────────────

  showLogin() {
    document.body.innerHTML = `
      <div class="auth-container">
        <div class="auth-box">
          <h2>SK ShopKeep</h2>
          <p>Sign in to continue</p>
          <div id="login-error" class="error-message"></div>
          <form id="login-form">
            <label for="login-username" style="display:none">Username</label>
            <input type="text" id="login-username" placeholder="Username" required autocomplete="off">
            <label for="login-password" style="display:none">Password</label>
            <input type="password" id="login-password" placeholder="Password" required>
            <button type="submit">Sign In</button>
          </form>
        </div>
      </div>
    `;
    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('button');
      btn.disabled = true; btn.textContent = 'Signing in…';
      try {
        await auth.login(
          document.getElementById('login-username').value,
          document.getElementById('login-password').value
        );
        await this.loadInitialData();
        this.renderShell();
        this.navigateTo('dashboard');
      } catch (err) {
        document.getElementById('login-error').textContent = err.message;
        btn.disabled = false; btn.textContent = 'Sign In';
      }
    });
  }

  showSetup() {
    document.body.innerHTML = `
      <div class="auth-container">
        <div class="auth-box" style="max-width:420px">
          <h2>Welcome to SK ShopKeep</h2>
          <p>Create your administrator account to get started</p>
          <div id="setup-error" class="error-message"></div>
          <form id="setup-form">
            <div class="form-group">
              <label for="setup-username">Admin Username</label>
              <input type="text" id="setup-username" placeholder="Choose a username" required minlength="3" autocomplete="off">
              <small>At least 3 characters, letters/numbers/underscores only</small>
            </div>
            <div class="form-group">
              <label for="setup-password">Password</label>
              <input type="password" id="setup-password" placeholder="Choose a strong password" required minlength="8">
              <small>At least 8 characters, must include a letter and a number</small>
            </div>
            <div class="form-group">
              <label for="setup-confirm">Confirm Password</label>
              <input type="password" id="setup-confirm" placeholder="Re-enter your password" required>
            </div>
            <button type="submit" style="width:100%;margin-top:8px">Create Admin Account</button>
          </form>
          <p style="font-size:11px;color:#555;margin-top:20px;text-align:center">You can add more users after setup.</p>
        </div>
      </div>
    `;
    document.getElementById('setup-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('setup-username').value.trim();
      const password = document.getElementById('setup-password').value;
      const confirm  = document.getElementById('setup-confirm').value;
      const errorEl  = document.getElementById('setup-error');
      const btn      = e.target.querySelector('button');

      if (password !== confirm) { errorEl.textContent = 'Passwords do not match'; return; }

      btn.disabled = true; btn.textContent = 'Creating…';
      try {
        const res = await fetch('/api/auth/setup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) { errorEl.textContent = data.error; btn.disabled = false; btn.textContent = 'Create Admin Account'; return; }
        await auth.login(username, password);
        await this.loadInitialData();
        this.renderShell();
        this.navigateTo('dashboard');
      } catch (err) {
        errorEl.textContent = err.message;
        btn.disabled = false; btn.textContent = 'Create Admin Account';
      }
    });
  }

  // ── DASHBOARD ─────────────────────────────────────────────────────────────

  async renderDashboard() {
    this.setContent('<div class="loading">Loading dashboard</div>');
    try {
      const [summary, topProds] = await Promise.all([
        ApiService.getReportSummary(),
        ApiService.getTopProducts(5)
      ]);
      const lowStock = this.state.products.filter(p => p.quantity <= p.reorder_threshold);

      this.setContent(`
        <div class="page-header">
          <div><h2>Dashboard</h2><p>Overview of your shop</p></div>
        </div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value">₱${this.fmt(summary.total_revenue)}</div>
            <div class="stat-sub">${summary.total_transactions} transactions</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">Products</div>
            <div class="stat-value">${summary.total_products}</div>
            <div class="stat-sub">${summary.total_stock} units in stock</div>
          </div>
          <div class="stat-card ${summary.low_stock_count > 0 ? 'danger' : ''}">
            <div class="stat-label">Low Stock</div>
            <div class="stat-value">${summary.low_stock_count}</div>
            <div class="stat-sub">items below threshold</div>
          </div>
        </div>

        ${lowStock.length > 0 ? `
        <div class="alert alert-error" style="margin-bottom:20px">
          ⚠️ ${lowStock.length} product${lowStock.length > 1 ? 's' : ''} below reorder threshold:
          ${lowStock.map(p => `<strong>${this.escape(p.name)}</strong> (${p.quantity} left)`).join(', ')}
        </div>` : ''}

        <div class="card">
          <div class="card-header">
            <span class="card-title">Top Products by Revenue</span>
            <button class="btn-ghost" onclick="app.navigateTo('reports')">Full Report →</button>
          </div>
          <div class="bar-chart">
            ${this.renderBarChart(topProds.top_products, 'name', 'revenue', '₱')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Recent Sales</span>
            <button class="btn-ghost" onclick="app.navigateTo('sales')">View All →</button>
          </div>
          ${this.renderSalesTable(this.state.sales.slice(0, 8))}
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load dashboard: ${e.message}</div>`);
    }
  }

  renderBarChart(rows, labelKey, valueKey, prefix = '') {
    if (!rows || rows.length === 0) return '<p style="color:var(--text3);font-size:13px">No data yet.</p>';
    const max = Math.max(...rows.map(r => r[valueKey])) || 1;
    return rows.map(r => `
      <div class="bar-row">
        <div class="bar-label" title="${this.escape(r[labelKey])}">${this.escape(r[labelKey])}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${Math.round(r[valueKey]/max*100)}%"></div></div>
        <div class="bar-val">${prefix}${this.fmt(r[valueKey])}</div>
      </div>
    `).join('');
  }

  // ── INVENTORY ─────────────────────────────────────────────────────────────

  async renderInventory() {
    await this.loadInitialData();
    this.setContent(`
      <div class="page-header">
        <div><h2>Inventory</h2><p>${this.state.products.length} products</p></div>
        <button class="btn-primary" onclick="app.showAddProductModal()">+ Add Product</button>
      </div>
      <div class="card">
        <div class="filter-bar">
          <input type="text" id="inv-search" placeholder="Search products…" oninput="app.filterInventory()">
          <select id="inv-cat" onchange="app.filterInventory()">
            <option value="">All Categories</option>
            ${[...new Set(this.state.products.map(p => p.category))].map(c =>
              `<option value="${this.escape(c)}">${this.escape(c)}</option>`
            ).join('')}
          </select>
        </div>
        <table class="data-table" id="inv-table">
          <thead>
            <tr>
              <th>Product</th><th>Category</th><th>Price</th>
              <th>Stock</th><th>Reorder At</th><th>Actions</th>
            </tr>
          </thead>
          <tbody id="inv-body">
            ${this.renderInventoryRows(this.state.products)}
          </tbody>
        </table>
      </div>
    `);
  }

  renderInventoryRows(products) {
    if (products.length === 0) return `<tr><td colspan="6" style="text-align:center;color:var(--text3);padding:32px">No products found</td></tr>`;
    return products.map(p => {
      const low = p.quantity <= p.reorder_threshold;
      return `
        <tr class="${low ? 'low-stock-row' : ''}">
          <td><strong>${this.escape(p.name)}</strong></td>
          <td>${this.escape(p.category)}</td>
          <td style="font-family:var(--mono)">₱${this.fmt(p.price)}</td>
          <td>
            <span class="badge ${low ? 'badge-low' : 'badge-ok'}">${p.quantity}</span>
          </td>
          <td style="color:var(--text3);font-family:var(--mono)">${p.reorder_threshold}</td>
          <td style="display:flex;gap:8px">
            <button class="btn-ghost btn-small" onclick="app.showEditProductModal('${p.id}')">Edit</button>
            <button class="btn-ghost btn-small" onclick="app.showSellModal('${p.id}')" ${p.quantity === 0 ? 'disabled' : ''}>Sell</button>
            ${auth.isAdmin ? `<button class="btn-danger btn-small" onclick="app.confirmDeleteProduct('${p.id}','${this.escape(p.name)}')">Delete</button>` : ''}
          </td>
        </tr>
      `;
    }).join('');
  }

  filterInventory() {
    const search = document.getElementById('inv-search')?.value.toLowerCase() || '';
    const cat    = document.getElementById('inv-cat')?.value || '';
    const filtered = this.state.products.filter(p =>
      (!search || p.name.toLowerCase().includes(search) || p.category.toLowerCase().includes(search)) &&
      (!cat || p.category === cat)
    );
    document.getElementById('inv-body').innerHTML = this.renderInventoryRows(filtered);
  }

  showAddProductModal() {
    this.showProductModal(null);
  }

  async showEditProductModal(productId) {
    const product = this.state.products.find(p => p.id === productId);
    if (product) this.showProductModal(product);
  }

  showProductModal(product) {
    const isEdit = !!product;
    const modal  = this.createModal(`
      <h3>${isEdit ? 'Edit Product' : 'Add Product'}</h3>
      <div id="product-modal-error" class="error-message"></div>
      <form id="product-form">
        <div class="form-group">
          <label for="pname">Product Name</label>
          <input id="pname" placeholder="e.g. Rice 5kg" required value="${isEdit ? this.escape(product.name) : ''}">
        </div>
        <div class="form-group">
          <label for="pcat">Category</label>
          <input id="pcat" placeholder="e.g. Grains" required value="${isEdit ? this.escape(product.category) : ''}">
        </div>
        <div class="form-group">
          <label for="pprice">Price (₱)</label>
          <input id="pprice" type="number" min="0" step="0.01" placeholder="0.00" required value="${isEdit ? product.price : ''}">
        </div>
        <div class="form-group">
          <label for="pqty">Quantity</label>
          <input id="pqty" type="number" min="0" placeholder="0" value="${isEdit ? product.quantity : '0'}">
        </div>
        <div class="form-group">
          <label for="preorder">Reorder Threshold</label>
          <input id="preorder" type="number" min="0" placeholder="10" value="${isEdit ? product.reorder_threshold : '10'}">
          <small>Alert when stock falls to or below this number</small>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
          <button type="submit" class="btn-primary">${isEdit ? 'Save Changes' : 'Add Product'}</button>
        </div>
      </form>
    `);

    modal.querySelector('#product-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn  = e.target.querySelector('[type=submit]');
      const data = {
        name:              document.getElementById('pname').value.trim(),
        category:          document.getElementById('pcat').value.trim(),
        price:             parseFloat(document.getElementById('pprice').value),
        quantity:          parseInt(document.getElementById('pqty').value)    || 0,
        reorder_threshold: parseInt(document.getElementById('preorder').value) || 10,
      };
      btn.disabled = true; btn.textContent = 'Saving…';
      try {
        if (isEdit) {
          await ApiService.updateProduct(product.id, data);
        } else {
          await ApiService.createProduct(data);
        }
        modal.remove();
        await this.loadInitialData();
        this.renderInventory();
      } catch (err) {
        document.getElementById('product-modal-error').textContent = err.message;
        btn.disabled = false; btn.textContent = isEdit ? 'Save Changes' : 'Add Product';
      }
    });
  }

  async confirmDeleteProduct(id, name) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await ApiService.deleteProduct(id);
      await this.loadInitialData();
      this.renderInventory();
    } catch (e) { alert(e.message); }
  }

  // ── SALES ─────────────────────────────────────────────────────────────────

  async renderSales() {
    await this.loadInitialData();
    this.setContent(`
      <div class="page-header">
        <div><h2>Sales</h2><p>Record a sale or view history</p></div>
        <button class="btn-primary" onclick="app.showSellModal(null)">+ Record Sale</button>
      </div>
      <div class="card">
        <div class="card-header">
          <span class="card-title">Recent Transactions</span>
          <span style="font-size:12px;color:var(--text3);font-family:var(--mono)">${this.state.sales.length} records</span>
        </div>
        ${this.renderSalesTable(this.state.sales)}
      </div>
    `);
  }

  renderSalesTable(sales) {
    if (!sales || sales.length === 0) return `<div class="empty-state"><div class="empty-icon">🧾</div><p>No sales recorded yet</p></div>`;
    return `
      <table class="data-table">
        <thead><tr><th>Product</th><th>Qty</th><th>Total</th><th>Date</th></tr></thead>
        <tbody>
          ${sales.map(s => `
            <tr>
              <td><strong>${this.escape(s.product_name)}</strong></td>
              <td style="font-family:var(--mono)">${s.quantity}</td>
              <td style="font-family:var(--mono)">₱${this.fmt(s.total)}</td>
              <td style="color:var(--text3);font-family:var(--mono)">${this.formatDate(s.timestamp)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  showSellModal(productId) {
    const inStockProducts = this.state.products.filter(p => p.quantity > 0);
    if (inStockProducts.length === 0) { alert('No products in stock.'); return; }
    const modal = this.createModal(`
      <h3>Record Sale</h3>
      <div id="sell-error" class="error-message"></div>
      <form id="sell-form">
        <div class="form-group">
          <label for="sell-product">Product</label>
          <select id="sell-product" required>
            ${inStockProducts.map(p =>
              `<option value="${p.id}" ${p.id === productId ? 'selected' : ''}>
                ${this.escape(p.name)} — ${p.quantity} in stock @ ₱${this.fmt(p.price)}
              </option>`
            ).join('')}
          </select>
        </div>
        <div class="form-group">
          <label for="sell-qty">Quantity</label>
          <input id="sell-qty" type="number" min="1" value="1" required>
        </div>
        <div id="sell-total" style="font-family:var(--mono);color:var(--accent);font-size:18px;font-weight:700;margin-bottom:16px">Total: ₱0.00</div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
          <button type="submit" class="btn-primary">Confirm Sale</button>
        </div>
      </form>
    `);

    const updateTotal = () => {
      const sel = document.getElementById('sell-product');
      const qty = parseInt(document.getElementById('sell-qty').value) || 0;
      const prod = this.state.products.find(p => p.id === sel.value);
      if (prod) document.getElementById('sell-total').textContent = `Total: ₱${this.fmt(prod.price * qty)}`;
    };
    modal.querySelector('#sell-product').addEventListener('change', updateTotal);
    modal.querySelector('#sell-qty').addEventListener('input', updateTotal);
    updateTotal();

    modal.querySelector('#sell-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Processing…';
      try {
        await ApiService.createSale({
          product_id: document.getElementById('sell-product').value,
          quantity:   parseInt(document.getElementById('sell-qty').value)
        });
        modal.remove();
        await this.loadInitialData();
        this.renderSales();
      } catch (err) {
        document.getElementById('sell-error').textContent = err.message;
        btn.disabled = false; btn.textContent = 'Confirm Sale';
      }
    });
  }

  // ── REPORTS ───────────────────────────────────────────────────────────────

  async renderReports() {
    this.setContent('<div class="loading">Loading reports</div>');
    try {
      const [summary, topProds, invValue, salesSum] = await Promise.all([
        ApiService.getReportSummary(),
        ApiService.getTopProducts(10),
        ApiService.getInventoryValue(),
        ApiService.getSalesSummary()
      ]);

      this.setContent(`
        <div class="page-header">
          <div><h2>Reports</h2><p>Sales and inventory analytics</p></div>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value">₱${this.fmt(summary.total_revenue)}</div>
            <div class="stat-sub">${summary.total_transactions} transactions</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">Inventory Value</div>
            <div class="stat-value">₱${this.fmt(invValue.grand_total)}</div>
            <div class="stat-sub">${summary.total_products} products</div>
          </div>
          <div class="stat-card ${summary.low_stock_count > 0 ? 'danger' : ''}">
            <div class="stat-label">Low Stock Items</div>
            <div class="stat-value">${summary.low_stock_count}</div>
            <div class="stat-sub">below reorder threshold</div>
          </div>
        </div>

        <div class="report-grid">
          <div class="card">
            <div class="card-header"><span class="card-title">Top Products by Revenue</span></div>
            <div class="bar-chart">${this.renderBarChart(topProds.top_products, 'name', 'revenue', '₱')}</div>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">Top Products by Units Sold</span></div>
            <div class="bar-chart">${this.renderBarChart(topProds.top_products, 'name', 'units_sold')}</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">Inventory Value by Category</span></div>
          <table class="data-table">
            <thead><tr><th>Category</th><th>Products</th><th>Units</th><th>Value</th><th>Low Stock</th></tr></thead>
            <tbody>
              ${invValue.by_category.map(c => `
                <tr>
                  <td><strong>${this.escape(c.category)}</strong></td>
                  <td style="font-family:var(--mono)">${c.product_count}</td>
                  <td style="font-family:var(--mono)">${c.total_units}</td>
                  <td style="font-family:var(--mono)">₱${this.fmt(c.total_value)}</td>
                  <td>${c.low_stock_count > 0 ? `<span class="badge badge-low">${c.low_stock_count}</span>` : '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Daily Sales (Last 30 Days)</span>
          </div>
          ${this.renderDailySalesTable(salesSum.sales_summary)}
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load reports: ${e.message}</div>`);
    }
  }

  renderDailySalesTable(rows) {
    if (!rows || rows.length === 0) return '<div class="empty-state"><div class="empty-icon">📊</div><p>No sales data yet</p></div>';
    return `
      <table class="data-table">
        <thead><tr><th>Date</th><th>Transactions</th><th>Revenue</th></tr></thead>
        <tbody>
          ${rows.map(r => `
            <tr>
              <td style="font-family:var(--mono)">${r.day}</td>
              <td style="font-family:var(--mono)">${r.transactions}</td>
              <td style="font-family:var(--mono)">₱${this.fmt(r.revenue)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  // ── LOGS ──────────────────────────────────────────────────────────────────

  async renderLogs(page = 1) {
    this.setContent('<div class="loading">Loading audit log</div>');
    try {
      const action    = this._logFilters?.action    || '';
      const date_from = this._logFilters?.date_from || '';
      const date_to   = this._logFilters?.date_to   || '';

      const data = await ApiService.getLogs({ page, per_page: 50, action, date_from, date_to });
      const { logs, pagination } = data;

      this.setContent(`
        <div class="page-header">
          <div><h2>Audit Log</h2><p>All system actions</p></div>
        </div>
        <div class="card">
          <div class="filter-bar">
            <select id="log-action" onchange="app._logFilters={...app._logFilters||{},action:this.value};app.renderLogs(1)">
              <option value="">All Actions</option>
              ${['LOGIN','LOGOUT','CREATE_PRODUCT','EDIT_PRODUCT','DELETE_PRODUCT','SALE','CREATE_USER','DELETE_USER','BACKUP_CREATED','SETUP_COMPLETED']
                .map(a => `<option value="${a}" ${action===a?'selected':''}>${a}</option>`).join('')}
            </select>
            <input type="date" id="log-from" value="${date_from}"
              onchange="app._logFilters={...app._logFilters||{},date_from:this.value};app.renderLogs(1)"
              placeholder="From date">
            <input type="date" id="log-to" value="${date_to}"
              onchange="app._logFilters={...app._logFilters||{},date_to:this.value};app.renderLogs(1)"
              placeholder="To date">
            <button class="btn-ghost" onclick="app._logFilters={};app.renderLogs(1)">Clear</button>
          </div>
          <table class="data-table">
            <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Details</th></tr></thead>
            <tbody>
              ${logs.length === 0
                ? `<tr><td colspan="4" style="text-align:center;color:var(--text3);padding:32px">No log entries found</td></tr>`
                : logs.map(l => `
                  <tr>
                    <td style="font-family:var(--mono);color:var(--text3)">${this.formatDate(l.timestamp)}</td>
                    <td><strong>${this.escape(l.username || '—')}</strong></td>
                    <td><span class="badge badge-action">${l.action}</span></td>
                    <td style="color:var(--text2)">${this.escape(l.details || '')}</td>
                  </tr>
                `).join('')}
            </tbody>
          </table>
          <div class="pagination">
            <button onclick="app.renderLogs(${pagination.page - 1})" ${pagination.page <= 1 ? 'disabled' : ''}>← Prev</button>
            <span>Page ${pagination.page} of ${pagination.pages} (${pagination.total} entries)</span>
            <button onclick="app.renderLogs(${pagination.page + 1})" ${pagination.page >= pagination.pages ? 'disabled' : ''}>Next →</button>
          </div>
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load logs: ${e.message}</div>`);
    }
  }

  // ── USERS ─────────────────────────────────────────────────────────────────

  async renderUsers() {
    this.setContent('<div class="loading">Loading users</div>');
    try {
      const data = await ApiService.getUsers();
      const users = data.users || [];

      this.setContent(`
        <div class="page-header">
          <div><h2>Users</h2><p>${users.length} accounts</p></div>
          <button class="btn-primary" onclick="app.showAddUserModal()">+ Add User</button>
        </div>
        <div class="card">
          <table class="data-table">
            <thead><tr><th>Username</th><th>Role</th><th>Created</th><th>Actions</th></tr></thead>
            <tbody>
              ${users.map(u => `
                <tr>
                  <td>
                    <strong>${this.escape(u.username)}</strong>
                    ${u.id === auth.user?.id ? '<span class="badge badge-admin" style="margin-left:8px">You</span>' : ''}
                  </td>
                  <td><span class="badge badge-${u.role}">${u.role}</span></td>
                  <td style="color:var(--text3);font-family:var(--mono)">${this.formatDate(u.created_at)}</td>
                  <td>
                    ${u.id !== auth.user?.id
                      ? `<button class="btn-danger btn-small" onclick="app.confirmDeleteUser('${u.id}','${this.escape(u.username)}')">Remove</button>`
                      : '—'}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load users: ${e.message}</div>`);
    }
  }

  showAddUserModal() {
    const modal = this.createModal(`
      <h3>Add New User</h3>
      <div id="user-modal-error" class="error-message"></div>
      <form id="add-user-form">
        <div class="form-group">
          <label for="new-username">Username</label>
          <input type="text" id="new-username" placeholder="Username" required minlength="3" autocomplete="off">
        </div>
        <div class="form-group">
          <label for="new-password">Password</label>
          <input type="password" id="new-password" placeholder="Min 8 characters" required minlength="8">
          <small>At least 8 characters, must include a letter and a number</small>
        </div>
        <div class="form-group">
          <label for="new-role">Role</label>
          <select id="new-role">
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
          <button type="submit" class="btn-primary">Add User</button>
        </div>
      </form>
    `);

    modal.querySelector('#add-user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Adding…';
      try {
        await ApiService.createUser({
          username: document.getElementById('new-username').value.trim(),
          password: document.getElementById('new-password').value,
          role:     document.getElementById('new-role').value
        });
        modal.remove();
        this.renderUsers();
      } catch (err) {
        document.getElementById('user-modal-error').textContent = err.message;
        btn.disabled = false; btn.textContent = 'Add User';
      }
    });
  }

  async confirmDeleteUser(id, username) {
    if (!confirm(`Remove user "${username}"? This cannot be undone.`)) return;
    try {
      await ApiService.deleteUser(id);
      this.renderUsers();
    } catch (e) { alert(e.message); }
  }

  // ── BACKUP ────────────────────────────────────────────────────────────────

  async renderBackup() {
    this.setContent('<div class="loading">Loading backup status</div>');
    try {
      const data = await ApiService.listBackups();
      const backups = data.backups || [];

      this.setContent(`
        <div class="page-header">
          <div><h2>Backup</h2><p>Database backup and recovery</p></div>
        </div>

        <div class="alert alert-info">
          💡 Backups contain all products, sales, users, and logs. Store them securely.
        </div>

        <div class="card" style="margin-bottom:16px">
          <div class="card-header"><span class="card-title">Actions</span></div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <button class="btn-primary" onclick="app.downloadBackup()">⬇ Download Live Database</button>
            <button class="btn-ghost" id="create-backup-btn" onclick="app.createBackup()">💾 Save Dated Backup</button>
          </div>
          <p style="margin-top:12px;font-size:12px;color:var(--text3)">
            "Download" gives you the current database file directly.<br>
            "Save Dated Backup" creates a timestamped copy on the server.
          </p>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Saved Backups</span>
            <button class="btn-ghost" onclick="app.renderBackup()">↺ Refresh</button>
          </div>
          ${backups.length === 0
            ? `<div class="empty-state"><div class="empty-icon">💾</div><p>No saved backups yet. Click "Save Dated Backup" to create one.</p></div>`
            : backups.map(b => `
              <div class="backup-item">
                <div>
                  <div class="backup-name">${this.escape(b.filename)}</div>
                  <div class="backup-meta">${b.size_kb} KB · ${b.created}</div>
                </div>
              </div>
            `).join('')}
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load backup info: ${e.message}</div>`);
    }
  }

  downloadBackup() {
    window.location.href = ApiService.downloadBackupUrl();
  }

  async createBackup() {
    const btn = document.getElementById('create-backup-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }
    try {
      const res = await ApiService.createBackup();
      alert(`Backup saved: ${res.filename}`);
      this.renderBackup();
    } catch (e) {
      alert('Backup failed: ' + e.message);
      if (btn) { btn.disabled = false; btn.textContent = '💾 Save Dated Backup'; }
    }
  }

  // ── HELPERS ───────────────────────────────────────────────────────────────

  createModal(innerHTML) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `<div class="modal-content">${innerHTML}</div>`;
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
    document.body.appendChild(modal);
    return modal;
  }

  escape(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  fmt(num) {
    return Number(num || 0).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  formatDate(ts) {
    if (!ts) return '—';
    return new Date(ts).toLocaleString('en-PH', { dateStyle: 'medium', timeStyle: 'short' });
  }
}

let app;
document.addEventListener('DOMContentLoaded', () => { app = new ShopKeepApp(); });
