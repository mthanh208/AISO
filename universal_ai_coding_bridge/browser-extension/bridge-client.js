/**
 * Bridge Client for UACB Extension
 * 
 * Handles communication with the local bridge server
 */

const BRIDGE_URL = 'http://127.0.0.1:8765';

const BridgeClient = {
    /**
     * Check if bridge is healthy
     * @returns {Promise<boolean>}
     */
    async healthCheck() {
        try {
            const response = await fetch(`${BRIDGE_URL}/health`);
            const data = await response.json();
            return data.status === 'healthy';
        } catch (e) {
            console.error('Bridge health check failed:', e);
            return false;
        }
    },

    /**
     * Execute a tool call
     * @param {Object} toolCall - Tool call object
     * @returns {Promise<Object>} Result object
     */
    async executeTool(toolCall) {
        try {
            const endpoint = this._getToolEndpoint(toolCall.tool);
            
            const response = await fetch(`${BRIDGE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(toolCall.arguments)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Tool execution failed');
            }

            return await response.json();
        } catch (e) {
            console.error('Tool execution failed:', e);
            return {
                ok: false,
                error: e.message
            };
        }
    },

    /**
     * Get the API endpoint for a tool
     * @param {string} toolName - Tool name
     * @returns {string} Endpoint path
     */
    _getToolEndpoint(toolName) {
        const toolMap = {
            'inspect_project': '/inspect_project',
            'read_file': '/read_file',
            'write_file': '/write_file',
            'apply_patch': '/apply_patch',
            'search': '/search',
            'run': '/run',
            'run_main': '/run_main',
            'run_pytest': '/run_pytest',
            'git_status': '/git_status',
            'git_diff': '/git_diff',
            'session': '/session',
            'checkpoint': '/checkpoint',
            'rollback': '/rollback',
            'loop': '/loop'
        };

        return toolMap[toolName] || `/tools/${toolName}`;
    },

    /**
     * Create a new session
     * @param {string} project - Project name
     * @returns {Promise<Object>} Session info
     */
    async createSession(project) {
        try {
            const response = await fetch(`${BRIDGE_URL}/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ project })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create session');
            }

            return await response.json();
        } catch (e) {
            console.error('Failed to create session:', e);
            throw e;
        }
    },

    /**
     * Get session info
     * @param {string} sessionId - Session ID
     * @returns {Promise<Object>} Session info
     */
    async getSession(sessionId) {
        try {
            const response = await fetch(`${BRIDGE_URL}/session/${sessionId}`);
            
            if (!response.ok) {
                throw new Error('Session not found');
            }

            return await response.json();
        } catch (e) {
            console.error('Failed to get session:', e);
            throw e;
        }
    },

    /**
     * Process AI response through agent loop
     * @param {string} sessionId - Session ID
     * @param {string} aiResponse - AI response text
     * @returns {Promise<Object>} Loop result
     */
    async processLoop(sessionId, aiResponse) {
        try {
            const response = await fetch(`${BRIDGE_URL}/loop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    ai_response: aiResponse
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Loop processing failed');
            }

            return await response.json();
        } catch (e) {
            console.error('Loop processing failed:', e);
            return {
                status: 'ERROR',
                error: e.message
            };
        }
    },

    /**
     * Create a checkpoint
     * @param {string} sessionId - Session ID
     * @param {string} name - Checkpoint name
     * @returns {Promise<Object>} Checkpoint info
     */
    async createCheckpoint(sessionId, name) {
        try {
            const response = await fetch(`${BRIDGE_URL}/checkpoint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId, name })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Checkpoint failed');
            }

            return await response.json();
        } catch (e) {
            console.error('Checkpoint failed:', e);
            throw e;
        }
    },

    /**
     * Rollback to a checkpoint
     * @param {string} sessionId - Session ID
     * @param {string} checkpointName - Checkpoint name
     * @returns {Promise<Object>} Rollback result
     */
    async rollback(sessionId, checkpointName) {
        try {
            const response = await fetch(`${BRIDGE_URL}/rollback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: sessionId, checkpoint_name: checkpointName })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Rollback failed');
            }

            return await response.json();
        } catch (e) {
            console.error('Rollback failed:', e);
            throw e;
        }
    },

    /**
     * List available projects
     * @returns {Promise<Array>} List of project names
     */
    async listProjects() {
        try {
            const response = await fetch(`${BRIDGE_URL}/projects`);
            const data = await response.json();
            return data.projects || [];
        } catch (e) {
            console.error('Failed to list projects:', e);
            return [];
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BridgeClient;
}
