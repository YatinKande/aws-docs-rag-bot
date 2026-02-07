import React from 'react';
import { Send, User, Bot, FileText, Cloud, Layers } from 'lucide-react';
import type { ChatMessage } from '../../types';

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage: (content: string) => void;
    isLoading: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, isLoading }) => {
    const [input, setInput] = React.useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput('');
        }
    };

    return (
        <div className="flex flex-col h-full bg-white border-r border-slate-200">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
                        <Layers className="w-12 h-12 opacity-20" />
                        <p className="text-lg font-medium">How can I help you today?</p>
                        <div className="grid grid-cols-2 gap-3 max-w-md">
                            {['What is my AWS bill?', 'Explain our S3 policy', 'Compare costs to budget', 'List EC2 instances'].map((suggestion) => (
                                <button
                                    key={suggestion}
                                    onClick={() => onSendMessage(suggestion)}
                                    className="px-4 py-2 text-sm text-left border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] flex space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-brand-600' : 'bg-slate-100 border border-slate-200'
                                }`}>
                                {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-brand-600" />}
                            </div>

                            <div className="space-y-2">
                                <div className={`px-4 py-3 rounded-2xl shadow-sm ${msg.role === 'user'
                                    ? 'bg-brand-600 text-white shadow-brand-500/10'
                                    : 'bg-slate-100 text-slate-800'
                                    }`}>
                                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                                </div>

                                {msg.source_type && msg.source_type !== 'none' && (
                                    <div className="flex items-center space-x-2 px-1">
                                        <span className={`flex items-center text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${msg.source_type === 'docs' ? 'bg-blue-100 text-blue-700' :
                                            msg.source_type === 'api' ? 'bg-orange-100 text-orange-700' :
                                                'bg-purple-100 text-purple-700'
                                            }`}>
                                            {msg.source_type === 'docs' ? <FileText className="w-3 h-3 mr-1" /> : <Cloud className="w-3 h-3 mr-1" />}
                                            {msg.source_type === 'docs' ? 'Document' : msg.source_type === 'api' ? 'Live API' : 'Hybrid'}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="flex space-x-3">
                            <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center animate-pulse">
                                <Bot className="w-5 h-5 text-slate-400" />
                            </div>
                            <div className="px-4 py-3 rounded-2xl bg-slate-100 flex items-center space-x-1">
                                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="p-4 bg-slate-50 border-t border-slate-200">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isLoading}
                        placeholder="Type your question..."
                        className="w-full bg-white border border-slate-200 rounded-2xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all disabled:opacity-50 shadow-sm"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 p-2 bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors disabled:bg-slate-300"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </form>
        </div>
    );
};
