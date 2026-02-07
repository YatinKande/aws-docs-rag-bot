import React from 'react';
import { Upload, Database, FileText, CheckCircle2, AlertCircle, Loader2, Trash2, Zap } from 'lucide-react';
import { api } from '../../services/api';

export const KnowledgeBasePanel: React.FC = () => {
    const [file, setFile] = React.useState<File | null>(null);
    const [database, setDatabase] = React.useState('faiss');
    const [isUploading, setIsUploading] = React.useState(false);
    const [status, setStatus] = React.useState<{ type: 'success' | 'error', message: string } | null>(null);
    const [documents, setDocuments] = React.useState<any[]>([]);
    const [isLoadingDocs, setIsLoadingDocs] = React.useState(false);

    const fetchDocuments = async () => {
        setIsLoadingDocs(true);
        try {
            const docs = await api.getDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
        } finally {
            setIsLoadingDocs(false);
        }
    };

    React.useEffect(() => {
        fetchDocuments();
        // Set up polling for status updates
        const interval = setInterval(fetchDocuments, 5000);
        return () => clearInterval(interval);
    }, []);

    const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
        }
    };

    const onUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        setStatus(null);

        try {
            const result = await api.uploadDocument(file, database);
            setStatus({ type: 'success', message: result.message || 'File uploaded successfully!' });
            setFile(null);
            fetchDocuments(); // Refresh list
            const input = document.getElementById('file-upload') as HTMLInputElement;
            if (input) input.value = '';
        } catch (error) {
            console.error('Upload error:', error);
            setStatus({ type: 'error', message: 'Failed to upload document. Please try again.' });
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-extrabold text-slate-900 mb-2 bg-clip-text text-transparent bg-gradient-to-r from-brand-600 to-indigo-600">Knowledge Base</h1>
                <p className="text-slate-500 font-medium">Upload, track, and manage your documents across multiple local vector databases.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                {/* Upload Section */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center space-x-4 mb-8">
                            <div className="w-12 h-12 bg-brand-50 rounded-2xl flex items-center justify-center">
                                <Upload className="text-brand-600 w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-800">Add New Information</h3>
                                <p className="text-slate-500 text-sm">Upload a new document to your selected database.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-bold text-slate-700 mb-3 uppercase tracking-wider">Storage Engine</label>
                                    <div className="relative">
                                        <select
                                            value={database}
                                            onChange={(e) => setDatabase(e.target.value)}
                                            className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-5 py-4 text-slate-700 appearance-none focus:outline-none focus:ring-4 focus:ring-brand-500/10 focus:border-brand-500 transition-all cursor-pointer font-bold shadow-inner"
                                        >
                                            <option value="faiss">📦 Local FAISS (Fast & Reliable)</option>
                                            <option value="chroma">💾 ChromaDB (SQL-based)</option>
                                            <option value="lancedb">⚡ LanceDB (Modern & Fast)</option>
                                            <option value="milvus">🏢 Milvus (Enterprise-ready)</option>
                                            <option value="qdrant">🔍 Qdrant (High-performance)</option>
                                        </select>
                                        <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                                            <Database className="w-5 h-5" />
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={onUpload}
                                    disabled={!file || isUploading}
                                    className={`w-full py-4 rounded-2xl flex items-center justify-center font-black text-white transition-all shadow-xl group ${!file || isUploading ? 'bg-slate-300 cursor-not-allowed shadow-none' : 'bg-gradient-premium hover:shadow-brand-500/40 transform hover:-translate-y-1 active:scale-95'}`}
                                >
                                    {isUploading ? (
                                        <>
                                            <Loader2 className="w-6 h-6 mr-2 animate-spin" />
                                            Encrypting & Storing...
                                        </>
                                    ) : (
                                        <>
                                            <Upload className="w-6 h-6 mr-2 group-hover:animate-bounce" />
                                            Ingest into {database.toUpperCase()}
                                        </>
                                    )}
                                </button>

                                {status && (
                                    <div className={`p-5 rounded-2xl flex items-start space-x-3 animate-in slide-in-from-top-4 duration-300 ${status.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'}`}>
                                        {status.type === 'success' ? <CheckCircle2 className="w-6 h-6 mt-0.5 flex-shrink-0" /> : <AlertCircle className="w-6 h-6 mt-0.5 flex-shrink-0" />}
                                        <p className="text-sm font-bold tracking-tight">{status.message}</p>
                                    </div>
                                )}
                            </div>

                            <div
                                className={`border-3 border-dashed rounded-3xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer group ${file ? 'border-brand-500 bg-brand-50/20' : 'border-slate-200 hover:border-brand-400 bg-slate-50/50 hover:bg-white'}`}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                                        setFile(e.dataTransfer.files[0]);
                                    }
                                }}
                                onClick={() => document.getElementById('file-upload')?.click()}
                            >
                                <input
                                    type="file"
                                    id="file-upload"
                                    className="hidden"
                                    onChange={onFileChange}
                                    accept=".txt,.pdf,.docx,.json"
                                />
                                {file ? (
                                    <div className="flex flex-col items-center text-center">
                                        <div className="w-20 h-20 bg-brand-100 rounded-3xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform shadow-sm">
                                            <FileText className="text-brand-600 w-10 h-10" />
                                        </div>
                                        <p className="text-slate-900 font-black mb-1 truncate max-w-[250px] leading-tight">{file.name}</p>
                                        <p className="text-slate-400 font-bold text-xs mb-5 uppercase">{(file.size / 1024).toFixed(1)} KB</p>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                            className="text-rose-500 text-xs font-black uppercase tracking-widest hover:text-rose-600 flex items-center bg-rose-50 px-3 py-2 rounded-lg transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4 mr-1.5" /> Remove
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center text-center">
                                        <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mb-5 group-hover:bg-brand-50 transition-all shadow-inner">
                                            <Upload className="text-slate-400 w-10 h-10 group-hover:text-brand-500 transition-colors" />
                                        </div>
                                        <p className="text-slate-700 font-black mb-1">Drop your files here</p>
                                        <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">PDF, TXT, DOCX, JSON</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Document Library */}
                    <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center">
                                    <FileText className="text-indigo-600 w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-slate-800">Knowledge Library</h3>
                                    <p className="text-slate-500 text-sm">Monitor processing and manage your ingested knowledge.</p>
                                </div>
                            </div>
                            <button onClick={fetchDocuments} className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400 hover:text-brand-500">
                                <Loader2 className={`w-5 h-5 ${isLoadingDocs ? 'animate-spin' : ''}`} />
                            </button>
                        </div>

                        <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-inner bg-slate-50/30">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-slate-100/50">
                                        <th className="px-6 py-4 text-[11px] font-black text-slate-500 uppercase tracking-widest">Document</th>
                                        <th className="px-6 py-4 text-[11px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                                        <th className="px-6 py-4 text-[11px] font-black text-slate-500 uppercase tracking-widest">Database</th>
                                        <th className="px-6 py-4 text-[11px] font-black text-slate-500 uppercase tracking-widest">Details</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 bg-white">
                                    {documents.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-6 py-12 text-center text-slate-400 font-bold italic">
                                                No documents found. Start by uploading a file above.
                                            </td>
                                        </tr>
                                    ) : (
                                        documents.map((doc) => (
                                            <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center">
                                                        <div className="w-8 h-8 mr-3 bg-slate-100 rounded-lg flex items-center justify-center text-slate-400">
                                                            <FileText className="w-4 h-4" />
                                                        </div>
                                                        <div>
                                                            <p className="text-sm font-bold text-slate-800 truncate max-w-[150px]">{doc.filename}</p>
                                                            <p className="text-[10px] text-slate-400 font-bold uppercase">{new Date(doc.upload_date).toLocaleDateString()}</p>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider shadow-sm ${doc.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                                                        doc.status === 'processing' ? 'bg-amber-100 text-amber-700 animate-pulse' :
                                                            doc.status === 'failed' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-500'
                                                        }`}>
                                                        {doc.status === 'processing' && <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />}
                                                        {doc.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="text-xs font-black text-brand-600 bg-brand-50 px-2 py-1 rounded-lg uppercase">
                                                        {doc.metadata_info?.target_database || 'faiss'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-[10px] text-slate-500 font-bold">
                                                        {doc.status === 'completed' ? (
                                                            <div className="flex flex-col">
                                                                <span className="text-indigo-600">✓ {doc.metadata_info?.chunks || 0} Chunks</span>
                                                                <span className="text-slate-400">§ {doc.file_type.toUpperCase()} Processed</span>
                                                            </div>
                                                        ) : (
                                                            <span className="text-slate-300 italic">Calculating...</span>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Info Section */}
                <div className="space-y-8">
                    <div className="bg-slate-900 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden group">
                        <div className="relative z-10">
                            <h3 className="text-xl font-black mb-6 flex items-center tracking-tight">
                                <span className="w-10 h-10 bg-brand-500/20 rounded-2xl flex items-center justify-center mr-3 border border-brand-500/30">
                                    <Database className="w-5 h-5 text-brand-400" />
                                </span>
                                Intelligence Engine
                            </h3>
                            <div className="space-y-6">
                                <div className="bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 hover:bg-slate-800 transition-colors">
                                    <p className="font-black text-sm text-brand-400 uppercase tracking-widest mb-1">Local FAISS</p>
                                    <p className="text-slate-400 text-xs font-medium leading-relaxed">Lightning-fast vector operations on your local CPU. Perfect for rapid prototyping.</p>
                                </div>
                                <div className="bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 hover:bg-slate-800 transition-colors">
                                    <p className="font-black text-sm text-amber-400 uppercase tracking-widest mb-1">Enterprise Ready</p>
                                    <p className="text-slate-400 text-xs font-medium leading-relaxed">Scaling to ChromaDB or Milvus allows for production-grade persistent storage.</p>
                                </div>
                            </div>
                        </div>
                        <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-brand-500/10 rounded-full blur-[80px] group-hover:bg-brand-500/20 transition-all duration-700" />
                    </div>

                    <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                        <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center">
                            <Zap className="w-5 h-5 mr-3 text-amber-500" />
                            Ingestion Pipeline
                        </h3>
                        <div className="space-y-6">
                            {[
                                { step: 1, title: 'Deep Extraction', desc: 'Securely parsing documents into high-fidelity text blocks.' },
                                { step: 2, title: 'Semantic Chunking', desc: 'Recursive character splitting with smart overlaps.' },
                                { step: 3, title: 'Vector Embedding', desc: 'Transforming text into 384-dimensional dense vectors.' },
                                { step: 4, title: 'Final Indexing', desc: 'Committing to the vector store with Cosine Similarity.' },
                            ].map((item) => (
                                <div key={item.step} className="flex items-start space-x-4 relative">
                                    {item.step < 4 && <div className="absolute left-[15px] top-10 bottom-[-24px] w-0.5 bg-slate-100" />}
                                    <span className="w-8 h-8 bg-slate-900 text-white rounded-xl flex items-center justify-center text-[11px] font-black flex-shrink-0 z-10 border-4 border-white shadow-sm">
                                        0{item.step}
                                    </span>
                                    <div>
                                        <p className="text-sm font-black text-slate-800 uppercase tracking-tight">{item.title}</p>
                                        <p className="text-xs text-slate-400 font-medium leading-tight">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
