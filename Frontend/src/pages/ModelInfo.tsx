import React, { useEffect, useState } from 'react';
import apiService, { type ModelInfoResponse } from '../services/api';
import { Box, Tag, Terminal } from 'lucide-react';
import StatCard from '../components/StatCard';

const ModelInfo: React.FC = () => {
    const [info, setInfo] = useState<ModelInfoResponse | null>(null);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        const fetchInfo = async () => {
            try {
                const data = await apiService.getModelInfo();
                setInfo(data);
            } catch (err) {
                setError('Failed to load model info');
                console.error(err);
            }
        };

        fetchInfo();
    }, []);

    if (error) {
        return (
            <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">Error loading model info</h3>
                        <div className="mt-2 text-sm text-red-700">{error}</div>
                    </div>
                </div>
            </div>
        );
    }

    if (!info) {
        return <div className="text-gray-500">Loading model information...</div>;
    }

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Model Information</h1>
            <p className="text-gray-600">Details about the currently served MLflow model.</p>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                <StatCard
                    title="Model Alias"
                    value={info.alias}
                    icon={Tag}
                    color="indigo"
                    subtext="Configured environment"
                />
                <StatCard
                    title="Run ID"
                    value={info.run_id}
                    icon={Terminal}
                    color="gray"
                    subtext="MLflow Run Identifier"
                />
                <StatCard
                    title="Model Name"
                    value="model_top20"
                    icon={Box}
                    color="blue"
                    subtext="Registered Model Name"
                />
            </div>

            {/* Metrics & Params Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Parameters */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                    <div className="px-4 py-5 sm:px-6">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">Parameters</h3>
                        <p className="mt-1 max-w-2xl text-sm text-gray-500">Training configuration.</p>
                    </div>
                    <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
                        <dl className="sm:divide-y sm:divide-gray-200">
                            {info.params && Object.entries(info.params).map(([key, val]) => (
                                <div key={key} className="py-3 sm:py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                                    <dt className="text-sm font-medium text-gray-500">{key}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 font-mono">{val}</dd>
                                </div>
                            ))}
                            {(!info.params || Object.keys(info.params).length === 0) && (
                                <div className="px-6 py-4 text-sm text-gray-500">No parameters available.</div>
                            )}
                        </dl>
                    </div>
                </div>

                {/* Metrics */}
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                    <div className="px-4 py-5 sm:px-6">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">Metrics</h3>
                        <p className="mt-1 max-w-2xl text-sm text-gray-500">Model performance on test set.</p>
                    </div>
                    <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
                        <dl className="sm:divide-y sm:divide-gray-200">
                            {info.metrics && Object.entries(info.metrics).map(([key, val]) => (
                                <div key={key} className="py-3 sm:py-4 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                                    <dt className="text-sm font-medium text-gray-500">{key}</dt>
                                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 font-bold text-indigo-600">
                                        {typeof val === 'number' ? val.toFixed(4) : val}
                                    </dd>
                                </div>
                            ))}
                            {(!info.metrics || Object.keys(info.metrics).length === 0) && (
                                <div className="px-6 py-4 text-sm text-gray-500">No metrics available.</div>
                            )}
                        </dl>
                    </div>
                </div>
            </div>

            {/* Artifacts (Plots) */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Artifacts & Plots</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">Visualizations generated during training.</p>
                </div>
                <div className="border-t border-gray-200 px-6 py-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {info.artifacts?.filter(f => f.endsWith('.png')).map((file) => (
                            <div key={file} className="border border-gray-200 rounded-lg p-2 bg-gray-50">
                                <div className="text-xs font-medium text-gray-500 mb-2 truncate" title={file}>{file}</div>
                                <img
                                    src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/model-artifact/${file}`}
                                    alt={file}
                                    className="w-full h-auto rounded shadow-sm"
                                />
                            </div>
                        ))}
                        {(!info.artifacts || info.artifacts.length === 0) && (
                            <div className="text-sm text-gray-500 col-span-2">No artifacts found.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ModelInfo;
