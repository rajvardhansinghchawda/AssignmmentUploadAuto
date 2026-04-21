import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';
import { ScheduleToggle } from '../components/ScheduleToggle';

export function Setup() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [enrollmentNo, setEnrollmentNo] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [isActive, setIsActive] = useState(true);
  const [runTime, setRunTime] = useState('08:00');

  useEffect(() => {
    // Fetch existing config if any
    api.get('config/')
      .then(res => {
        if (res.data?.enrollment_no) setEnrollmentNo(res.data.enrollment_no);
        if (res.data?.full_name) setFullName(res.data.full_name);
      })
      .catch(console.error);
      
    // Fetch schedule
    api.get('scheduler/')
      .then(res => {
        if (res.data) {
          setIsActive(res.data.is_active ?? true);
          if (res.data.run_time) setRunTime(res.data.run_time);
        }
      })
      .catch(console.error);
  }, []);

  const handleSaveCredentials = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('config/', { 
        full_name: fullName, 
        enrollment_no: enrollmentNo, 
        piemr_password: password 
      });
      toast.success('Credentials saved securely', {
        style: {
          background: '#0b1326',
          color: '#dae2fd',
          border: '1px solid #1c2971'
        }
      });
      // Optionally clear password field
      setPassword('');
    } catch (err) {
      toast.error('Failed to save credentials');
    } finally {
      setSubmitting(false);
    }
  };

  const handleScheduleUpdate = async (newActive, newTime) => {
    try {
      await api.post('scheduler/', { is_active: newActive, run_time: newTime });
      setIsActive(newActive);
      setRunTime(newTime);
      toast.success('Schedule updated');
    } catch (err) {
      toast.error('Failed to update schedule');
    }
  };

  return (
    <div className="min-h-screen bg-background py-16 px-4">
      <div className="max-w-xl mx-auto space-y-8">
        
        <div className="mb-10 text-center">
           <h1 className="font-display text-3xl font-bold text-on-surface">Configuration</h1>
           <p className="text-on-surface-variant mt-2">Initialize your automated workspace.</p>
        </div>

        <div className="glass-panel rounded-lg overflow-hidden relative">
          <div className="p-6 border-b border-outline-variant/15">
            <h2 className="font-display font-medium text-lg text-primary mb-6 flex items-center gap-2">
              <span className="w-1 h-4 bg-primary rounded-full"></span>
              PIEMR Portal Credentials
            </h2>
            
            <form onSubmit={handleSaveCredentials} className="space-y-5">
              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-2 uppercase tracking-wide">
                  Full Name (for document footer)
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  className="w-full bg-surface-container-highest border border-transparent focus:border-primary/40 rounded px-4 py-2.5 text-on-surface outline-none transition-colors"
                  placeholder="e.g. John Doe"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-2 uppercase tracking-wide">
                  Enrollment Number
                </label>
                <input
                  type="text"
                  value={enrollmentNo}
                  onChange={e => setEnrollmentNo(e.target.value)}
                  className="w-full bg-surface-container-highest border border-transparent focus:border-primary/40 rounded px-4 py-2.5 text-on-surface outline-none transition-colors"
                  placeholder="e.g. 0808CS..."
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-on-surface-variant mb-2 uppercase tracking-wide flex justify-between">
                  <span>Portal Password</span>
                  <button 
                    type="button" 
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-primary hover:text-primary-fixed transition-colors"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full bg-surface-container-highest border border-transparent focus:border-primary/40 rounded px-4 py-2.5 text-on-surface outline-none transition-colors"
                  placeholder="Password is never sent to frontend if previously saved"
                  required
                />
                <p className="text-[10px] uppercase font-mono text-on-surface-variant/50 mt-2 text-right">
                  Stored securely using AES-256 encryption
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center justify-center gap-2 px-5 py-2.5 bg-surface-container-high hover:bg-surface-bright text-primary font-medium rounded transition-colors group"
                >
                  <Save className="h-4 w-4 group-hover:scale-110 transition-transform" />
                  Save Credentials
                </button>
              </div>
            </form>
          </div>

          <div className="p-6 bg-surface-container-lowest/50">
            <h2 className="font-display font-medium text-lg text-primary mb-6 flex items-center gap-2">
              <span className="w-1 h-4 bg-primary-container rounded-full"></span>
              Automation Schedule
            </h2>
            
            <ScheduleToggle 
              isActive={isActive} 
              runTime={runTime} 
              onUpdate={handleScheduleUpdate} 
            />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-6 py-3 gradient-primary text-on-primary-container rounded font-medium hover:shadow-bloom transition-all group"
          >
            Go to Dashboard
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

      </div>
    </div>
  );
}
