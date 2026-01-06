import React from 'react';
import { ExternalLink, BarChart2, Database } from 'lucide-react';

const Monitoring: React.FC = () => {
    // Assuming these services are running on localhost ports as per docker-compose
    const GRAFANA_URL = "http://localhost:3000";
    const MLFLOW_URL = "http://localhost:5000";

    const openLink = (url: string) => {
        window.open(url, '_blank');
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
            <p className="text-gray-600">Access external dashboards for detailed metrics and experiment tracking.</p>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {/* Grafana Card */}
                <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0 bg-orange-100 rounded-md p-3">
                                <BarChart2 className="h-8 w-8 text-orange-600" />
                            </div>
                            <div className="ml-5">
                                <h3 className="text-lg font-medium text-gray-900">Grafana Dashboards</h3>
                                <div className="mt-2 text-sm text-gray-500">
                                    Real-time visualization of inference metrics, latency, and data drift.
                                </div>
                            </div>
                        </div>
                        <div className="mt-6">
                            <button
                                onClick={() => openLink(GRAFANA_URL)}
                                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                            >
                                Open Grafana <ExternalLink className="ml-2 -mr-1 h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* MLflow Card */}
                <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                                <Database className="h-8 w-8 text-blue-600" />
                            </div>
                            <div className="ml-5">
                                <h3 className="text-lg font-medium text-gray-900">MLflow Tracking</h3>
                                <div className="mt-2 text-sm text-gray-500">
                                    Model registry, experiment runs, and artifact storage.
                                </div>
                            </div>
                        </div>
                        <div className="mt-6">
                            <button
                                onClick={() => openLink(MLFLOW_URL)}
                                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                Open MLflow <ExternalLink className="ml-2 -mr-1 h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-8 bg-indigo-50 border border-indigo-100 rounded-lg p-4">
                <h4 className="text-sm font-medium text-indigo-800">About Monitoring</h4>
                <p className="mt-1 text-sm text-indigo-700">
                    Metrics are collected via Prometheus. If dashboards are empty, ensure the streaming detection service is running and producing data.
                </p>
            </div>
        </div>
    );
};

export default Monitoring;
