/**
 * Popup Script for UACB Extension
 */

const BRIDGE_URL = 'http://127.0.0.1:8765';

document.addEventListener('DOMContentLoaded', async () => {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const projectSelect = document.getElementById('projectSelect');
    const refreshBtn = document.getElementById('refreshBtn');
    const resetBtn = document.getElementById('resetBtn');

    // Check bridge health
    async function checkHealth() {
        try {
            const response = await fetch(`${BRIDGE_URL}/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Bridge Connected';
                loadProjects();
            } else {
                throw new Error('Unhealthy');
            }
        } catch (e) {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Bridge Disconnected';
            projectSelect.innerHTML = '<option value="">Bridge offline</option>';
        }
    }

    // Load projects
    async function loadProjects() {
        try {
            const response = await fetch(`${BRIDGE_URL}/projects`);
            const data = await response.json();
            
            projectSelect.innerHTML = '<option value="">Select Project...</option>';
            
            if (data.projects && data.projects.length > 0) {
                for (const project of data.projects) {
                    const option = document.createElement('option');
                    option.value = project;
                    option.textContent = project;
                    projectSelect.appendChild(option);
                }
            }
        } catch (e) {
            console.error('Failed to load projects:', e);
        }
    }

    // Refresh button
    refreshBtn.addEventListener('click', () => {
        checkHealth();
    });

    // Reset button
    resetBtn.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'reset' });
            alert('Session reset!');
        }
    });

    // Initial check
    checkHealth();
});
