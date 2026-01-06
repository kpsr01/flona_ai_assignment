import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Loader2, 
  Video, 
  FileJson, 
  Download, 
  CheckCircle2,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import VideoPreview from './components/VideoPreview';
import TranscriptView from './components/TranscriptView';
import Timeline from './components/Timeline';
import InsertionsList from './components/InsertionsList';
import { 
  healthCheck, 
  getSampleData, 
  generatePlan, 
  renderVideo, 
  getRenderStatus,
  getDownloadUrl 
} from './api';

function App() {
  const [sampleData, setSampleData] = useState(null);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, generating, completed, rendering, rendered
  const [renderJobId, setRenderJobId] = useState(null);
  const [apiHealth, setApiHealth] = useState(null);

  // Check API health and load sample data on mount
  useEffect(() => {
    const init = async () => {
      try {
        const health = await healthCheck();
        setApiHealth(health);
        
        const data = await getSampleData();
        setSampleData(data);
      } catch (err) {
        setError('Failed to connect to API. Make sure the backend is running.');
        console.error(err);
      }
    };
    init();
  }, []);

  // Poll render status
  useEffect(() => {
    if (!renderJobId) return;
    
    const interval = setInterval(async () => {
      try {
        const status = await getRenderStatus(renderJobId);
        if (status.status === 'completed') {
          setStatus('rendered');
          clearInterval(interval);
        } else if (status.status === 'failed') {
          setError(`Render failed: ${status.error}`);
          setStatus('completed');
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [renderJobId]);

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);
    setStatus('generating');
    setPlan(null);
    
    try {
      const result = await generatePlan(true);
      setPlan(result);
      setStatus('completed');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setStatus('idle');
    } finally {
      setLoading(false);
    }
  };

  const handleRenderVideo = async () => {
    if (!plan) return;
    
    setStatus('rendering');
    setError(null);
    
    try {
      const result = await renderVideo(plan);
      setRenderJobId(result.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setStatus('completed');
    }
  };

  const handleDownloadPlan = () => {
    if (!plan) return;
    
    const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'timeline_plan.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
                <Sparkles className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold">Flona AI</h1>
                <p className="text-sm text-slate-400">B-Roll Insertion System</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {apiHealth ? (
                <span className="flex items-center gap-1 text-sm text-green-400">
                  <CheckCircle2 size={16} />
                  API Connected
                </span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-red-400">
                  <AlertCircle size={16} />
                  API Disconnected
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-900/50 border border-red-700 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="text-red-400" />
            <p className="text-red-200">{error}</p>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              ×
            </button>
          </div>
        )}

        {/* Video Sources */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Video className="text-blue-400" />
            Video Sources
          </h2>
          
          {sampleData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* A-Roll */}
              <div>
                <h3 className="text-lg font-medium mb-3 text-green-400">A-Roll (Main Video)</h3>
                <VideoPreview 
                  url={sampleData.a_roll.url}
                  title="A-Roll"
                  metadata={sampleData.a_roll.metadata}
                />
              </div>
              
              {/* B-Rolls Grid */}
              <div>
                <h3 className="text-lg font-medium mb-3 text-blue-400">B-Roll Clips ({sampleData.b_rolls.length})</h3>
                <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-2">
                  {sampleData.b_rolls.map((broll) => (
                    <VideoPreview 
                      key={broll.id}
                      url={broll.url}
                      title={broll.id}
                      metadata={broll.metadata}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Actions */}
        <section className="mb-8">
          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleGeneratePlan}
              disabled={loading || !apiHealth?.gemini_configured}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-medium transition-colors"
            >
              {loading && status === 'generating' ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Analyzing Videos...
                </>
              ) : (
                <>
                  <Play size={20} />
                  Generate B-Roll Plan
                </>
              )}
            </button>
            
            {plan && (
              <>
                <button
                  onClick={handleDownloadPlan}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  <FileJson size={20} />
                  Download Plan JSON
                </button>
                
                <button
                  onClick={handleRenderVideo}
                  disabled={status === 'rendering'}
                  className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  {status === 'rendering' ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Rendering...
                    </>
                  ) : (
                    <>
                      <Video size={20} />
                      Render Final Video
                    </>
                  )}
                </button>
                
                {status === 'rendered' && renderJobId && (
                  <a
                    href={getDownloadUrl(`${renderJobId}.mp4`)}
                    download
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 px-6 py-3 rounded-lg font-medium transition-colors"
                  >
                    <Download size={20} />
                    Download Rendered Video
                  </a>
                )}
              </>
            )}
          </div>
          
          {!apiHealth?.gemini_configured && (
            <p className="mt-2 text-yellow-400 text-sm">
              ⚠️ Gemini API key not configured. Set GEMINI_API_KEY in backend/.env
            </p>
          )}
        </section>

        {/* Results */}
        {plan && (
          <section className="space-y-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <CheckCircle2 className="text-green-400" />
              Generated Plan
              <span className="text-sm font-normal text-slate-400">
                (A-Roll Duration: {plan.a_roll_duration?.toFixed(1)}s)
              </span>
            </h2>
            
            {/* Timeline */}
            <Timeline 
              duration={plan.a_roll_duration}
              transcript={plan.transcript}
              insertions={plan.insertions}
            />
            
            {/* Transcript and Insertions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TranscriptView 
                segments={plan.transcript}
                insertions={plan.insertions}
              />
              <InsertionsList 
                insertions={plan.insertions}
                bRolls={plan.b_rolls}
              />
            </div>
          </section>
        )}

        {/* Loading State */}
        {loading && status === 'generating' && (
          <div className="text-center py-12">
            <Loader2 className="animate-spin mx-auto mb-4" size={48} />
            <h3 className="text-lg font-medium mb-2">Analyzing Videos with Gemini AI</h3>
            <p className="text-slate-400">
              This may take 1-2 minutes. We're transcribing the A-roll,<br />
              analyzing B-roll clips, and generating the optimal insertion plan.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 border-t border-slate-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-slate-400 text-sm">
          Flona AI - Automated B-Roll Insertion System | Powered by Gemini AI
        </div>
      </footer>
    </div>
  );
}

export default App;
