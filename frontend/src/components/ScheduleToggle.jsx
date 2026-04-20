import React, { useState, useEffect, useRef } from 'react';

export function ScheduleToggle({ isActive, runTime, onUpdate }) {
  const [localActive, setLocalActive] = useState(isActive);
  const [localTime, setLocalTime] = useState(runTime);
  const timerRef = useRef(null);

  useEffect(() => {
    setLocalActive(isActive);
    setLocalTime(runTime);
  }, [isActive, runTime]);

  const handleChange = (newActive, newTime) => {
    setLocalActive(newActive);
    setLocalTime(newTime);

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      onUpdate(newActive, newTime);
    }, 800);
  };

  return (
    <div className="flex items-center gap-6 p-4 rounded-md bg-surface-container-low border border-outline-variant/15">
      <div className="flex items-center gap-3">
        <label className="relative inline-flex items-center cursor-pointer">
          <input 
            type="checkbox" 
            className="sr-only peer" 
            checked={localActive}
            onChange={(e) => handleChange(e.target.checked, localTime)}
          />
          <div className="w-11 h-6 bg-surface-bright rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-container"></div>
        </label>
        <span className="text-sm font-medium text-on-surface">Enable Daily Auto-Run</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-on-surface-variant">Run at</span>
        <input 
          type="time" 
          value={localTime} 
          disabled={!localActive}
          onChange={(e) => handleChange(localActive, e.target.value)}
          className="bg-surface-container-highest border-none text-sm font-mono text-on-surface rounded p-1.5 focus:ring-1 focus:ring-primary/40 disabled:opacity-50 outline-none"
        />
      </div>
    </div>
  );
}
