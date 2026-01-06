import React from 'react';
import { type LucideIcon } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    subtext?: string;
    trend?: 'up' | 'down' | 'neutral';
    color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, subtext, color = "blue" }) => {
    return (
        <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-100">
            <div className="p-5">
                <div className="flex items-center">
                    <div className={`flex-shrink-0 bg-${color}-50 rounded-md p-3`}>
                        <Icon className={`h-6 w-6 text-${color}-600`} aria-hidden="true" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                        <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
                            <dd>
                                <div className="text-lg font-medium text-gray-900">{value}</div>
                                {subtext && (
                                    <div className="text-sm text-gray-400 mt-1">{subtext}</div>
                                )}
                            </dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StatCard;
