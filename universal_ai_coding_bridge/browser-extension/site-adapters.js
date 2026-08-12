/**
 * Site Adapters for UACB Extension v2.0
 * 
 * Abstracts DOM interactions for different AI websites
 * Auto-detects and adapts to new AI web interfaces dynamically
 */

/**
 * Base adapter interface with auto-discovery capabilities
 */
class SiteAdapter {
    constructor() {
        this.name = 'Generic';
        this.domCache = new Map();
        this.lastUpdated = Date.now();
    }

    /**
     * Check if this adapter matches the current site
     * @returns {boolean}
     */
    matches() {
        return false;
    }

    /**
     * Dynamic DOM scanner - finds elements by multiple strategies
     * @param {string[]} selectors - Array of CSS selectors to try
     * @param {string} attributeKey - Optional attribute key to match
     * @param {string} attributeValue - Optional attribute value to match
     * @returns {Element|null}
     */
    scanDOM(selectors, attributeKey = null, attributeValue = null) {
        const cacheKey = selectors.join('|');
        const cached = this.domCache.get(cacheKey);
        
        // Return cached element if still valid (less than 5 seconds old)
        if (cached && (Date.now() - this.lastUpdated) < 5000) {
            return cached;
        }

        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            
            for (const el of elements) {
                // If no attribute filter, return first match
                if (!attributeKey) {
                    this.domCache.set(cacheKey, el);
                    this.lastUpdated = Date.now();
                    return el;
                }
                
                // Check if element has matching attribute
                const attrValue = el.getAttribute(attributeKey);
                if (attrValue && (
                    !attributeValue || 
                    attrValue.toLowerCase().includes(attributeValue.toLowerCase())
                )) {
                    this.domCache.set(cacheKey, el);
                    this.lastUpdated = Date.now();
                    return el;
                }
            }
        }
        
        return null;
    }

    /**
     * Find the composer/input element with auto-discovery
     * @returns {Element|null}
     */
    findComposer() {
        // Strategy 1: Look for textarea with common placeholders
        const composer = this.scanDOM([
            'textarea[placeholder*="message" i]',
            'textarea[placeholder*="type" i]',
            'textarea[placeholder*="ask" i]',
            'textarea[placeholder*="chat" i]',
            'div[contenteditable="true"]',
            '[role="textbox"]',
            'input[type="text"][aria-label*="message" i]'
        ]);
        
        if (composer) return composer;

        // Strategy 2: Look for elements near send buttons
        const sendButton = this.findSendButton();
        if (sendButton) {
            const form = sendButton.closest('form');
            if (form) {
                return form.querySelector('textarea, input[type="text"], [contenteditable]');
            }
            
            // Look in parent containers
            let parent = sendButton.parentElement;
            while (parent && parent !== document.body) {
                const sibling = parent.querySelector('textarea, [contenteditable]');
                if (sibling) return sibling;
                parent = parent.parentElement;
            }
        }

        // Strategy 3: Global search for editable elements
        const editables = document.querySelectorAll('textarea, [contenteditable="true"]');
        if (editables.length > 0) {
            return editables[editables.length - 1]; // Usually the last one is the input
        }

        return null;
    }

    /**
     * Find the send button with auto-discovery
     * @returns {Element|null}
     */
    findSendButton() {
        return this.scanDOM([
            'button[aria-label*="send" i]',
            'button[type="submit"]',
            'button[aria-label*="Send" i]',
            '.send-button',
            'send-button',
            '[data-testid*="send"]',
            'svg path[d*="M2.01"]', // Common send icon path
            'button svg'
        ]);
    }

    /**
     * Find assistant messages with auto-discovery
     * @returns {Element[]}
     */
    findAssistantMessages() {
        const selectors = [
            '[role="assistant"]',
            '[data-message-author-role="assistant"]',
            '[data-is-user="false"]',
            '.assistant-message',
            '.bot-response',
            '.response',
            '.model-response',
            'article:last-of-type',
            '[class*="assistant"]',
            '[class*="response"]'
        ];

        const messages = [];
        for (const selector of selectors) {
            const els = document.querySelectorAll(selector);
            if (els.length > 0) {
                messages.push(...Array.from(els));
            }
        }
        
        // Remove duplicates and sort by position
        const unique = [...new Set(messages)];
        return unique.sort((a, b) => {
            const position = a.compareDocumentPosition(b);
            return position & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
        });
    }

    /**
     * Get the latest assistant message text
     * @returns {string}
     */
    latestAssistantText() {
        const messages = this.findAssistantMessages();
        if (messages.length === 0) return '';
        return messages[messages.length - 1].textContent || '';
    }

    /**
     * Insert text into composer with enhanced simulation
     * @param {string} text - Text to insert
     */
    insertPrompt(text) {
        const composer = this.findComposer();
        if (!composer) {
            console.error('UACB: Composer not found');
            return;
        }

        // Clear existing content
        composer.value = '';
        composer.textContent = '';

        // Focus and simulate typing
        composer.focus();
        
        // Method 1: Using InputEvent (modern browsers)
        if (typeof InputEvent !== 'undefined') {
            composer.dispatchEvent(new InputEvent('beforeinput', { 
                bubbles: true, 
                cancelable: true,
                data: text 
            }));
            composer.value = text;
            composer.textContent = text;
            composer.dispatchEvent(new InputEvent('input', { 
                bubbles: true,
                data: text 
            }));
        } 
        // Method 2: Using execCommand (fallback)
        else {
            document.execCommand('insertText', false, text);
        }

        // Trigger additional events for React/Vue/Angular apps
        composer.dispatchEvent(new Event('change', { bubbles: true }));
        composer.dispatchEvent(new KeyboardEvent('keyup', { 
            key: 'v', 
            bubbles: true 
        }));
    }

    /**
     * Send the message
     */
    send() {
        const sendButton = this.findSendButton();
        if (sendButton) {
            sendButton.click();
        } else {
            // Fallback: Try keyboard shortcut
            const composer = this.findComposer();
            if (composer) {
                composer.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    ctrlKey: false,
                    shiftKey: false
                }));
            }
        }
    }

    /**
     * Wait for new assistant response with mutation observer
     * @param {Function} callback - Callback when response arrives
     */
    waitForResponse(callback) {
        const initialCount = this.findAssistantMessages().length;
        let triggered = false;

        const observer = new MutationObserver((mutations) => {
            if (triggered) return;
            
            const messages = this.findAssistantMessages();
            if (messages.length > initialCount) {
                triggered = true;
                const lastMessage = messages[messages.length - 1];
                callback(lastMessage);
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Timeout after 60 seconds
        setTimeout(() => {
            if (!triggered) {
                observer.disconnect();
                callback(null);
            }
        }, 60000);

        return observer;
    }
}

/**
 * ChatGPT Adapter
 */
class ChatGPTAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'ChatGPT';
    }

    matches() {
        return window.location.hostname.includes('chat.openai.com') ||
               window.location.hostname.includes('chatgpt.com');
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            'textarea[data-id*="root"]',
            '#prompt-textarea'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button[data-testid*="send"]',
            'form button[type="submit"]',
            'button[aria-label*="Send"'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'))
            .concat(Array.from(document.querySelectorAll('article')));
    }
}

/**
 * Claude Adapter
 */
class ClaudeAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'Claude';
    }

    matches() {
        return window.location.hostname.includes('claude.ai');
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            'div[contenteditable="true"]',
            '#prompt-input'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button[aria-label*="send" i]',
            'button svg path[d*="M2.01"]'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('[data-is-user="false"]'));
    }
}

/**
 * Gemini Adapter
 */
class GeminiAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'Gemini';
    }

    matches() {
        return window.location.hostname.includes('gemini.google.com') ||
               (window.location.hostname.includes('google.com') && 
                document.title.includes('Gemini'));
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            'rich-textarea',
            '.ql-editor',
            '#mat-input-0'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button[aria-label*="Send" i]',
            'send-button',
            '.send-button'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('.response-container'))
            .concat(Array.from(document.querySelectorAll('[data-locale] .model-response')));
    }
}

/**
 * Qwen Adapter
 */
class QwenAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'Qwen';
    }

    matches() {
        return window.location.hostname.includes('qwen.ai') ||
               window.location.hostname.includes('tongyi.aliyun.com');
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            '#user-input',
            '.input-box textarea'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button.send-button',
            '[aria-label="Send" i]'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('.assistant-message'))
            .concat(Array.from(document.querySelectorAll('.bot-response')));
    }
}

/**
 * DeepSeek Adapter
 */
class DeepSeekAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'DeepSeek';
    }

    matches() {
        return window.location.hostname.includes('deepseek.com') ||
               window.location.hostname.includes('chat.deepseek.com');
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            '#chat-input',
            '.input-area textarea'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button[aria-label*="send" i]',
            '.send-btn'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('.assistant-item'))
            .concat(Array.from(document.querySelectorAll('.response-content')));
    }
}

/**
 * Grok Adapter
 */
class GrokAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'Grok';
    }

    matches() {
        return window.location.hostname.includes('grok.x.ai') ||
               window.location.hostname.includes('x.com') && 
               document.title.includes('Grok');
    }

    findComposer() {
        return this.scanDOM([
            'textarea[placeholder*="message" i]',
            '[data-testid="tweetbox"] textarea'
        ]);
    }

    findSendButton() {
        return this.scanDOM([
            'button[aria-label*="post" i]',
            'button[aria-label*="send" i]'
        ]);
    }

    findAssistantMessages() {
        return Array.from(document.querySelectorAll('[data-testid="tweet"]'))
            .filter(el => el.textContent.includes('Grok'));
    }
}

/**
 * Generic fallback adapter with enhanced auto-discovery
 */
class GenericAdapter extends SiteAdapter {
    constructor() {
        super();
        this.name = 'Generic';
    }

    matches() {
        return true;
    }
}

/**
 * Adapter registry with auto-registration support
 */
const adapters = [
    new ChatGPTAdapter(),
    new ClaudeAdapter(),
    new GeminiAdapter(),
    new QwenAdapter(),
    new DeepSeekAdapter(),
    new GrokAdapter(),
    new GenericAdapter()
];

/**
 * Get the appropriate adapter for current site
 * @returns {SiteAdapter}
 */
function getAdapter() {
    for (const adapter of adapters) {
        if (adapter.matches()) {
            console.log(`UACB: Using ${adapter.name} adapter`);
            return adapter;
        }
    }
    return new GenericAdapter();
}

/**
 * Register a custom adapter at runtime
 * @param {SiteAdapter} adapter 
 */
function registerAdapter(adapter) {
    // Insert before GenericAdapter
    adapters.splice(adapters.length - 1, 0, adapter);
    console.log(`UACB: Registered custom adapter: ${adapter.name}`);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SiteAdapter, getAdapter, adapters, registerAdapter };
} else {
    window.UACBAdapters = { SiteAdapter, getAdapter, adapters, registerAdapter };
}
