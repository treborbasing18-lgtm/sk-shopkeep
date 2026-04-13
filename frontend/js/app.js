class ShopKeepApp {
  constructor() {
    this.state = { products: [], sales: [], stats: null };
    this.currentView = 'dashboard';
    this._logFilters = {};
    this._moreMenuOpen = false;
    this.init();
  }

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

        <!-- Mobile top bar -->
        <div class="top-bar">
          <div class="top-bar-title">SK ShopKeep</div>
          <div class="top-bar-user">
            <strong>${this.escape(auth.user?.username)}</strong>
            ${auth.user?.role}
          </div>
        </div>

        <!-- Desktop sidebar (hidden on mobile via CSS) -->
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
            <button class="btn-secondary" id="logout-btn-sidebar">Sign Out</button>
          </div>
        </div>

        <!-- Main content -->
        <div class="main-content" id="main-content"></div>

        <!-- Mobile bottom nav -->
        <nav class="bottom-nav">
          <div class="nav-item" data-view="dashboard">
            <span class="nav-icon">⬛</span>
            <span>Home</span>
          </div>
          <div class="nav-item" data-view="inventory">
            <span class="nav-icon">📦</span>
            <span>Inventory</span>
          </div>
          <div class="nav-item" data-view="sales">
            <span class="nav-icon">🧾</span>
            <span>Sales</span>
          </div>
          <div class="nav-item" data-view="reports">
            <span class="nav-icon">📊</span>
            <span>Reports</span>
          </div>
          <div class="nav-item" id="more-btn">
            <span class="nav-icon">☰</span>
            <span>More</span>
          </div>
        </nav>
      </div>
    `;

    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
      el.addEventListener('click', () => this.navigateTo(el.dataset.view));
    });

    document.getElementById('more-btn')?.addEventListener('click', () => this.toggleMoreMenu());
    document.getElementById('logout-btn-sidebar')?.addEventListener('click', () => this.doLogout());
  }

  toggleMoreMenu() {
    const existing = document.getElementById('more-menu');
    if (existing) { existing.remove(); document.getElementById('more-overlay')?.remove(); return; }

    const isAdmin = auth.isAdmin;
    const overlay = document.createElement('div');
    overlay.className = 'more-menu-overlay';
    overlay.id = 'more-overlay';
    overlay.addEventListener('click', () => { menu.remove(); overlay.remove(); });

    const menu = document.createElement('div');
    menu.className = 'more-menu';
    menu.id = 'more-menu';
    menu.innerHTML = `
      ${isAdmin ? `
      <div class="more-menu-item" data-view="logs"><span class="nav-icon">🗒️</span> Audit Log</div>
      <div class="more-menu-item" data-view="users"><span class="nav-icon">👥</span> Users</div>
      <div class="more-menu-item" data-view="backup"><span class="nav-icon">💾</span> Backup</div>
      ` : ''}
      <div class="more-menu-item" id="logout-more"><span class="nav-icon">🚪</span> Sign Out</div>
    `;

    menu.querySelectorAll('[data-view]').forEach(el => {
      el.addEventListener('click', () => {
        menu.remove(); overlay.remove();
        this.navigateTo(el.dataset.view);
      });
    });
    menu.querySelector('#logout-more')?.addEventListener('click', () => this.doLogout());

    document.body.appendChild(overlay);
    document.body.appendChild(menu);
  }

  async doLogout() {
    await auth.logout();
    this.showLogin();
  }

  navigateTo(view) {
    this.currentView = view;
    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
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
            <input type="text" id="login-username" placeholder="Username" required autocomplete="username">
            <label for="login-password" style="display:none">Password</label>
            <input type="password" id="login-password" placeholder="Password" required autocomplete="current-password">
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
        <div class="auth-box">
          <h2>Welcome to SK ShopKeep</h2>
          <p>Create your administrator account to get started</p>
          <div id="setup-error" class="error-message"></div>
          <form id="setup-form">
            <div class="form-group">
              <label for="setup-username">Admin Username</label>
              <input type="text" id="setup-username" placeholder="Choose a username" required minlength="3" autocomplete="username">
              <small>At least 3 characters, letters/numbers/underscores only</small>
            </div>
            <div class="form-group">
              <label for="setup-password">Password</label>
              <input type="password" id="setup-password" placeholder="Min 8 characters" required minlength="8" autocomplete="new-password">
              <small>At least 8 characters with a letter and a number</small>
            </div>
            <div class="form-group">
              <label for="setup-confirm">Confirm Password</label>
              <input type="password" id="setup-confirm" placeholder="Re-enter your password" required autocomplete="new-password">
            </div>
            <button type="submit" style="width:100%;margin-top:8px">Create Admin Account</button>
          </form>
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
        const res  = await fetch('/api/auth/setup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
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
        ApiService.getReportSummary(), ApiService.getTopProducts(5)
      ]);
      const lowStock = this.state.products.filter(p => p.quantity <= p.reorder_threshold);
      this.setContent(`
        <div class="page-header">
          <div><h2>Dashboard</h2><p>Overview</p></div>
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
            <div class="stat-sub">${summary.total_stock} units</div>
          </div>
          <div class="stat-card ${summary.low_stock_count > 0 ? 'danger' : ''}">
            <div class="stat-label">Low Stock</div>
            <div class="stat-value">${summary.low_stock_count}</div>
            <div class="stat-sub">below threshold</div>
          </div>
        </div>
        ${lowStock.length > 0 ? `
        <div class="alert alert-error">
          ⚠️ Low stock: ${lowStock.map(p => `<strong>${this.escape(p.name)}</strong> (${p.quantity})`).join(', ')}
        </div>` : ''}
        <div class="card">
          <div class="card-header">
            <span class="card-title">Top Products</span>
            <button class="btn-ghost" onclick="app.navigateTo('reports')">Report →</button>
          </div>
          <div class="bar-chart">${this.renderBarChart(topProds.top_products, 'name', 'revenue', '₱')}</div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Recent Sales</span>
            <button class="btn-ghost" onclick="app.navigateTo('sales')">All →</button>
          </div>
          ${this.renderSalesRows(this.state.sales.slice(0, 6))}
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load: ${e.message}</div>`);
    }
  }

  renderBarChart(rows, labelKey, valueKey, prefix = '') {
    if (!rows || rows.length === 0) return '<p style="color:var(--text3);font-size:13px;padding:8px 0">No data yet.</p>';
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
        <button class="btn-primary" onclick="app.showProductModal(null)">+ Add</button>
      </div>
      <div class="card">
        <div class="filter-bar">
          <input type="search" id="inv-search" placeholder="Search…" oninput="app.filterInventory()">
          <select id="inv-cat" onchange="app.filterInventory()">
            <option value="">All</option>
            ${[...new Set(this.state.products.map(p => p.category))].map(c =>
              `<option value="${this.escape(c)}">${this.escape(c)}</option>`
            ).join('')}
          </select>
        </div>
        <div id="inv-list">${this.renderInventoryRows(this.state.products)}</div>
      </div>
    `);
  }

  renderInventoryRows(products) {
    if (products.length === 0) return `<div class="empty-state"><div class="empty-icon">📦</div><p>No products found</p></div>`;
    return products.map(p => {
      const low = p.quantity <= p.reorder_threshold;
      return `
        <div class="list-row ${low ? 'low-stock-row' : ''}">
          <div class="list-row-main">
            <div class="list-row-name">${this.escape(p.name)}</div>
            <div class="list-row-sub">
              ${this.escape(p.category)} · ₱${this.fmt(p.price)} ·
              <span class="badge ${low ? 'badge-low' : 'badge-ok'}">${p.quantity} left</span>
            </div>
          </div>
          <div class="list-row-actions">
            <button class="btn-ghost btn-small" onclick="app.showProductModal(${JSON.stringify(p).replace(/"/g, '&quot;')})">Edit</button>
            <button class="btn-primary btn-small" onclick="app.showSellModal('${p.id}')" ${p.quantity === 0 ? 'disabled' : ''}>Sell</button>
          </div>
        </div>
      `;
    }).join('');
  }

  filterInventory() {
    const search   = document.getElementById('inv-search')?.value.toLowerCase() || '';
    const cat      = document.getElementById('inv-cat')?.value || '';
    const filtered = this.state.products.filter(p =>
      (!search || p.name.toLowerCase().includes(search) || p.category.toLowerCase().includes(search)) &&
      (!cat || p.category === cat)
    );
    document.getElementById('inv-list').innerHTML = this.renderInventoryRows(filtered);
  }

  showProductModal(product) {
    const isEdit = !!product;
    const modal  = this.createModal(`
      <div class="modal-handle"></div>
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
          <input id="pprice" type="number" inputmode="decimal" min="0" step="0.01" placeholder="0.00" required value="${isEdit ? product.price : ''}">
        </div>
        <div class="form-group">
          <label for="pqty">Quantity</label>
          <input id="pqty" type="number" inputmode="numeric" min="0" placeholder="0" value="${isEdit ? product.quantity : '0'}">
        </div>
        <div class="form-group">
          <label for="preorder">Reorder Threshold</label>
          <input id="preorder" type="number" inputmode="numeric" min="0" placeholder="10" value="${isEdit ? product.reorder_threshold : '10'}">
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
          ${isEdit && auth.isAdmin ? `<button type="button" class="btn-danger" onclick="app.confirmDeleteProduct('${product.id}','${this.escape(product.name)}');this.closest('.modal').remove()">Delete</button>` : ''}
          <button type="submit" class="btn-primary">${isEdit ? 'Save' : 'Add Product'}</button>
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
        isEdit ? await ApiService.updateProduct(product.id, data) : await ApiService.createProduct(data);
        modal.remove();
        await this.loadInitialData();
        this.renderInventory();
      } catch (err) {
        document.getElementById('product-modal-error').textContent = err.message;
        btn.disabled = false; btn.textContent = isEdit ? 'Save' : 'Add Product';
      }
    });
  }

  async confirmDeleteProduct(id, name) {
    if (!confirm(`Delete "${name}"?`)) return;
    try { await ApiService.deleteProduct(id); await this.loadInitialData(); this.renderInventory(); }
    catch (e) { alert(e.message); }
  }

  // ── SALES ─────────────────────────────────────────────────────────────────

  async renderSales() {
    await this.loadInitialData();
    this.setContent(`
      <div class="page-header">
        <div><h2>Sales</h2><p>History &amp; record</p></div>
        <button class="btn-primary" onclick="app.showSellModal(null)">+ Sale</button>
      </div>
      <div class="card">
        <div class="card-header">
          <span class="card-title">Recent Transactions</span>
        </div>
        ${this.renderSalesRows(this.state.sales)}
      </div>
    `);
  }

  renderSalesRows(sales) {
    if (!sales || sales.length === 0) return `<div class="empty-state"><div class="empty-icon">🧾</div><p>No sales yet</p></div>`;
    return sales.map(s => `
      <div class="list-row">
        <div class="list-row-main">
          <div class="list-row-name">${this.escape(s.product_name)}</div>
          <div class="list-row-sub">${this.formatDate(s.timestamp)} · qty ${s.quantity}</div>
        </div>
        <div style="font-family:var(--mono);font-weight:700;color:var(--accent);white-space:nowrap">₱${this.fmt(s.total)}</div>
      </div>
    `).join('');
  }

  showSellModal(productId) {
    const inStock = this.state.products.filter(p => p.quantity > 0);
    if (inStock.length === 0) { alert('No products in stock.'); return; }
    const modal = this.createModal(`
      <div class="modal-handle"></div>
      <h3>Record Sale</h3>
      <div id="sell-error" class="error-message"></div>
      <form id="sell-form">
        <div class="form-group">
          <label for="sell-product">Product</label>
          <select id="sell-product" required>
            ${inStock.map(p =>
              `<option value="${p.id}" ${p.id === productId ? 'selected' : ''}>
                ${this.escape(p.name)} (${p.quantity} left)
              </option>`
            ).join('')}
          </select>
        </div>
        <div class="form-group">
          <label for="sell-qty">Quantity</label>
          <input id="sell-qty" type="number" inputmode="numeric" min="1" value="1" required>
        </div>
        <div class="sell-total" id="sell-total">Total: ₱0.00</div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
          <button type="submit" class="btn-primary">Confirm Sale</button>
        </div>
      </form>
    `);
    const updateTotal = () => {
      const prod = this.state.products.find(p => p.id === document.getElementById('sell-product').value);
      const qty  = parseInt(document.getElementById('sell-qty').value) || 0;
      document.getElementById('sell-total').textContent = `Total: ₱${this.fmt((prod?.price || 0) * qty)}`;
    };
    modal.querySelector('#sell-product').addEventListener('change', updateTotal);
    modal.querySelector('#sell-qty').addEventListener('input', updateTotal);
    updateTotal();
    modal.querySelector('#sell-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Processing…';
      try {
        await ApiService.createSale({ product_id: document.getElementById('sell-product').value, quantity: parseInt(document.getElementById('sell-qty').value) });
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
        ApiService.getReportSummary(), ApiService.getTopProducts(8),
        ApiService.getInventoryValue(), ApiService.getSalesSummary()
      ]);
      this.setContent(`
        <div class="page-header"><div><h2>Reports</h2><p>Analytics</p></div></div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Revenue</div>
            <div class="stat-value">₱${this.fmt(summary.total_revenue)}</div>
            <div class="stat-sub">${summary.total_transactions} transactions</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">Inventory</div>
            <div class="stat-value">₱${this.fmt(invValue.grand_total)}</div>
            <div class="stat-sub">${summary.total_products} products</div>
          </div>
          <div class="stat-card ${summary.low_stock_count > 0 ? 'danger' : ''}">
            <div class="stat-label">Low Stock</div>
            <div class="stat-value">${summary.low_stock_count}</div>
            <div class="stat-sub">items</div>
          </div>
        </div>
        <div class="report-grid">
          <div class="card">
            <div class="card-header"><span class="card-title">Top by Revenue</span></div>
            <div class="bar-chart">${this.renderBarChart(topProds.top_products, 'name', 'revenue', '₱')}</div>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">Top by Units</span></div>
            <div class="bar-chart">${this.renderBarChart(topProds.top_products, 'name', 'units_sold')}</div>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Inventory by Category</span></div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Category</th><th>Units</th><th>Value</th><th>Low</th></tr></thead>
              <tbody>
                ${invValue.by_category.map(c => `
                  <tr>
                    <td><strong>${this.escape(c.category)}</strong></td>
                    <td style="font-family:var(--mono)">${c.total_units}</td>
                    <td style="font-family:var(--mono)">₱${this.fmt(c.total_value)}</td>
                    <td>${c.low_stock_count > 0 ? `<span class="badge badge-low">${c.low_stock_count}</span>` : '—'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Daily Sales (30 days)</span></div>
          <div class="table-wrap">
            <table class="data-table">
              <thead><tr><th>Date</th><th>Txns</th><th>Revenue</th></tr></thead>
              <tbody>
                ${(salesSum.sales_summary || []).length === 0
                  ? `<tr><td colspan="3" style="text-align:center;color:var(--text3);padding:24px">No data yet</td></tr>`
                  : (salesSum.sales_summary || []).map(r => `
                    <tr>
                      <td style="font-family:var(--mono)">${r.day}</td>
                      <td style="font-family:var(--mono)">${r.transactions}</td>
                      <td style="font-family:var(--mono)">₱${this.fmt(r.revenue)}</td>
                    </tr>
                  `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load: ${e.message}</div>`);
    }
  }

  // ── LOGS ──────────────────────────────────────────────────────────────────

  async renderLogs(page = 1) {
    this.setContent('<div class="loading">Loading audit log</div>');
    try {
      const { action = '', date_from = '', date_to = '' } = this._logFilters;
      const data = await ApiService.getLogs({ page, per_page: 30, action, date_from, date_to });
      const { logs, pagination } = data;
      this.setContent(`
        <div class="page-header"><div><h2>Audit Log</h2><p>All actions</p></div></div>
        <div class="card">
          <div class="filter-bar">
            <select id="log-action" onchange="app._logFilters={...app._logFilters,action:this.value};app.renderLogs(1)">
              <option value="">All Actions</option>
              ${['LOGIN','LOGOUT','CREATE_PRODUCT','EDIT_PRODUCT','DELETE_PRODUCT','SALE','CREATE_USER','DELETE_USER','BACKUP_CREATED'].map(a =>
                `<option value="${a}" ${action===a?'selected':''}>${a}</option>`
              ).join('')}
            </select>
            <input type="date" value="${date_from}" onchange="app._logFilters={...app._logFilters,date_from:this.value};app.renderLogs(1)">
            <input type="date" value="${date_to}"   onchange="app._logFilters={...app._logFilters,date_to:this.value};app.renderLogs(1)">
          </div>
          ${logs.length === 0
            ? `<div class="empty-state"><div class="empty-icon">🗒️</div><p>No entries found</p></div>`
            : logs.map(l => `
              <div class="list-row">
                <div class="list-row-main">
                  <div class="list-row-name">
                    <span class="badge badge-action">${l.action}</span>
                    <span style="margin-left:8px;font-weight:600">${this.escape(l.username || '—')}</span>
                  </div>
                  <div class="list-row-sub">${this.escape(l.details || '')} · ${this.formatDate(l.timestamp)}</div>
                </div>
              </div>
            `).join('')}
          <div class="pagination">
            <button onclick="app.renderLogs(${pagination.page-1})" ${pagination.page<=1?'disabled':''}>← Prev</button>
            <span>${pagination.page} / ${pagination.pages}</span>
            <button onclick="app.renderLogs(${pagination.page+1})" ${pagination.page>=pagination.pages?'disabled':''}>Next →</button>
          </div>
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed to load: ${e.message}</div>`);
    }
  }

  // ── USERS ─────────────────────────────────────────────────────────────────

  async renderUsers() {
    this.setContent('<div class="loading">Loading users</div>');
    try {
      const { users = [] } = await ApiService.getUsers();
      this.setContent(`
        <div class="page-header">
          <div><h2>Users</h2><p>${users.length} accounts</p></div>
          <button class="btn-primary" onclick="app.showAddUserModal()">+ Add</button>
        </div>
        <div class="card">
          ${users.map(u => `
            <div class="list-row">
              <div class="list-row-main">
                <div class="list-row-name">
                  ${this.escape(u.username)}
                  ${u.id === auth.user?.id ? '<span class="badge badge-admin" style="margin-left:6px">You</span>' : ''}
                </div>
                <div class="list-row-sub"><span class="badge badge-${u.role}">${u.role}</span> · ${this.formatDate(u.created_at)}</div>
              </div>
              ${u.id !== auth.user?.id ? `<button class="btn-danger btn-small" onclick="app.confirmDeleteUser('${u.id}','${this.escape(u.username)}')">Remove</button>` : ''}
            </div>
          `).join('')}
        </div>
      `);
    } catch (e) {
      this.setContent(`<div class="alert alert-error">Failed: ${e.message}</div>`);
    }
  }

  showAddUserModal() {
    const modal = this.createModal(`
      <div class="modal-handle"></div>
      <h3>Add User</h3>
      <div id="user-modal-error" class="error-message"></div>
      <form id="add-user-form">
        <div class="form-group">
          <label for="new-username">Username</label>
          <input type="text" id="new-username" placeholder="Username" required minlength="3" autocomplete="off">
        </div>
        <div class="form-group">
          <label for="new-password">Password</label>
          <input type="password" id="new-password" placeholder="Min 8 characters" required minlength="8" autocomplete="new-password">
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
        modal.remove(); this.renderUsers();
      } catch (err) {
        document.getElementById('user-modal-error').textContent = err.message;
        btn.disabled = false; btn.textContent = 'Add User';
      }
    });
  }

  async confirmDeleteUser(id, username) {
    if (!confirm(`Remove "${username}"?`)) return;
    try { await ApiService.deleteUser(id); this.renderUsers(); }
    catch (e) { alert(e.message); }
  }

  // ── BACKUP ────────────────────────────────────────────────────────────────

  async renderBackup() {
    this.setContent('<div class="loading">Loading backup info</div>');
    try {
      const { backups = [] } = await ApiService.listBackups();
      this.setContent(`
        <div class="page-header"><div><h2>Backup</h2><p>Database recovery</p></div></div>
        <div class="alert alert-info">💡 Backups contain all products, sales, users, and logs.</div>
        <div class="card" style="margin-bottom:14px">
          <div class="card-header"><span class="card-title">Actions</span></div>
          <div style="display:flex;flex-direction:column;gap:10px">
            <button class="btn-primary" onclick="app.downloadBackup()">⬇ Download Live Database</button>
            <button class="btn-ghost" id="create-backup-btn" onclick="app.createBackup()">💾 Save Dated Backup</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Saved Backups</span>
            <button class="btn-ghost" onclick="app.renderBackup()">↺</button>
          </div>
          ${backups.length === 0
            ? `<div class="empty-state"><div class="empty-icon">💾</div><p>No saved backups yet</p></div>`
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
      this.setContent(`<div class="alert alert-error">Failed: ${e.message}</div>`);
    }
  }

  downloadBackup() { window.location.href = ApiService.downloadBackupUrl(); }

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
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
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
