import { useEffect, useRef, useState } from 'react';

export function useSSE(url, isActive) {
  const [lines, setLines] = useState([]);
  const esRef = useRef(null);

  useEffect(() => {
    if (!isActive || !url) return;

    const token = localStorage.getItem('piemr_token');
    esRef.current = new EventSource(`${import.meta.env.VITE_API_BASE || '/api/'}${url}?token=${token}`);

    esRef.current.onmessage = (e) => {
      setLines(prev => [...prev, e.data]);
    };

    esRef.current.onerror = () => {
      esRef.current.close();
    };

    return () => esRef.current?.close();
  }, [url, isActive]);

  return lines;
}
