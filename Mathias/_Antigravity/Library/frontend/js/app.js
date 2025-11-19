import * as api from './api.js';

// State
let currentPath = null;

// DOM Elements
const mainContent = document.getElementById('main-content');
const breadcrumbs = document.getElementById('breadcrumbs');
const modalContainer = document.getElementById('modal-container');

// Init
async function init() {
    // Check if we have a stored path or start at libraries
    loadLibraries();
}

async function loadLibraries() {
    mainContent.innerHTML = '<div style="text-align:center; padding: 20px;">Loading libraries...</div>';
    breadcrumbs.innerHTML = '';

    try {
        const data = await api.getLibraries();
        renderLibraryChooser(data.drives);
    } catch (e) {
        mainContent.innerHTML = `<div style="color:red; text-align:center;">Error loading libraries: ${e.message}</div>`;
    }
}

function renderLibraryChooser(drives) {
    currentPath = null;
    breadcrumbs.innerHTML = '<div class="breadcrumb-item">Libraries</div>';

    const container = document.createElement('div');
    container.className = 'library-list';

    const title = document.createElement('h2');
    title.textContent = 'Select a Library';
    title.style.marginBottom = '20px';
    title.style.textAlign = 'center';
    container.appendChild(title);

    drives.forEach(drive => {
        const item = document.createElement('div');
        item.className = 'library-item';
        item.innerHTML = `
            <h3>${drive}</h3>
            <p style="font-size: 0.8rem; color: var(--text-secondary);">Drive Root</p>
        `;
        item.onclick = () => navigateTo(drive);
        container.appendChild(item);
    });

    mainContent.innerHTML = '';
    mainContent.appendChild(container);
}

async function navigateTo(path) {
    currentPath = path;
    updateBreadcrumbs(path);

    mainContent.innerHTML = '<div style="text-align:center; padding: 20px;">Loading...</div>';

    try {
        const data = await api.scanDirectory(path);
        renderFileExplorer(data.items);
    } catch (e) {
        mainContent.innerHTML = `<div style="color:red; text-align:center;">Error loading directory: ${e.message}</div>`;
    }
}

function updateBreadcrumbs(path) {
    // Simple breadcrumb logic for Windows paths
    const parts = path.split('\\').filter(p => p);
    breadcrumbs.innerHTML = '';

    const home = document.createElement('div');
    home.className = 'breadcrumb-item';
    home.textContent = 'Libraries';
    home.onclick = () => loadLibraries();
    breadcrumbs.appendChild(home);

    breadcrumbs.appendChild(createSeparator());

    let builtPath = '';
    parts.forEach((part, index) => {
        builtPath += part + (index === 0 ? '\\' : '\\'); // Keep trailing slash for drive, or add backslash
        // Fix path building logic slightly for visual purposes
        // Actually, let's just reconstruct it properly

        // For click handler, we need the full path up to this point
        const clickPath = parts.slice(0, index + 1).join('\\') + (index === 0 ? '\\' : '');

        const item = document.createElement('div');
        item.className = 'breadcrumb-item';
        item.textContent = part;
        item.onclick = () => navigateTo(clickPath);
        breadcrumbs.appendChild(item);

        if (index < parts.length - 1) {
            breadcrumbs.appendChild(createSeparator());
        }
    });
}

function createSeparator() {
    const span = document.createElement('span');
    span.className = 'breadcrumb-separator';
    span.textContent = '/';
    return span;
}

function renderFileExplorer(items) {
    const grid = document.createElement('div');
    grid.className = 'grid-container';

    if (items.length === 0) {
        mainContent.innerHTML = '<div style="text-align:center; color: var(--text-secondary); margin-top: 50px;">Folder is empty</div>';
        return;
    }

    items.forEach(item => {
        const el = document.createElement('div');
        el.className = 'grid-item';

        let iconHtml = '';
        if (item.type === 'directory') {
            iconHtml = '<div style="font-size: 3rem;">📁</div>';
        } else if (item.mime_type && item.mime_type.startsWith('image/')) {
            const url = api.getMediaUrl(item.path);
            iconHtml = `<img src="${url}" loading="lazy" alt="${item.name}">`;
        } else if (item.mime_type && item.mime_type.startsWith('video/')) {
            iconHtml = '<div style="font-size: 3rem;">▶️</div>';
        } else {
            iconHtml = '<div style="font-size: 3rem;">📄</div>';
        }

        el.innerHTML = `
            <div class="icon-placeholder">${iconHtml}</div>
            <div class="item-name">${item.name}</div>
        `;

        el.onclick = () => {
            if (item.type === 'directory') {
                navigateTo(item.path);
            } else {
                openMedia(item);
            }
        };

        grid.appendChild(el);
    });

    mainContent.innerHTML = '';
    mainContent.appendChild(grid);
}

function openMedia(item) {
    if (!item.mime_type) return;

    const url = api.getMediaUrl(item.path);
    let content = '';

    if (item.mime_type.startsWith('image/')) {
        content = `<img src="${url}" alt="${item.name}">`;
    } else if (item.mime_type.startsWith('video/')) {
        content = `
            <video controls autoplay>
                <source src="${url}" type="${item.mime_type}">
                Your browser does not support the video tag.
            </video>
        `;
    }

    modalContainer.innerHTML = `
        <div class="modal-content">
            <button class="close-btn" onclick="document.getElementById('modal-container').classList.add('hidden')">&times;</button>
            ${content}
        </div>
    `;
    modalContainer.classList.remove('hidden');

    // Close on background click
    modalContainer.onclick = (e) => {
        if (e.target === modalContainer) {
            modalContainer.classList.add('hidden');
        }
    };
}

// Start
init();
