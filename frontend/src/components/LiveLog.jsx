import React, { useEffect, useRef } from 'react';
import { useSSE } from '../hooks/useSSE';

export function LiveLog({ runId, isActive }) {
  const bottomRef = useRef(null);
  
  // Only stream if isActive is true
  const streamUrl = isActive ? `assignments/runs/${runId}/stream/` : null;
  const streamedLines = useSSE(streamUrl, isActive);
  
  // For static lines, we would fetch them via a normal API call in RunDetail page
  // and pass them as props, but for simplicity here we assume streamedLines is everything
  // when active.
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [streamedLines]);

  return (
    <div className="bg-surface-container-lowest border border-outline-variant/15 text-primary-fixed font-mono text-sm p-5 rounded-md overflow-y-auto h-96 shadow-inner relative">
      <div className="absolute top-0 right-0 p-3 flex gap-2">
         {isActive && (
           <div className="flex items-center gap-2 text-xs">
             <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
             </span>
             <span className="text-primary-container uppercase font-bold tracking-widest text-[10px]">Listening</span>
           </div>
         )}
      </div>
      
      {streamedLines.length === 0 ? (
        <div className="text-outline-variant h-full flex items-center justify-center italic">
          Waiting for logs...
        </div>
      ) : (
        <div className="space-y-1">
          {streamedLines.map((line, index) => (
            <div key={index} className="break-words">{line}</div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
