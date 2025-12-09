// State
const state = {
    services: [],
    isAdmin: false,
    isServerMode: false,
    showDetails: false
};

// DOM Elements
const servicesGrid = document.getElementById('services-grid');
const modeSwitch = document.getElementById('mode-switch');
const modeLabel = document.getElementById('mode-label');
const descSwitch = document.getElementById('desc-switch');
const glassSwitch = document.getElementById('glass-switch');
const adminBtn = document.getElementById('admin-btn');
const adminLabel = document.getElementById('admin-label');
const loginModal = document.getElementById('login-modal');
const closeModalBtn = document.getElementById('close-modal');
const loginBtn = document.getElementById('login-btn');
const passwordInput = document.getElementById('admin-password');

// Init
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchServices();
    setupEventListeners();
});

// Fetch Services
async function fetchServices() {
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        state.services = data;
        renderServices();
    } catch (error) {
        console.error('Error fetching services:', error);
        servicesGrid.innerHTML = '<p style="text-align:center; grid-column: 1/-1; color: var(--danger-color);">Error loading services. Is the backend running?</p>';
    }
}

// Render Services
function renderServices() {
    servicesGrid.innerHTML = '';

    state.services.forEach(service => {
        const card = document.createElement('a');
        const isRunning = service.status === 'running';
        card.className = `service-card ${isRunning ? 'running' : 'stopped'}`;

        // Determine URL based on mode
        const host = state.isServerMode ? service.server_ip : 'localhost';
        card.href = `http://${host}:${service.port}`;
        card.target = '_blank';
        card.rel = 'noopener noreferrer';

        // Status Class
        const statusClass = `status-${service.status === 'running' ? 'running' : 'stopped'}`;

        // Icon/Image Logic
        let iconHtml;
        if (service.image && service.image.endsWith('.webp')) {
            iconHtml = `<img src="images/${service.image}" alt="${service.name}" style="width: 32px; height: 32px; object-fit: contain;">`;
        } else {
            iconHtml = `<i data-lucide="${service.image || service.icon || 'box'}"></i>`;
        }

        card.innerHTML = `
            <div class="card-header">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    ${iconHtml}
                    <span class="service-name">${service.name}</span>
                </div>
                <div class="status-indicator ${statusClass}" title="${service.status}"></div>
            </div>
            <div class="service-desc ${state.showDetails ? 'visible' : ''}">
                ${service.description}
            </div>
            <div class="card-actions ${state.isAdmin ? 'visible' : ''}">
                <button class="action-btn btn-start" onclick="handleAction(event, '${service.id}', 'start')">
                    <i data-lucide="play" style="width: 16px; height: 16px;"></i> Start
                </button>
                <button class="action-btn btn-stop" onclick="handleAction(event, '${service.id}', 'stop')">
                    <i data-lucide="square" style="width: 16px; height: 16px;"></i> Stop
                </button>
            </div>
        `;

        servicesGrid.appendChild(card);
    });

    lucide.createIcons();
}

// Handle Actions (Start/Stop)
async function handleAction(event, serviceId, action) {
    event.preventDefault(); // Prevent navigation
    event.stopPropagation(); // Prevent bubbling

    if (!state.isAdmin) return;

    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 16px; height: 16px;"></i>';
    lucide.createIcons();

    try {
        const response = await fetch(`/api/services/${serviceId}/${action}`, { method: 'POST' });
        const result = await response.json();

        if (response.ok) {
            // Refresh services to update status
            await fetchServices();
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error performing action:', error);
        alert('Network error');
    } finally {
        btn.innerHTML = originalContent;
        lucide.createIcons();
    }
}

// Event Listeners
function setupEventListeners() {
    // Local/Server Switch
    modeSwitch.addEventListener('change', (e) => {
        state.isServerMode = e.target.checked;
        modeLabel.textContent = state.isServerMode ? 'Server' : 'Local';
        renderServices();
    });

    // Description Switch
    descSwitch.addEventListener('change', (e) => {
        state.showDetails = e.target.checked;
        renderServices();
    });

    // Glass Mode Switch
    glassSwitch.addEventListener('change', (e) => {
        document.body.classList.toggle('transparent-mode', e.target.checked);
    });

    // Admin Button
    adminBtn.addEventListener('click', () => {
        if (state.isAdmin) {
            // Logout
            state.isAdmin = false;
            updateAdminButton();
            renderServices();
        } else {
            // Open Login Modal
            loginModal.classList.remove('hidden');
            passwordInput.value = '';
            passwordInput.focus();
        }
    });

    // Close Modal
    closeModalBtn.addEventListener('click', () => {
        loginModal.classList.add('hidden');
    });

    // Login Logic
    loginBtn.addEventListener('click', attemptLogin);
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') attemptLogin();
    });
}

function updateAdminButton() {
    adminBtn.innerHTML = `
        <i data-lucide="${state.isAdmin ? 'unlock' : 'lock'}"></i>
        <span id="admin-label">${state.isAdmin ? 'Admin' : 'Visitor'}</span>
    `;
    lucide.createIcons();
}

function attemptLogin() {
    const password = passwordInput.value;
    // Hardcoded password for demo purposes
    if (password === 'admin') {
        state.isAdmin = true;
        updateAdminButton();
        loginModal.classList.add('hidden');
        renderServices();
    } else {
        alert('Incorrect password');
        passwordInput.value = '';
    }
}

// Expose handleAction to global scope for onclick
window.handleAction = handleAction;
