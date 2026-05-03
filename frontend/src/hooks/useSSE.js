import { useEffect, useRef, useState } from 'react';

export function useSSE(url, isActive, initialLines = []) {
  const [lines, setLines] = useState(initialLines);
  const esRef = useRef(null);

  // Sync with initialLines if they change (e.g. when run detail is first loaded)
  useEffect(() => {
    if (initialLines.length > 0 && lines.length === 0) {
      setLines(initialLines);
    }
  }, [initialLines]);

  useEffect(() => {
    if (!isActive || !url) return;

    const token = localStorage.getItem('piemr_token');
    esRef.current = new EventSource(`${import.meta.env.VITE_API_BASE || '/api/'}${url}?token=${token}`);

    esRef.current.onmessage = (e) => {
      // Avoid duplicates if initialLines already contains this data
      setLines(prev => {
        if (prev.includes(e.data)) return prev;
        return [...prev, e.data];
      });
    };

    esRef.current.onerror = () => {
      esRef.current.close();
    };

    return () => esRef.current?.close();
  }, [url, isActive]);

  return lines;
}
