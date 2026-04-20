import React from 'react';
import { ExternalLink, Check, Clock } from 'lucide-react';

export function DocCard({ doc }) {
  return (
    <div className="bg-surface-container rounded-md p-4 border border-outline-variant/15 hover:border-primary/30 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-display text-base font-medium text-on-surface">{doc.subject_name}</h4>
          <p className="text-sm text-on-surface-variant mt-1">Assignment {doc.assignment_no}</p>
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${doc.uploaded_to_portal ? 'bg-primary/10 text-primary border-primary/20 shadow-success' : 'bg-surface-bright/30 text-on-surface-variant border-outline-variant/20'}`}>
          {doc.uploaded_to_portal ? <Check className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
          {doc.uploaded_to_portal ? 'Uploaded ✓' : 'Pending'}
        </div>
      </div>
      
      <div className="flex items-center justify-between pt-3 border-t border-outline-variant/15">
        <span className="font-mono text-xs text-on-surface-variant">
          {new Date(doc.created_at).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })}
        </span>
        <a 
          href={doc.drive_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs font-mono text-primary hover:text-primary-container transition-colors"
        >
          OPEN IN DRIVE <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}
