import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true', // Bypasses Ngrok warning page
    },
});

console.log('API Base URL:', api.defaults.baseURL);

// Define types for API responses
export interface StatusResponse {
    running: boolean;
}

export interface ModelInfoResponse {
    model_uri: string;
    run_id: string;
    alias: string;
    status: string;
    params?: Record<string, string>;
    metrics?: Record<string, number>;
    artifacts?: string[];
}

export interface HealthResponse {
    status: string;
}

// API methods
export const apiService = {
    // Start the detection stream
    startDetection: async () => {
        const response = await api.post<{ status: string }>('/start-detection');
        return response.data;
    },

    // Stop the detection stream
    stopDetection: async () => {
        const response = await api.post<{ status: string }>('/stop-detection');
        return response.data;
    },

    // Get current status (running or not)
    getStatus: async () => {
        const response = await api.get<StatusResponse>('/status');
        return response.data;
    },

    // Get model information
    getModelInfo: async () => {
        const response = await api.get<ModelInfoResponse>('/model-info');
        return response.data;
    },

    // Health check
    checkHealth: async () => {
        const response = await api.get<HealthResponse>('/health');
        return response.data;
    },

    // Get recent logs
    getLogs: async () => {
        const response = await api.get<{ logs: any[] }>('/logs');
        return response.data;
    },

    // Fetch artifact image as Blob (to bypass Ngrok warning)
    getArtifact: async (filename: string) => {
        const response = await api.get(`/model-artifact/${filename}`, {
            responseType: 'blob'
        });
        return URL.createObjectURL(response.data);
    },
};

export default apiService;
