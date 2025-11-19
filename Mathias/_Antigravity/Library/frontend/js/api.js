const API_BASE = 'http://localhost:8000/api';

export async function getLibraries() {
    const response = await fetch(`${API_BASE}/libraries`);
    return await response.json();
}

export async function scanDirectory(path) {
    const response = await fetch(`${API_BASE}/scan?path=${encodeURIComponent(path)}`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to scan directory');
    return await response.json();
}

export function getMediaUrl(path) {
    return `http://localhost:8000/media/stream?path=${encodeURIComponent(path)}`;
}
