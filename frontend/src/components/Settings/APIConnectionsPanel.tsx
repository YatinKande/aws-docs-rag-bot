import React from 'react';
import { Plus, Cloud, CheckCircle2, Trash2, ShieldCheck, Globe, ExternalLink, Key } from 'lucide-react';
import type { APIKey } from '../../types';
import { api } from '../../services/api';

export const APIConnectionsPanel: React.FC = () => {
    const [keys, setKeys] = React.useState<APIKey[]>([]);
    const [isAdding, setIsAdding] = React.useState(false);
    const [newKey, setNewKey] = React.useState({
        provider: 'aws',
        nickname: '',
        access_key: '',
        secret_key: '',
        region: 'us-east-1'
    });

    React.useEffect(() => {
        loadKeys();
    }, []);

    const loadKeys = async () => {
        try {
            const data = await api.getApiKeys();
            setKeys(data);
        } catch (e) {
            console.error(e);
        }
    };

    const handleAddKey = async (e: React.FormEvent) => {
        e.preventDefault();
        const creds = {
            access_key: newKey.access_key,
            secret_key: newKey.secret_key,
            region: newKey.region
        };
        await api.createApiKey(newKey.provider, newKey.nickname, creds);
        setIsAdding(false);
        loadKeys();
    };

    const handleDelete = async (id: string) => {
        if (confirm('Are you sure you want to remove this connection?')) {
            await api.deleteApiKey(id);
            loadKeys();
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-8 space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 tracking-tight">API Connections</h1>
                    <p className="text-sm text-slate-500 mt-1">Manage your cloud provider credentials securely.</p>
                </div>
                {!isAdding && (
                    <button
                        onClick={() => setIsAdding(true)}
                        className="flex items-center px-4 py-2 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 shadow-lg shadow-brand-500/20 transition-all active:scale-95"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Connection
                    </button>
                )}
            </div>

            <div className="bg-brand-50 border border-brand-100 rounded-2xl p-4 flex items-start space-x-3">
                <ShieldCheck className="w-5 h-5 text-brand-600 mt-0.5" />
                <div>
                    <h3 className="text-sm font-bold text-brand-900">Security Guardrails</h3>
                    <p className="text-xs text-brand-700 mt-1 leading-relaxed">
                        All credentials are encrypted at rest using AES-256 (Fernet). We only support read-only access for cloud services. NEVER provide keys with administrative or write permissions.
                    </p>
                </div>
            </div>

            {isAdding && (
                <div className="premium-card p-6 animate-in fade-in slide-in-from-top-4 duration-300">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-bold text-slate-800">New Connection</h2>
                        <button onClick={() => setIsAdding(false)} className="text-sm text-slate-400 hover:text-slate-600 font-medium">Cancel</button>
                    </div>
                    <form onSubmit={handleAddKey} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cloud Provider</label>
                                <select
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                                    value={newKey.provider}
                                    onChange={(e) => setNewKey({ ...newKey, provider: e.target.value as any })}
                                >
                                    <option value="aws">Amazon Web Services (AWS)</option>
                                    <option value="gcp">Google Cloud Platform (GCP)</option>
                                    <option value="azure">Microsoft Azure</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Nickname</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Production AWS"
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                                    value={newKey.nickname}
                                    onChange={(e) => setNewKey({ ...newKey, nickname: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Access Key ID</label>
                                <input
                                    type="text"
                                    placeholder="AKIA..."
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                                    value={newKey.access_key}
                                    onChange={(e) => setNewKey({ ...newKey, access_key: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Secret Access Key</label>
                                <input
                                    type="password"
                                    placeholder="••••••••••••••••"
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                                    value={newKey.secret_key}
                                    onChange={(e) => setNewKey({ ...newKey, secret_key: e.target.value })}
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="w-full py-3 bg-brand-600 text-white font-bold rounded-xl hover:bg-brand-700 transition-all shadow-lg shadow-brand-500/20"
                        >
                            Verify & Save Connection
                        </button>
                    </form>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {keys.map((key) => (
                    <div key={key.id} className="premium-card p-5 group hover:shadow-xl transition-all border-l-4 border-l-aws">
                        <div className="flex justify-between items-start">
                            <div className="flex space-x-4">
                                <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center">
                                    <Cloud className="w-6 h-6 text-aws" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-slate-900">{key.nickname}</h3>
                                    <div className="flex items-center mt-1 space-x-2">
                                        <span className="text-[10px] font-bold text-slate-400 flex items-center">
                                            <Globe className="w-3 h-3 mr-1" /> us-east-1
                                        </span>
                                        <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                                        <span className="text-[10px] font-bold text-emerald-600 flex items-center uppercase tracking-wide">
                                            <CheckCircle2 className="w-3 h-3 mr-1" /> {key.status}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(key.id)}
                                className="p-2 text-slate-300 hover:text-red-500 bg-slate-50 hover:bg-red-50 rounded-lg transition-colors"
                                title="Delete connection"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="mt-6 flex items-center justify-between">
                            <div className="flex -space-x-1">
                                {['EC2', 'S3', 'CE'].map(s => (
                                    <div key={s} className="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-[8px] font-bold text-slate-500 shadow-sm">
                                        {s}
                                    </div>
                                ))}
                            </div>
                            <button className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center">
                                View Details <ExternalLink className="w-3 h-3 ml-1" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {keys.length === 0 && !isAdding && (
                <div className="text-center py-20 bg-slate-50 border-2 border-dashed border-slate-200 rounded-3xl space-y-4">
                    <Key className="w-12 h-12 text-slate-300 mx-auto" />
                    <div>
                        <h3 className="text-sm font-bold text-slate-700">No active connections</h3>
                        <p className="text-xs text-slate-400 mt-1">Connect your AWS, GCP, or Azure accounts to enable live data queries.</p>
                    </div>
                </div>
            )}
        </div>
    );
};
