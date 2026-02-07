import React from 'react';
import { ChatPanel } from './components/Chat/ChatPanel';
import { EvidencePanel } from './components/Evidence/EvidencePanel';
import { APIConnectionsPanel } from './components/Settings/APIConnectionsPanel';
import { KnowledgeBasePanel } from './components/KnowledgeBase/KnowledgeBasePanel';
import { Database, MessageSquare, Settings as SettingsIcon, Cloud, Zap, Search, User, BookOpen } from 'lucide-react';
import type { ChatMessage } from './types';
import { api } from './services/api';

const App: React.FC = () => {
  const [view, setView] = React.useState<'chat' | 'settings' | 'knowledge_base'>('chat');
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [selectedSource, setSelectedSource] = React.useState('auto');
  const [selectedDb, setSelectedDb] = React.useState('faiss');

  const onSendMessage = async (content: string) => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.chat(content, selectedSource, selectedDb);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        source_type: response.source_type,
        source_details: response.source_details || []
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please check if the backend is running.',
        timestamp: new Date().toISOString(),
        source_type: 'none'
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="w-16 bg-slate-900 flex flex-col items-center py-6 space-y-8 z-50">
        <div className="w-10 h-10 bg-gradient-premium rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/40">
          <Zap className="text-white w-6 h-6" />
        </div>

        <div className="flex-1 flex flex-col space-y-4">
          <button
            onClick={() => setView('chat')}
            className={`p-3 rounded-xl transition-all duration-200 ${view === 'chat' ? 'bg-brand-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-800'}`}
          >
            <MessageSquare className="w-6 h-6" />
          </button>
          <button
            onClick={() => setView('knowledge_base')}
            className={`p-3 rounded-xl transition-all duration-200 ${view === 'knowledge_base' ? 'bg-brand-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-800'}`}
          >
            <BookOpen className="w-6 h-6" />
          </button>
          <button
            onClick={() => setView('settings')}
            className={`p-3 rounded-xl transition-all duration-200 ${view === 'settings' ? 'bg-brand-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-800'}`}
          >
            <SettingsIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center border border-slate-700">
          <User className="text-slate-400 w-5 h-5" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 z-40">
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-800 tracking-tight">
              {view === 'chat' ? 'Cloud Intelligence' : view === 'settings' ? 'System Settings' : 'Knowledge Base'}
            </h2>
            {view === 'chat' && (
              <span className="flex items-center px-2 py-0.5 bg-brand-50 text-brand-600 text-[10px] font-bold rounded-full border border-brand-100 uppercase tracking-wider">
                Alpha 1.0
              </span>
            )}
          </div>

          {view === 'chat' && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center bg-slate-100 rounded-xl p-1 border border-slate-200">
                <button
                  onClick={() => setSelectedSource('auto')}
                  className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${selectedSource === 'auto' ? 'bg-white text-brand-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  <Search className="w-3 h-3 inline mr-1" /> Auto
                </button>
                <button
                  onClick={() => setSelectedSource('docs')}
                  className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${selectedSource === 'docs' ? 'bg-white text-brand-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  <Database className="w-3 h-3 inline mr-1" /> Knowledge Base
                </button>
                <button
                  onClick={() => setSelectedSource('aws')}
                  className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${selectedSource === 'aws' ? 'bg-white text-aws shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                >
                  <Cloud className="w-3 h-3 inline mr-1" /> AWS
                </button>
              </div>

              {selectedSource === 'docs' && (
                <div className="flex items-center bg-slate-100 rounded-xl p-1 border border-slate-200">
                  <span className="text-[10px] font-bold text-slate-400 px-2 uppercase tracking-wider">DB:</span>
                  <select
                    value={selectedDb}
                    onChange={(e) => setSelectedDb(e.target.value)}
                    className="bg-transparent text-xs font-bold text-brand-600 outline-none pr-4 cursor-pointer"
                  >
                    <option value="faiss">FAISS</option>
                    <option value="chroma">ChromaDB</option>
                    <option value="lancedb">LanceDB</option>
                    <option value="milvus">Milvus</option>
                    <option value="qdrant">Qdrant</option>
                  </select>
                </div>
              )}
            </div>
          )}
        </header>

        <main className="flex-1 flex flex-row overflow-hidden">
          {view === 'chat' ? (
            <>
              <div className="w-[65%] h-full">
                <ChatPanel
                  messages={messages}
                  onSendMessage={onSendMessage}
                  isLoading={isLoading}
                />
              </div>
              <div className="w-[35%] h-full">
                <EvidencePanel
                  sourceType={messages.length > 0 ? messages[messages.length - 1].source_type || 'none' : 'none'}
                  sourceDetails={[]}
                />
              </div>
            </>
          ) : view === 'settings' ? (
            <div className="w-full h-full bg-white overflow-y-auto">
              <APIConnectionsPanel />
            </div>
          ) : (
            <div className="w-full h-full bg-white overflow-y-auto">
              <KnowledgeBasePanel />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
