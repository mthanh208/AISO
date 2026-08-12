/**
 * Content Script for UACB Extension
 * 
 * Main entry point for content script functionality
 */

(function() {
    'use strict';

    console.log('UACB: Content script loaded');

    // State
    let currentSession = null;
    let processedCallIds = new Set();
    let adapter = null;
    let isProcessing = false;

    /**
     * Initialize the extension
     */
    async function init() {
        // Get the appropriate adapter
        adapter = window.UACBAdapters ? window.UACBAdapters.getAdapter() : null;
        
        if (!adapter) {
            console.error('UACB: No adapter found');
            return;
        }

        console.log(`UACB: Initialized with ${adapter.name} adapter`);

        // Check bridge health
        const healthy = await BridgeClient.healthCheck();
        if (!healthy) {
            console.warn('UACB: Bridge server not responding. Is it running on http://127.0.0.1:8765?');
            showBridgeWarning();
            return;
        }

        console.log('UACB: Bridge server is healthy');

        // Start monitoring for AI responses
        monitorAssistantMessages();
    }

    /**
     * Monitor assistant messages for tool calls
     */
    function monitorAssistantMessages() {
        let lastMessageText = '';
        let lastMessageTime = 0;

        setInterval(async () => {
            if (isProcessing) return;

            const messages = adapter.findAssistantMessages();
            if (messages.length === 0) return;

            const lastMessage = messages[messages.length - 1];
            const text = lastMessage.textContent || '';
            const messageTime = lastMessage.getAttribute('data-timestamp') || Date.now();

            // Check if this is a new message
            if (text !== lastMessageText && Date.now() - lastMessageTime > 2000) {
                lastMessageText = text;
                lastMessageTime = messageTime;

                // Parse tool calls from the message
                const toolCalls = UACBProtocol.parseToolCalls(text);
                
                if (toolCalls.length > 0) {
                    console.log('UACB: Found tool calls:', toolCalls.length);
                    await processToolCalls(toolCalls);
                }
            }
        }, 3000);
    }

    /**
     * Process tool calls from AI response
     * @param {Array} toolCalls - Array of tool call objects
     */
    async function processToolCalls(toolCalls) {
        isProcessing = true;

        try {
            // Create session if needed
            if (!currentSession) {
                // Try to get project from context or prompt user
                const projects = await BridgeClient.listProjects();
                
                if (projects.length === 0) {
                    console.warn('UACB: No projects found in sandbox');
                    insertResult({
                        ok: false,
                        error: 'No projects found in sandbox. Please add a project to sandbox/'
                    });
                    return;
                }

                // Use first project by default
                currentSession = await BridgeClient.createSession(projects[0]);
                console.log('UACB: Created session:', currentSession.session_id);
            }

            // Process each tool call
            for (const call of toolCalls) {
                // Skip already processed calls
                if (processedCallIds.has(call.id)) {
                    console.log('UACB: Skipping already processed call:', call.id);
                    continue;
                }

                console.log('UACB: Executing tool:', call.tool);

                // Execute the tool
                const result = await BridgeClient.executeTool(call);
                
                // Mark as processed
                processedCallIds.add(call.id);

                // Insert result
                insertResult({
                    id: call.id,
                    tool: call.tool,
                    ok: result.ok,
                    result: result.result,
                    error: result.error
                });

                // Small delay between tool calls
                await sleep(500);
            }

            // Auto-send after inserting results
            setTimeout(() => {
                autoSendResults();
            }, 1000);

        } catch (e) {
            console.error('UACB: Error processing tool calls:', e);
            insertResult({
                ok: false,
                error: `Processing error: ${e.message}`
            });
        } finally {
            isProcessing = false;
        }
    }

    /**
     * Insert a result block into the composer
     * @param {Object} result - Result object
     */
    function insertResult(result) {
        const resultBlock = UACBProtocol.createResultBlock(result);
        
        // Create a hidden element to store results (for debugging)
        const resultsContainer = document.getElementById('uacb-results') || 
                                 createResultsContainer();
        
        const resultEntry = document.createElement('div');
        resultEntry.className = 'uacb-result-entry';
        resultEntry.textContent = `${result.tool}: ${result.ok ? 'OK' : 'FAILED'}`;
        resultsContainer.appendChild(resultEntry);

        console.log('UACB: Result inserted:', result);
    }

    /**
     * Create results container
     */
    function createResultsContainer() {
        const container = document.createElement('div');
        container.id = 'uacb-results';
        container.style.cssText = 'position: fixed; bottom: 10px; right: 10px; background: #fff; border: 1px solid #ccc; padding: 10px; max-height: 200px; overflow-y: auto; z-index: 9999; font-size: 12px;';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Show bridge warning
     */
    function showBridgeWarning() {
        const warning = document.createElement('div');
        warning.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #ffeb3b; border: 2px solid #f44336; padding: 15px; z-index: 9999; max-width: 400px; border-radius: 5px;';
        warning.innerHTML = `
            <strong>UACB Warning</strong><br>
            Bridge server not responding.<br>
            Please run: <code>./run.sh</code><br>
            <button onclick="this.parentElement.remove()" style="margin-top: 10px; padding: 5px 10px;">Dismiss</button>
        `;
        document.body.appendChild(warning);

        // Auto-remove after 10 seconds
        setTimeout(() => warning.remove(), 10000);
    }

    /**
     * Auto-send results to AI
     */
    function autoSendResults() {
        // This would trigger the send button automatically
        // For safety, we'll just log instead of auto-sending
        console.log('UACB: Results ready. Please review and send manually.');
    }

    /**
     * Sleep utility
     * @param {number} ms - Milliseconds to sleep
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Handle messages from popup/background
     */
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'getStatus') {
            sendResponse({
                connected: currentSession !== null,
                sessionId: currentSession?.session_id,
                adapter: adapter?.name
            });
        }
        
        if (message.action === 'reset') {
            currentSession = null;
            processedCallIds.clear();
            sendResponse({ status: 'reset' });
        }

        return true;
    });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
