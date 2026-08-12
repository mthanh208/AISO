/**
 * UACB Protocol Utilities
 * 
 * Handles parsing and creating uacb-tool and uacb-result blocks
 */

const UACBProtocol = {
    TOOL_CALL_MARKER: 'uacb-tool',
    RESULT_MARKER: 'uacb-result',

    /**
     * Parse tool calls from text
     * @param {string} text - Text containing tool call blocks
     * @returns {Array} Array of tool call objects
     */
    parseToolCalls(text) {
        const calls = [];
        const startMarker = `\`\`\`${this.TOOL_CALL_MARKER}`;
        const endMarker = '```';

        let startIndex = 0;
        while (true) {
            const startPos = text.indexOf(startMarker, startIndex);
            if (startPos === -1) break;

            const contentStart = startPos + startMarker.length;
            const endPos = text.indexOf(endMarker, contentStart);

            if (endPos === -1) break;

            const jsonStr = text.substring(contentStart, endPos).trim();

            try {
                const call = JSON.parse(jsonStr);
                calls.push(call);
            } catch (e) {
                console.error('Failed to parse tool call:', e);
            }

            startIndex = endPos + endMarker.length;
        }

        return calls;
    },

    /**
     * Create a tool call block
     * @param {string} id - Call ID
     * @param {string} tool - Tool name
     * @param {Object} arguments - Tool arguments
     * @returns {string} Markdown block
     */
    createToolCall(id, tool, args) {
        const call = { id, tool, arguments: args };
        return `\`\`\`${this.TOOL_CALL_MARKER}\n${JSON.stringify(call, null, 2)}\n\`\`\``;
    },

    /**
     * Create a result block
     * @param {Object} result - Result object
     * @returns {string} Markdown block
     */
    createResultBlock(result) {
        return `\`\`\`${this.RESULT_MARKER}\n${JSON.stringify(result, null, 2)}\n\`\`\``;
    },

    /**
     * Generate a unique call ID
     * @returns {string} Call ID
     */
    generateCallId() {
        return `call-${Math.random().toString(36).substring(2, 10)}`;
    },

    /**
     * Parse result blocks from text
     * @param {string} text - Text containing result blocks
     * @returns {Array} Array of result objects
     */
    parseResults(text) {
        const results = [];
        const startMarker = `\`\`\`${this.RESULT_MARKER}`;
        const endMarker = '```';

        let startIndex = 0;
        while (true) {
            const startPos = text.indexOf(startMarker, startIndex);
            if (startPos === -1) break;

            const contentStart = startPos + startMarker.length;
            const endPos = text.indexOf(endMarker, contentStart);

            if (endPos === -1) break;

            const jsonStr = text.substring(contentStart, endPos).trim();

            try {
                const result = JSON.parse(jsonStr);
                results.push(result);
            } catch (e) {
                console.error('Failed to parse result:', e);
            }

            startIndex = endPos + endMarker.length;
        }

        return results;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UACBProtocol;
}
