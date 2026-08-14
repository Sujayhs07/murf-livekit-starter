"use client";

import { useState } from 'react';
import { Microphone, PhoneCall } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

function GlowingMic() {
  return (
    <div className="relative mb-8 flex items-center justify-center animate-float">
      {/* Outer ripple effects */}
      <div className="absolute size-32 animate-ping rounded-full bg-emerald-500/10 dark:bg-emerald-400/5 opacity-75 duration-3000" />
      <div className="absolute size-24 animate-pulse rounded-full bg-indigo-500/20 dark:bg-indigo-400/10 duration-2000" />

      {/* Inner visualizer bar-style icons container */}
      <div className="relative flex size-20 items-center justify-center rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-600 shadow-lg shadow-indigo-500/30 animate-pulse-glow">
        <Microphone className="size-10 animate-bounce text-white duration-1500" weight="fill" />
      </div>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [activeTab, setActiveTab] = useState<'inbound' | 'outbound'>('inbound');
  const [target, setTarget] = useState('');
  const [callType, setCallType] = useState('scheme_deadline');
  const [customMessage, setCustomMessage] = useState('');
  const [isCalling, setIsCalling] = useState(false);

  const handleOutboundCall = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) {
      toast.error('Please enter a target username or phone number');
      return;
    }

    setIsCalling(true);
    const loadingToast = toast.loading('Initiating outbound call via Linphone...');

    try {
      const response = await fetch('/api/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: target.trim(), callType, customMessage }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to place call');
      }

      toast.success('Call placed successfully! Check your Linphone app.', {
        id: loadingToast,
      });
    } catch (err: any) {
      toast.error(err.message || 'Error triggering outbound call', {
        id: loadingToast,
      });
    } finally {
      setIsCalling(false);
    }
  };

  return (
    <div ref={ref} className="flex flex-col items-center justify-center px-4 py-8">
      {/* Tab Switcher */}
      <div className="mb-6 flex gap-2 rounded-full bg-slate-100 dark:bg-slate-900 p-1 shadow-inner border border-slate-200/50 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('inbound')}
          className={`rounded-full px-5 py-2 text-xs font-bold transition-all duration-200 ${
            activeTab === 'inbound'
              ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Browser Call
        </button>
        <button
          onClick={() => setActiveTab('outbound')}
          className={`rounded-full px-5 py-2 text-xs font-bold transition-all duration-200 ${
            activeTab === 'outbound'
              ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Phone/SIP Call
        </button>
      </div>

      <section className="mx-auto flex w-full max-w-md flex-col items-center justify-center rounded-3xl p-10 text-center card-3d">
        {activeTab === 'inbound' ? (
          <>
            <GlowingMic />

            <h3 className="bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold tracking-tight text-transparent">
              Talk to Dia
            </h3>

            <p className="mt-2 max-w-xs text-sm font-semibold text-slate-500 dark:text-slate-400">
              Your warm and friendly AI Financial Assistant representing the NFLC.
            </p>

            {/* Feature Tags */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <span className="rounded-full border border-slate-200/40 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 px-3 py-1 text-xs font-bold text-slate-600 dark:text-slate-350">
                🇮🇳 Kannada / Hindi / Hinglish / English
              </span>
              <span className="rounded-full border border-slate-200/40 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 px-3 py-1 text-xs font-bold text-slate-600 dark:text-slate-350">
                📊 Govt Schemes
              </span>
              <span className="rounded-full border border-slate-200/40 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 px-3 py-1 text-xs font-bold text-slate-600 dark:text-slate-350">
                🛡️ Safe Banking
              </span>
            </div>

            <Button
              size="lg"
              onClick={onStartCall}
              className="mt-8 w-64 rounded-full bg-gradient-to-r from-emerald-600 to-indigo-600 text-sm font-extrabold tracking-wider text-white uppercase shadow-lg shadow-emerald-500/20 transition-all duration-200 hover:scale-105 active:scale-95"
            >
              {startButtonText}
            </Button>
          </>
        ) : (
          <form onSubmit={handleOutboundCall} className="w-full flex flex-col items-center">
            <div className="relative mb-6 flex size-20 items-center justify-center rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-600 shadow-lg shadow-indigo-500/30 animate-pulse-glow">
              <PhoneCall className="size-10 text-white animate-pulse" weight="fill" />
            </div>

            <h3 className="bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold tracking-tight text-transparent">
              Request Outbound Call
            </h3>
            
            <p className="mt-2 max-w-xs text-xs font-semibold text-slate-500 dark:text-slate-400">
              Enter your Linphone username or SIP Address to receive a voice call from Dia.
            </p>

            <div className="mt-6 w-full text-left space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                  Linphone Username / SIP User
                </label>
                <input
                  type="text"
                  placeholder="e.g. lucifer252006"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2.5 text-sm font-semibold text-slate-800 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                  Call Scenario / Topic
                </label>
                <select
                  value={callType}
                  onChange={(e) => setCallType(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2.5 text-sm font-semibold text-slate-800 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="scheme_deadline">PM-Kisan Scheme Deadline</option>
                  <option value="payment_reminder">Loan EMI Payment Reminder</option>
                  <option value="itr_deadline">ITR Filing Deadline</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                  Optional Enter Message (Custom Greeting)
                </label>
                <textarea
                  placeholder="e.g. Namaste! This is Dia. I am calling to discuss your credit score options."
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2.5 text-sm font-semibold text-slate-800 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  rows={2}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isCalling}
              size="lg"
              className="mt-8 w-64 rounded-full bg-gradient-to-r from-emerald-600 to-indigo-600 text-sm font-extrabold tracking-wider text-white uppercase shadow-lg shadow-emerald-500/20 transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50"
            >
              {isCalling ? 'Calling...' : 'Call My App'}
            </Button>
          </form>
        )}
      </section>

      <div className="mt-8 flex w-full items-center justify-center">
        <p className="max-w-prose pt-1 text-xs leading-5 font-semibold text-pretty text-slate-400 md:text-sm text-center">
          Need help getting set up? Check out the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="text-indigo-600 underline"
          >
            Voice AI quickstart
          </a>
          .
        </p>
      </div>
    </div>
  );
};
