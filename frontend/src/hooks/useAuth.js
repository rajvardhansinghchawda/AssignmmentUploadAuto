import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('piemr_token');
    // Basic verification - assuming if token exists, user is authenticated
    // In a real app, you might want to validate the token with the backend
    if (token) {
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
    setIsLoading(false);
  }, []);

  const login = (token, isNewUser) => {
    localStorage.setItem('piemr_token', token);
    setIsAuthenticated(true);
    if (isNewUser) {
      navigate('/setup');
    } else {
      navigate('/dashboard');
    }
  };

  const logout = () => {
    localStorage.removeItem('piemr_token');
    setIsAuthenticated(false);
    navigate('/');
  };

  return { isAuthenticated, isLoading, login, logout };
}
