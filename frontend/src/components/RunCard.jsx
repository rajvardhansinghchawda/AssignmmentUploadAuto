import React from 'react';
import { PlayCircle, CheckCircle2, XCircle, AlertCircle, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function RunCard({ run }) {
  const navigate = useNavigate();
  
  const getStatusConfig = (status) => {
    switch (status) {
      case 'success':
        return { icon: CheckCircle2, color: 'text-primary', glow: 'shadow-success', bg: 'bg-primary/10' };
      case 'failed':
        return { icon: XCircle, color: 'text-error', glow: 'shadow-error', bg: 'bg-error/10' };
      case 'partial':
        return { icon: AlertCircle, color: 'text-yellow-400', glow: '', bg: 'bg-yellow-400/10' };
      case 'running':
        return { icon: PlayCircle, color: 'text-primary-container animate-pulse', glow: 'shadow-bloom', bg: 'bg-primary-container/10' };
      default:
        return { icon: Clock, color: 'text-on-surface-variant', glow: '', bg: 'bg-surface-bright/20' };
    }
  };

  const config = getStatusConfig(run.status);
  const Icon = config.icon;

  return (
    <div 
      onClick={() => navigate(`/runs/${run.id}`)}
      className="glass-panel p-4 rounded-md cursor-pointer hover:bg-surface-bright/30 transition-all duration-300 group"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${config.bg} ${config.glow}`}>
            <Icon className={`h-5 w-5 ${config.color}`} />
          </div>
          <div>
            <div className="text-sm font-medium uppercase tracking-wider text-on-surface">
              {run.status}
            </div>
            <div className="text-xs text-on-surface-variant mt-1">
              Triggered by: {run.triggered_by}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-xs text-on-surface-variant group-hover:text-primary transition-colors">
            {new Date(run.started_at).toLocaleTimeString()}
          </div>
          <div className="text-xs text-on-surface-variant mt-1">
            {run.total_uploaded} uploads
          </div>
        </div>
      </div>
    </div>
  );
}
