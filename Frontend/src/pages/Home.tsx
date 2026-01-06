import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import { Play, Square, Activity, AlertCircle, RefreshCw } from 'lucide-react';

const Home: React.FC = () => {
    const [running, setRunning] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [statusLoading, setStatusLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    // Grafana Integration
    const GRAFANA_BASE = "http://localhost:3000/d-solo/inference-monitor/real-time-inference-monitoring";
    const ORG_ID = "1";
    const REFRESH = "5s";
    const THEME = "light";

    const fetchStatus = async () => {
        // If we are performing an action (loading), skip the poll to avoid race conditions
        if (loading) return;

        try {
            const data = await apiService.getStatus();
            // Only update if we are not loading (double check)
            if (!loading) {
                setRunning(data.running);
            }
        } catch (err) {
            console.error("Failed to fetch status", err);
        } finally {
            setStatusLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, [loading]); // Re-create interval if loading changes, effectively pausing/resuming updates

    const handleStart = async () => {
        setLoading(true);
        setError('');
        try {
            await apiService.startDetection();
            setRunning(true);
            fetchStatus(); // immediate refresh
        } catch (err: any) {
            const msg = err.response?.data?.detail || err.message || 'Failed to start detection';
            setError(`Failed to start detection: ${msg}`);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        setLoading(true);
        setError('');
        try {
            await apiService.stopDetection();
            setRunning(false);
            fetchStatus(); // immediate refresh
        } catch (err) {
            setError('Failed to stop detection');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* Header & Controls */}
            <div className="md:flex md:items-center md:justify-between">
                <div className="flex-1 min-w-0">
                    <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                        System Control Center
                    </h2>
                    <p className="mt-1 text-sm text-gray-500">
                        Manage real-time intrusion detection and view live metrics.
                    </p>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4 space-x-3">
                    {/* Status Indicator */}
                    <div className={`flex items-center px-4 py-2 rounded-full border ${statusLoading ? 'bg-gray-100 border-gray-200' :
                        running ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
                        }`}>
                        {statusLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin mr-2 text-gray-500" />
                        ) : (
                            <div className={`h-3 w-3 rounded-full mr-2 ${running ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        )}
                        <span className="font-medium text-sm">
                            {statusLoading ? 'Checking...' : running ? 'SYSTEM RUNNING' : 'SYSTEM STOPPED'}
                        </span>
                    </div>

                    {/* Buttons */}
                    <button
                        onClick={handleStart}
                        disabled={loading || running}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading && !running ? <RefreshCw className="animate-spin -ml-1 mr-2 h-5 w-5" /> : <Play className="-ml-1 mr-2 h-5 w-5" />}
                        Start Detection
                    </button>

                    <button
                        onClick={handleStop}
                        disabled={loading || !running}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading && running ? <RefreshCw className="animate-spin -ml-1 mr-2 h-5 w-5" /> : <Square className="-ml-1 mr-2 h-5 w-5 fill-current" />}
                        Stop Detection
                    </button>
                </div>
            </div>

            {error && (
                <div className="rounded-md bg-red-50 p-4">
                    <div className="flex">
                        <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Operation Failed</h3>
                            <div className="mt-2 text-sm text-red-700">{error}</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Live Stats - Grafana Embeds */}
            <div className="space-y-4">
                <div className="flex items-center space-x-2">
                    <Activity className="h-5 w-5 text-gray-400" />
                    <h3 className="text-lg font-medium text-gray-900">Live Metrics</h3>
                    <span className="text-xs text-gray-400">(Powered by Grafana)</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Total Inference Requests */}
                    <div className="bg-white p-2 rounded-lg shadow h-40 overflow-hidden border border-gray-100">
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=2&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Total Requests"
                        ></iframe>
                    </div>

                    {/* Requests / Sec */}
                    <div className="bg-white p-2 rounded-lg shadow h-40 overflow-hidden border border-gray-100">
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=1&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Throughput"
                        ></iframe>
                    </div>

                    {/* Fraud vs Normal */}
                    <div className="bg-white p-2 rounded-lg shadow h-40 overflow-hidden border border-gray-100">
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=3&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Fraud Ratio"
                        ></iframe>
                    </div>

                    {/* Latency */}
                    <div className="bg-white p-2 rounded-lg shadow h-40 overflow-hidden border border-gray-100">
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=4&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Latency"
                        ></iframe>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {/* Redis Consumer Lag */}
                    <div className="bg-white p-4 rounded-lg shadow h-64 overflow-hidden border border-gray-100">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Redis Stream Consumer Lag</h4>
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=5&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Consumer Lag"
                        ></iframe>
                    </div>

                    {/* Cache Hit Rate */}
                    <div className="bg-white p-4 rounded-lg shadow h-64 overflow-hidden border border-gray-100">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Cache Performance</h4>
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=6&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Cache Hit Rate"
                        ></iframe>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {/* New Inference Throughput (RPS) */}
                    <div className="bg-white p-4 rounded-lg shadow h-64 overflow-hidden border border-gray-100">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Inference Throughput (RPS)</h4>
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=7&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Inference Throughput"
                        ></iframe>
                    </div>

                    {/* New Cache Hit Ratio */}
                    <div className="bg-white p-4 rounded-lg shadow h-64 overflow-hidden border border-gray-100">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Cache Hit Ratio (%)</h4>
                        <iframe
                            src={`${GRAFANA_BASE}?orgId=${ORG_ID}&panelId=8&refresh=${REFRESH}&theme=${THEME}&kiosk`}
                            width="100%" height="100%" frameBorder="0"
                            title="Cache Hit Ratio"
                        ></iframe>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
