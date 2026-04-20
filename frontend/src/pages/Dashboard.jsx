import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Activity } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';
import { Navbar } from '../components/Navbar';
import { RunCard } from '../components/RunCard';
import { DocCard } from '../components/DocCard';

export function Dashboard() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [docs, setDocs] = useState([]);
  const [scheduleInfo, setScheduleInfo] = useState({ isActive: false, runTime: '' });
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [runsRes, docsRes, schedRes] = await Promise.all([
        api.get('assignments/runs/').catch(() => ({ data: [] })),
        api.get('assignments/docs/').catch(() => ({ data: [] })),
        api.get('scheduler/').catch(() => ({ data: {} }))
      ]);
      setRuns(runsRes.data);
      setDocs(docsRes.data);
      if (schedRes.data) {
        setScheduleInfo({ 
          isActive: schedRes.data.is_active, 
          runTime: schedRes.data.run_time 
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunNow = async () => {
    setTriggering(true);
    try {
      const res = await api.post('assignments/run/');
      toast.success('Run triggered successfully');
      navigate(`/runs/${res.data.run_id}`);
    } catch (err) {
      if (err.response && err.response.status === 409) {
        toast.error('A run is already in progress. Redirecting...');
        if (err.response.data.run_id) {
          navigate(`/runs/${err.response.data.run_id}`);
        }
      } else {
        toast.error('Failed to trigger run');
      }
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Top Action Bar */}
        <div className="mb-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-display font-semibold text-on-surface tracking-tight">Overview</h1>
            <div className="mt-2 flex items-center gap-2">
              <Activity className={`w-4 h-4 ${scheduleInfo.isActive ? 'text-primary animate-pulse' : 'text-on-surface-variant'}`} />
              <span className="text-sm font-mono text-on-surface-variant uppercase tracking-wider">
                {scheduleInfo.isActive 
                  ? `Schedule Active — Runs at ${scheduleInfo.runTime}` 
                  : 'Schedule Paused'}
              </span>
            </div>
          </div>
          
          <button 
            onClick={handleRunNow}
            disabled={triggering}
            className="flex items-center gap-2 px-6 py-3 gradient-primary text-on-primary-container disabled:opacity-70 font-medium rounded shadow-bloom hover:shadow-glow transition-all"
          >
            <Play className="w-4 h-4 fill-current" />
            {triggering ? 'INITIATING...' : 'RUN NOW'}
          </button>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
          
          {/* Recent Runs */}
          <section className="lg:col-span-5">
            <h2 className="text-lg font-display font-medium text-on-surface mb-6 border-b border-outline-variant/20 pb-2">
              Recent Runs
            </h2>
            <div className="no-divider-stack">
              {runs.length === 0 ? (
                <div className="text-on-surface-variant text-sm italic font-mono p-4 border border-dashed border-outline-variant/30 rounded">
                  No automated runs yet.
                </div>
              ) : (
                runs.map(run => <RunCard key={run.id} run={run} />)
              )}
            </div>
          </section>

          {/* Generated Documents */}
          <section className="lg:col-span-7">
            <h2 className="text-lg font-display font-medium text-on-surface mb-6 border-b border-outline-variant/20 pb-2">
              Generated Documents
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {docs.length === 0 ? (
                <div className="text-on-surface-variant text-sm italic font-mono p-4 border border-dashed border-outline-variant/30 rounded col-span-2">
                  No documents generated yet.
                </div>
              ) : (
                docs.map(doc => <DocCard key={doc.id} doc={doc} />)
              )}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}
