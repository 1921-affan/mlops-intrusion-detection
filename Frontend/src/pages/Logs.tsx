import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import api from '../services/api';

interface LogEntry {
    timestamp: string;
    src_ip: string;
    dst_ip: string;
    attack_type: string;
    prediction: number;
    label: number;
}

const Logs: React.FC = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);

    const fetchLogs = async () => {
        try {
            const data = await api.getLogs();
            setLogs(data.logs);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Activity className="w-6 h-6 text-blue-500" />
                Live Intrusion Logs
            </h1>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source IP</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dest IP</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attack Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {logs.map((log, idx) => (
                            <tr key={idx} className={log.prediction === 1 ? "bg-red-50" : ""}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.src_ip}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.dst_ip}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.attack_type}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    {log.prediction === 1 ? (
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                            <AlertTriangle className="w-3 h-3 mr-1 self-center" /> Detected
                                        </span>
                                    ) : (
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                            <CheckCircle className="w-3 h-3 mr-1 self-center" /> Safe
                                        </span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {logs.length === 0 && (
                    <div className="p-4 text-center text-gray-500">No logs available. Start detection to see live data.</div>
                )}
            </div>
        </div>
    );
};

export default Logs;
