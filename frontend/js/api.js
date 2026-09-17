/**
 * VidLink API Client
 * Handles communication with Flask backend REST endpoints.
 */
class VidLinkAPI {
    static async analyzeURL(url) {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url.trim() })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Media extraction failed.');
        }
        return data;
    }

    static async checkHealth() {
        try {
            const res = await fetch('/api/health');
            return await res.json();
        } catch (e) {
            return { status: 'offline' };
        }
    }
}

window.VidLinkAPI = VidLinkAPI;
