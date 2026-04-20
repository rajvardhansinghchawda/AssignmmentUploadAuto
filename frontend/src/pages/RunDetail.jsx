import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, PlayCircle, CheckCircle2, XCircle, AlertCircle, Square } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';
import { Navbar } from '../components/Navbar';
import { LiveLog } from '../components/LiveLog';
import { DocCard } from '../components/DocCard';

export function RunDetail() {
  const { id } = useParams();
  const [run, setRun] = useState(null);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stopping, setStopping] = useState(false);

  useEffect(() => {
    const fetchRunData = async () => {
      try {
        const [runRes, docsRes] = await Promise.all([
          api.get(`assignments/runs/${id}/`),
          api.get(`assignments/docs/?run_id=${id}`) // Assuming the backend filters by run_id
        ]);
        setRun(runRes.data);
        setDocs(docsRes.data || []);
      } catch (err) {
        console.error("Failed to load run", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRunData();
  }, [id]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="h-5 w-5 text-primary" />;
      case 'failed': return <XCircle className="h-5 w-5 text-error" />;
      case 'partial': return <AlertCircle className="h-5 w-5 text-yellow-400" />;
      case 'running': return <PlayCircle className="h-5 w-5 text-primary-container animate-pulse" />;
      default: return <Clock className="h-5 w-5 text-on-surface-variant" />;
    }
  };

  const handleStop = async () => {
    if (!window.confirm("Are you sure you want to stop the current pipeline run?")) return;
    
    setStopping(true);
    try {
      await api.post(`assignments/runs/${id}/stop/`);
      toast.success("Stop signal sent.");
      // Refresh run data to show stopped status
      const runRes = await api.get(`assignments/runs/${id}/`);
      setRun(runRes.data);
    } catch (err) {
      toast.error("Failed to stop run.");
      console.error(err);
    } finally {
      setStopping(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-on-surface-variant">
          Loading run details...
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-on-surface-variant">
          Run not found.
        </div>
      </div>
    );
  }

  const isRunning = run.status === 'running';

  return (
    <div className="min-h-screen bg-background flex flex-col pb-12">
      <Navbar />

      <main className="w-full max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm text-on-surface-variant hover:text-primary transition-colors mb-8 font-mono tracking-wide">
          <ArrowLeft className="h-4 w-4" /> BACK TO DASHBOARD
        </Link>
        
        {/* Header Section */}
        <div className="glass-panel p-6 rounded-lg mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                {getStatusIcon(run.status)}
                <h1 className="text-2xl font-display font-semibold text-on-surface">Run #{String(run.id).slice(0, 8)}</h1>
              </div>
              <p className="text-sm text-on-surface-variant">
                {run.triggered_by === 'manual' ? 'Triggered manually by user.' : `Triggered automatically by ${run.triggered_by} schedule.`}
              </p>
            </div>
            
            <div className="flex flex-col gap-3 text-right items-end">
              <div className="flex items-center gap-2">
                {isRunning && (
                  <button
                    onClick={handleStop}
                    disabled={stopping}
                    className="flex items-center gap-2 px-3 py-1.5 bg-error/10 hover:bg-error/20 text-error text-xs font-mono font-medium rounded border border-error/30 transition-all uppercase tracking-wider"
                  >
                    <Square className="h-3 w-3 fill-current" />
                    {stopping ? 'Stopping...' : 'Stop Pipeline'}
                  </button>
                )}
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-surface-container-highest border border-outline-variant/20 w-fit">
                  <span className={`h-2 w-2 rounded-full ${isRunning ? 'bg-primary-container animate-pulse' : (run.status === 'success' ? 'bg-primary' : 'bg-on-surface-variant')}`}></span>
                  <span className="text-xs font-mono uppercase tracking-wider text-on-surface">{run.status}</span>
                </div>
              </div>
              <div className="text-xs font-mono text-on-surface-variant">
                STARTED: {new Date(run.started_at).toLocaleTimeString()}<br/>
                {run.finished_at && `FINISHED: ${new Date(run.finished_at).toLocaleTimeString()}`}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4 mb-12">
          <h2 className="text-sm font-mono tracking-widest text-on-surface-variant uppercase ml-2 flex items-center gap-2">
            <span className="w-4 h-px bg-outline-variant/30"></span> 
            Terminal Console
          </h2>
          <LiveLog runId={id} isActive={isRunning} />
        </div>

        {docs.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-sm font-mono tracking-widest text-on-surface-variant uppercase ml-2 flex items-center gap-2">
              <span className="w-4 h-px bg-outline-variant/30"></span> 
              Documents Generated
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {docs.map(doc => <DocCard key={doc.id} doc={doc} />)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
