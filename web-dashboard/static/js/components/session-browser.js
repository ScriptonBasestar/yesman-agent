/**
 * SessionBrowser Component
 * Web component for browsing and managing tmux sessions
 */
class SessionBrowser extends HTMLElement {
    constructor() {
        super();
        this.sessions = [];
        this.viewMode = this.getStoredViewMode() || 'list';
        this.refreshInterval = null;
    }

    connectedCallback() {
        this.render();
        this.bindEvents();
        this.loadSessions();
        
        // Auto-refresh every 5 seconds
        this.refreshInterval = setInterval(() => this.loadSessions(), 5000);
    }

    disconnectedCallback() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    getStoredViewMode() {
        return localStorage.getItem('session-browser-view-mode');
    }

    setStoredViewMode(mode) {
        localStorage.setItem('session-browser-view-mode', mode);
    }

    async loadSessions() {
        try {
            const response = await axios.get('/web/api/sessions');
            this.sessions = response.data;
            this.renderSessions();
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.renderError('Failed to load sessions');
        }
    }

    changeViewMode(mode) {
        if (['list', 'grid', 'tree'].includes(mode)) {
            this.viewMode = mode;
            this.setStoredViewMode(mode);
            this.updateViewModeButtons();
            this.renderSessions();
        }
    }

    bindEvents() {
        // View mode buttons
        this.addEventListener('click', (e) => {
            if (e.target.matches('[data-view-mode]')) {
                const mode = e.target.dataset.viewMode;
                this.changeViewMode(mode);
            }
            
            // Session action buttons
            if (e.target.matches('[data-action]')) {
                const action = e.target.dataset.action;
                const sessionName = e.target.dataset.sessionName;
                this.handleSessionAction(action, sessionName);
            }
        });
    }

    async handleSessionAction(action, sessionName) {
        try {
            switch (action) {
                case 'enter':
                    await this.enterSession(sessionName);
                    break;
                case 'stop':
                    await this.stopSession(sessionName);
                    break;
                case 'refresh':
                    await this.loadSessions();
                    break;
                default:
                    console.warn('Unknown action:', action);
            }
        } catch (error) {
            console.error(`Failed to ${action} session:`, error);
        }
    }

    async enterSession(sessionName) {
        try {
            const response = await axios.post(`/web/api/sessions/${sessionName}/enter`);
            if (response.data.success) {
                // Show success notification
                this.showNotification(`Entered session: ${sessionName}`, 'success');
            }
        } catch (error) {
            this.showNotification(`Failed to enter session: ${sessionName}`, 'error');
        }
    }

    async stopSession(sessionName) {
        if (confirm(`Are you sure you want to stop session "${sessionName}"?`)) {
            try {
                const response = await axios.post(`/web/api/sessions/${sessionName}/stop`);
                if (response.data.success) {
                    this.showNotification(`Stopped session: ${sessionName}`, 'success');
                    await this.loadSessions();
                }
            } catch (error) {
                this.showNotification(`Failed to stop session: ${sessionName}`, 'error');
            }
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} fixed top-4 right-4 px-4 py-2 rounded-md text-white z-50`;
        notification.style.backgroundColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    render() {
        this.innerHTML = `
            <div class="session-browser">
                <!-- View Mode Controls -->
                <div class="mb-4 flex justify-between items-center">
                    <div class="view-mode-controls flex space-x-2">
                        <button 
                            data-view-mode="list"
                            class="view-mode-btn px-3 py-1 text-sm rounded-md border ${this.viewMode === 'list' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
                        >
                            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                            </svg>
                            List
                        </button>
                        <button 
                            data-view-mode="grid"
                            class="view-mode-btn px-3 py-1 text-sm rounded-md border ${this.viewMode === 'grid' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
                        >
                            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
                            </svg>
                            Grid
                        </button>
                        <button 
                            data-view-mode="tree"
                            class="view-mode-btn px-3 py-1 text-sm rounded-md border ${this.viewMode === 'tree' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}"
                        >
                            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                            </svg>
                            Tree
                        </button>
                    </div>
                    <button 
                        data-action="refresh"
                        class="refresh-btn px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md border border-gray-300 hover:bg-gray-200"
                    >
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Refresh
                    </button>
                </div>

                <!-- Sessions Container -->
                <div class="sessions-container">
                    <div class="loading text-center py-8 text-gray-500">
                        <svg class="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading sessions...
                    </div>
                </div>
            </div>
        `;
    }

    updateViewModeButtons() {
        const buttons = this.querySelectorAll('[data-view-mode]');
        buttons.forEach(btn => {
            const mode = btn.dataset.viewMode;
            if (mode === this.viewMode) {
                btn.className = btn.className.replace(/bg-white.*?hover:bg-gray-50/, 'bg-blue-600 text-white border-blue-600');
            } else {
                btn.className = btn.className.replace(/bg-blue-600.*?border-blue-600/, 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50');
            }
        });
    }

    renderSessions() {
        const container = this.querySelector('.sessions-container');
        
        if (!this.sessions || this.sessions.length === 0) {
            container.innerHTML = `
                <div class="empty-state text-center py-8">
                    <svg class="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No Sessions Found</h3>
                    <p class="text-gray-500">No tmux sessions are currently running.</p>
                </div>
            `;
            return;
        }

        switch (this.viewMode) {
            case 'list':
                container.innerHTML = this.renderListView();
                break;
            case 'grid':
                container.innerHTML = this.renderGridView();
                break;
            case 'tree':
                container.innerHTML = this.renderTreeView();
                break;
        }
    }

    renderListView() {
        return `
            <div class="list-view space-y-2">
                ${this.sessions.map(session => `
                    <div class="session-item p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <div class="flex-shrink-0">
                                    <div class="w-3 h-3 rounded-full ${session.exists ? 'bg-green-500' : 'bg-gray-400'}"></div>
                                </div>
                                <div>
                                    <h3 class="text-lg font-medium text-gray-900">${session.session_name}</h3>
                                    <p class="text-sm text-gray-500">
                                        Project: ${session.project_name} | 
                                        Template: ${session.template} | 
                                        Status: ${session.status}
                                    </p>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                ${this.renderActionButtons(session)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderGridView() {
        return `
            <div class="grid-view grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${this.sessions.map(session => `
                    <div class="session-card p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                        <div class="flex items-center justify-between mb-3">
                            <div class="w-3 h-3 rounded-full ${session.exists ? 'bg-green-500' : 'bg-gray-400'}"></div>
                            <span class="text-xs px-2 py-1 rounded-full ${session.exists ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                                ${session.status}
                            </span>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">${session.session_name}</h3>
                        <div class="text-sm text-gray-500 mb-4">
                            <div>Project: ${session.project_name}</div>
                            <div>Template: ${session.template}</div>
                            <div>Windows: ${session.windows ? session.windows.length : 0}</div>
                        </div>
                        <div class="flex space-x-2">
                            ${this.renderActionButtons(session)}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderTreeView() {
        return `
            <div class="tree-view space-y-4">
                ${this.sessions.map(session => `
                    <div class="session-tree border border-gray-200 rounded-lg">
                        <div class="session-header p-4 bg-gray-50 border-b border-gray-200">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-3">
                                    <div class="w-3 h-3 rounded-full ${session.exists ? 'bg-green-500' : 'bg-gray-400'}"></div>
                                    <h3 class="text-lg font-medium text-gray-900">${session.session_name}</h3>
                                    <span class="text-sm text-gray-500">(${session.project_name})</span>
                                </div>
                                <div class="flex space-x-2">
                                    ${this.renderActionButtons(session)}
                                </div>
                            </div>
                        </div>
                        <div class="windows-list p-4">
                            ${session.windows && session.windows.length > 0 ? `
                                <div class="space-y-2">
                                    ${session.windows.map((window, index) => `
                                        <div class="window-item pl-4 border-l-2 border-gray-200">
                                            <div class="font-medium text-gray-700">Window ${window.index}: ${window.name}</div>
                                            ${window.panes && window.panes.length > 0 ? `
                                                <div class="panes-list mt-2 pl-4 space-y-1">
                                                    ${window.panes.map(pane => `
                                                        <div class="pane-item text-sm text-gray-600">
                                                            📄 ${pane.command} ${pane.is_claude ? '(Claude)' : ''} ${pane.is_controller ? '(Controller)' : ''}
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            ` : `
                                <div class="text-sm text-gray-500">No windows available</div>
                            `}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderActionButtons(session) {
        return `
            <button 
                data-action="enter" 
                data-session-name="${session.session_name}"
                class="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 ${!session.exists ? 'opacity-50 cursor-not-allowed' : ''}"
                ${!session.exists ? 'disabled' : ''}
            >
                Enter
            </button>
            <button 
                data-action="stop" 
                data-session-name="${session.session_name}"
                class="px-3 py-1 text-xs bg-red-600 text-white rounded-md hover:bg-red-700 ${!session.exists ? 'opacity-50 cursor-not-allowed' : ''}"
                ${!session.exists ? 'disabled' : ''}
            >
                Stop
            </button>
        `;
    }

    renderError(message) {
        const container = this.querySelector('.sessions-container');
        container.innerHTML = `
            <div class="error-state text-center py-8">
                <svg class="w-12 h-12 mx-auto mb-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-medium text-gray-900 mb-2">Error</h3>
                <p class="text-gray-500">${message}</p>
                <button 
                    data-action="refresh"
                    class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                    Retry
                </button>
            </div>
        `;
    }
}

// Register the custom element
customElements.define('session-browser', SessionBrowser);