/**
 * Background Service Worker for UACB Extension
 */

chrome.runtime.onInstalled.addListener(() => {
    console.log('UACB: Extension installed');
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.sendMessage(tab.id, { action: 'toggle' });
});

// Keep service worker alive
setInterval(() => {
    // This keeps the service worker active
}, 20000);
