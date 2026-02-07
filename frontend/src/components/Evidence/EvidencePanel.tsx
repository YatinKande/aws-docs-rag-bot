import React from 'react';
import { FileText, Cloud, BarChart3, Activity, ExternalLink, Clock } from 'lucide-react';

interface EvidencePanelProps {
    sourceType: string;
    sourceDetails: any[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ sourceType }) => {
    return (
        <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white sticky top-0 z-10">
                <h2 className="text-sm font-semibold text-slate-700 flex items-center">
                    <Activity className="w-4 h-4 mr-2 text-brand-500" />
                    Evidence & Data
                </h2>
                <div className="flex space-x-1">
                    {['Sources', 'Metrics', 'Logs'].map((tab) => (
                        <button key={tab} className={`px-3 py-1 text-xs font-medium rounded-lg ${tab === 'Sources' ? 'bg-brand-50 text-brand-600' : 'text-slate-500 hover:bg-slate-100'
                            }`}>
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            <div className="p-4 space-y-4">
                {sourceType === 'api' && (
                    <div className="space-y-4 animate-in fade-in duration-500">
                        <div className="premium-card p-4">
                            <div className="flex items-center justify-between mb-4">
                                <span className="flex items-center text-xs font-bold text-slate-500 uppercase tracking-wider">
                                    <Cloud className="w-4 h-4 mr-2 text-aws" />
                                    Live AWS Data
                                </span>
                                <span className="text-[10px] text-slate-400 flex items-center">
                                    <Clock className="w-3 h-3 mr-1" /> Just now
                                </span>
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between items-end border-b border-slate-50 pb-2">
                                    <span className="text-xs text-slate-500 font-medium">AWS Cost Explorer</span>
                                    <span className="text-lg font-bold text-slate-800">$12,450.00</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2 mt-4">
                                    {['EC2: $5.2k', 'S3: $2.8k', 'RDS: $2.5k', 'Other: $1.9k'].map((item) => (
                                        <div key={item} className="p-2 bg-slate-50 rounded-lg text-[10px] font-medium text-slate-600 border border-slate-100">
                                            {item}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {sourceType === 'docs' && (
                    <div className="space-y-4 animate-in fade-in duration-500">
                        {[1, 2].map((i) => (
                            <div key={i} className="premium-card p-4 hover:border-brand-200 transition-colors cursor-pointer group">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center">
                                        <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center mr-3 group-hover:bg-blue-100 transition-colors">
                                            <FileText className="w-4 h-4 text-blue-600" />
                                        </div>
                                        <div>
                                            <h3 className="text-xs font-bold text-slate-800">AWS_Well_Architected_{i}.pdf</h3>
                                            <p className="text-[10px] text-slate-400">Section: Infrastructure & Cost</p>
                                        </div>
                                    </div>
                                    <ExternalLink className="w-3 h-3 text-slate-300 group-hover:text-brand-500 transition-colors" />
                                </div>
                                <div className="p-3 bg-slate-50 rounded-xl">
                                    <p className="text-[11px] text-slate-600 leading-relaxed italic">
                                        "Implementing cost-effective strategies for EC2 instance selection involves choosing the right instance types for your workload..."
                                    </p>
                                </div>
                                <div className="mt-3 flex items-center justify-between">
                                    <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                        <div className="h-full bg-brand-500" style={{ width: '85%' }}></div>
                                    </div>
                                    <span className="text-[9px] font-bold text-brand-600">85% Relevance</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {(!sourceType || sourceType === 'none') && (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-4">
                        <BarChart3 className="w-10 h-10 opacity-20" />
                        <p className="text-xs font-medium">No context available for this request.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
