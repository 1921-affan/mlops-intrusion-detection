import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Activity, ShieldCheck, List } from 'lucide-react';

const DashboardLayout: React.FC = () => {
    const location = useLocation();

    const navigation = [
        { name: 'System Control', href: '/', icon: LayoutDashboard },
        { name: 'Live Logs', href: '/logs', icon: List },
        { name: 'Model Info', href: '/model-info', icon: FileText },
        { name: 'Monitoring', href: '/monitoring', icon: Activity },
    ];

    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 z-30">
                <div className="flex items-center justify-center h-16 border-b border-gray-200 bg-white">
                    <div className="flex items-center space-x-2">
                        <ShieldCheck className="h-8 w-8 text-indigo-600" />
                        <span className="text-xl font-bold text-gray-900">Intrusion<span className="text-indigo-600">Ops</span></span>
                    </div>
                </div>
                <nav className="mt-5 px-4 space-y-1">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                className={`group flex items-center px-2 py-2 text-base font-medium rounded-md ${isActive
                                    ? 'bg-indigo-50 text-indigo-600'
                                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    }`}
                            >
                                <item.icon
                                    className={`mr-4 h-6 w-6 flex-shrink-0 ${isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500'
                                        }`}
                                    aria-hidden="true"
                                />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>
                <div className="absolute bottom-0 w-full p-4 border-t border-gray-200 bg-gray-50">
                    <p className="text-xs text-center text-gray-500">MLOps Intrusion Detection v1.0</p>
                </div>
            </div>

            {/* Main content */}
            <div className="flex-1 ml-64 flex flex-col min-h-screen">
                <main className="flex-1 p-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
