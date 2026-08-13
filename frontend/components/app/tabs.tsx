'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Image from 'next/image';
import type { AppConfig } from '@/app-config';
import { App } from '@/components/app/app';

import { TokenSource } from 'livekit-client';
import { useSession, useSessionContext, useRoomContext } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';
import { AudioVisualizer } from '@/components/agents-ui/blocks/agent-session-view-01/components/audio-visualizer';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();
  return null;
}

// Helper to check window existence for SSR safety
const isClient = () => typeof window !== 'undefined';

// Interactive & Database-backed Finance Dashboard component
function FinanceDashboard() {
  const [balance, setBalance] = useState(12345);
  const [amount, setAmount] = useState('');
  const [transactions, setTransactions] = useState<
    { id: number; type: 'add' | 'withdraw'; amount: number; time: string }[]
  >([]);
  const [escalations, setEscalations] = useState<
    {
      reference_id: string;
      reason: string;
      summary: string;
      what_was_checked: string;
      urgency: string;
      language: string;
      preferred_followup: string;
      status: string;
      timestamp: string;
    }[]
  >([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance);
        setTransactions(data.transactions);
        setEscalations(data.escalations || []);
      }
    } catch (err) {
      console.error('Error fetching finance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleAdd = async () => {
    const val = parseInt(amount, 10);
    if (!isNaN(val) && val > 0) {
      try {
        setLoading(true);
        const res = await fetch('/api/dashboard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'add_transaction', type: 'add', amount: val }),
        });
        if (res.ok) {
          await fetchDashboardData();
        }
      } catch (err) {
        console.error('Error adding transaction:', err);
      } finally {
        setLoading(false);
      }
    }
    setAmount('');
  };

  const handleWithdraw = async () => {
    const val = parseInt(amount, 10);
    if (!isNaN(val) && val > 0 && val <= balance) {
      try {
        setLoading(true);
        const res = await fetch('/api/dashboard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'add_transaction', type: 'withdraw', amount: val }),
        });
        if (res.ok) {
          await fetchDashboardData();
        }
      } catch (err) {
        console.error('Error executing withdrawal:', err);
      } finally {
        setLoading(false);
      }
    }
    setAmount('');
  };

  return (
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-white/85 p-6 text-slate-800 shadow-sm backdrop-blur-md transition-all hover:shadow-md">
      <h2 className="mb-4 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent">
        Finance Dashboard
      </h2>

      <div className="mb-6 rounded-xl border border-slate-100 bg-slate-50 p-4">
        <p className="text-sm font-medium text-slate-500">Current Balance</p>
        <p className="mt-1 text-3xl font-extrabold text-slate-900">
          ₹{balance.toLocaleString('en-IN')}
        </p>
      </div>

      <div className="mb-6 flex space-x-3">
        <input
          type="number"
          placeholder="Amount (₹)"
          value={amount}
          disabled={loading}
          onChange={(e) => setAmount(e.target.value)}
          className="flex-1 rounded-xl border border-slate-200 bg-white p-3 font-medium text-slate-800 placeholder-slate-400 transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none"
        />
        <button
          onClick={handleAdd}
          disabled={loading}
          className="rounded-xl bg-emerald-600 px-6 py-3 font-bold text-white shadow-sm transition-all hover:bg-emerald-700 hover:shadow active:scale-95 disabled:opacity-55"
        >
          Add
        </button>
        <button
          onClick={handleWithdraw}
          disabled={loading}
          className="rounded-xl bg-rose-600 px-6 py-3 font-bold text-white shadow-sm transition-all hover:bg-rose-700 hover:shadow active:scale-95 disabled:opacity-55"
        >
          Withdraw
        </button>
      </div>

      <div>
        <h3 className="text-md mb-3 font-bold text-slate-700">Transaction History</h3>
        {transactions.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No transactions recorded yet.</p>
        ) : (
          <div className="max-h-40 space-y-2 overflow-y-auto pr-2">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between rounded-lg border border-slate-100/80 bg-slate-50/50 p-2.5 text-sm"
              >
                <span className="font-semibold text-slate-500">{tx.time}</span>
                <span
                  className={
                    tx.type === 'add' ? 'font-bold text-emerald-600' : 'font-bold text-rose-600'
                  }
                >
                  {tx.type === 'add' ? '+' : '-'} ₹{tx.amount.toLocaleString('en-IN')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 border-t border-slate-200/60 pt-6">
        <h3 className="text-md mb-3 font-bold text-slate-700">Support Tickets & Escalations</h3>
        {escalations.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No active support requests.</p>
        ) : (
          <div className="max-h-60 space-y-3 overflow-y-auto pr-2 animate-fadeIn">
            {escalations.map((esc) => (
              <div
                key={esc.reference_id}
                className="rounded-lg border border-slate-200/80 bg-slate-50/55 p-3 text-sm shadow-sm hover:border-emerald-200 transition-all"
              >
                <div className="flex items-center justify-between font-bold mb-1">
                  <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">{esc.reference_id}</span>
                  <span className={`px-2 py-0.5 rounded text-xs tracking-wider uppercase ${esc.urgency === 'EMERGENCY' ? 'bg-red-100 text-red-700 border border-red-200 font-extrabold animate-pulse' :
                      esc.urgency === 'HIGH' ? 'bg-orange-100 text-orange-700 border border-orange-200' :
                        esc.urgency === 'MEDIUM' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                          'bg-slate-100 text-slate-700 border border-slate-200'
                    }`}>
                    {esc.urgency} Urgency
                  </span>
                </div>
                <div className="text-xs text-slate-500 mb-2 font-medium">{esc.timestamp} • Status: <span className="font-semibold text-slate-700">{esc.status}</span></div>
                <div className="space-y-1 text-slate-700">
                  <div><strong>Reason:</strong> {esc.reason.replace('_', ' ').toUpperCase()}</div>
                  <div><strong>Language:</strong> {esc.language}</div>
                  <div><strong>Follow-up:</strong> {esc.preferred_followup}</div>
                  <div className="text-slate-600 mt-1 bg-white/70 p-2 rounded border border-slate-100 text-xs italic">{esc.summary}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsDashboard() {
  const { isConnected, start } = useSessionContext();
  const room = useRoomContext();
  const [connecting, setConnecting] = useState(false);
  const [analytics, setAnalytics] = useState({
    total_calls: 0,
    successful_calls: 0,
    failed_calls: 0,
  });
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalyticsData = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
      const historyRes = await fetch('/api/calls');
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData);
      }
    } catch (err) {
      console.error('Error fetching analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    const interval = setInterval(fetchAnalyticsData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartCall = async () => {
    setConnecting(true);
    try {
      await start();
    } catch (e) {
      console.error(e);
    } finally {
      setConnecting(false);
    }
  };

  const total = analytics.total_calls;
  const successRate = total > 0 ? Math.round((analytics.successful_calls / total) * 100) : 0;

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0s';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return isoString;
    }
  };

  return (
    <div className="mx-auto mt-8 max-w-4xl rounded-2xl border border-slate-200 bg-white/85 p-6 text-slate-800 shadow-sm backdrop-blur-md transition-all hover:shadow-md">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent">
            FINORA AI — Call Analytics
          </h2>
          <p className="text-sm font-medium text-slate-500">
            Monitor voice-agent performance and call outcomes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isConnected ? (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50/50 px-3 py-1.5 shadow-sm">
              <div className="relative flex size-10 items-center justify-center overflow-hidden rounded-full bg-emerald-100/50">
                <AudioVisualizer
                  audioVisualizerType="wave"
                  audioVisualizerColor="#059669"
                  isChatOpen={false}
                  className="absolute size-10"
                />
              </div>
              <button
                onClick={() => room.disconnect()}
                className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-bold text-white shadow-sm hover:bg-rose-700 active:scale-95"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              onClick={handleStartCall}
              disabled={connecting}
              className="rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:opacity-90 active:scale-95 disabled:opacity-50"
            >
              {connecting ? 'Connecting...' : 'Talk to Dia'}
            </button>
          )}
          <button
            onClick={() => {
              setLoading(true);
              fetchAnalyticsData();
            }}
            disabled={loading}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 shadow-sm hover:bg-slate-50 active:scale-95 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Calls</p>
          <p className="mt-2 text-3xl font-extrabold text-slate-900">{analytics.total_calls}</p>
        </div>

        <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Successful Calls</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-700">{analytics.successful_calls}</p>
        </div>

        <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-rose-600">Failed Calls</p>
          <p className="mt-2 text-3xl font-extrabold text-rose-700">{analytics.failed_calls}</p>
        </div>

        <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Success Rate</p>
          <p className="mt-2 text-3xl font-extrabold text-indigo-700">{successRate}%</p>
        </div>
      </div>

      <div>
        <h3 className="mb-4 text-lg font-bold text-slate-700">Recent Calls</h3>
        {history.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center">
            <p className="text-sm text-slate-400 italic">No completed calls recorded yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-100 bg-slate-50/30">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-200/60 bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <th className="p-3.5">Call ID</th>
                  <th className="p-3.5">Time</th>
                  <th className="p-3.5">Duration</th>
                  <th className="p-3.5">Language</th>
                  <th className="p-3.5">Channel</th>
                  <th className="p-3.5">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((call) => (
                  <tr key={call.call_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-3.5 font-semibold text-slate-700">{call.call_id}</td>
                    <td className="p-3.5 text-slate-500">{formatTime(call.started_at)}</td>
                    <td className="p-3.5 text-slate-600 font-medium">{formatDuration(call.duration_seconds)}</td>
                    <td className="p-3.5 text-slate-600">{call.language}</td>
                    <td className="p-3.5 text-slate-600 capitalize">{call.channel}</td>
                    <td className="p-3.5">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${call.outcome === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                      >
                        {call.outcome}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Workable Settings Dashboard component (keeps localStorage for device/browser-specific state)
function SettingsDashboard() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    if (isClient()) {
      const savedNotif = localStorage.getItem('settings_notifications');
      const savedDark = localStorage.getItem('settings_dark');
      const savedLang = localStorage.getItem('settings_lang');

      if (savedNotif !== null) setNotifications(savedNotif === 'true');
      if (savedDark !== null) {
        const isDark = savedDark === 'true';
        setDarkMode(isDark);
        // Sync body class
        if (isDark) document.documentElement.classList.add('dark');
        else document.documentElement.classList.remove('dark');
      }
      if (savedLang !== null) setLanguage(savedLang);
    }
  }, []);

  const handleNotificationsChange = () => {
    const nextVal = !notifications;
    setNotifications(nextVal);
    localStorage.setItem('settings_notifications', String(nextVal));
  };

  const handleDarkModeChange = () => {
    const nextVal = !darkMode;
    setDarkMode(nextVal);
    localStorage.setItem('settings_dark', String(nextVal));
    if (nextVal) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextLang = e.target.value;
    setLanguage(nextLang);
    localStorage.setItem('settings_lang', nextLang);
  };

  return (
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-white/85 p-6 text-slate-800 shadow-sm backdrop-blur-md transition-all hover:shadow-md">
      <h2 className="mb-6 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent">
        Settings
      </h2>

      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3">
          <span className="font-semibold text-slate-700">Enable notifications</span>
          <input
            type="checkbox"
            checked={notifications}
            onChange={handleNotificationsChange}
            className="size-5 cursor-pointer accent-emerald-600"
          />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3">
          <span className="font-semibold text-slate-700">Dark mode</span>
          <input
            type="checkbox"
            checked={darkMode}
            onChange={handleDarkModeChange}
            className="size-5 cursor-pointer accent-emerald-600"
          />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3">
          <span className="font-semibold text-slate-700">Language</span>
          <select
            value={language}
            onChange={handleLanguageChange}
            className="rounded-lg border border-slate-200 bg-white p-2 font-medium text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none"
          >
            <option value="en">English</option>
          </select>
        </div>
      </div>
    </div>
  );
}

// Help Dashboard component
function HelpDashboard() {
  const { isConnected, start } = useSessionContext();
  const room = useRoomContext();
  const [connecting, setConnecting] = useState(false);

  const handleStartCall = async () => {
    setConnecting(true);
    try {
      await start();
    } catch (e) {
      console.error(e);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-white/85 p-8 text-slate-800 shadow-sm backdrop-blur-md">
      <div className="text-center mb-8">
        <h2 className="mb-2 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold text-transparent">
          Finora AI — Help & Guide
        </h2>
        <p className="text-sm font-medium text-slate-500">
          Learn how to interact with your AI voice-agent Dia.
        </p>
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            🎙️ Meet Dia — Your AI Voice Agent
          </h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Dia is a multilingual financial assistant speaking both **English** and **Hindi**. She supports browser-based audio conversations to guide you through your financial queries.
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            💡 Supported Tasks & Financial Services
          </h3>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-600 list-disc pl-5">
            <li>Check eligibility and documents needed for government schemes (PMJDY, PMSBY, APY, etc.).</li>
            <li>Look up live exchange rates and cryptocurrency quotes (Bitcoin, Ethereum).</li>
            <li>Calculate monthly EMIs or compound interest savings with decision advice.</li>
            <li>Inquire about secure banking guidelines or check stock market quotes.</li>
          </ul>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            🔒 Privacy & Safety
          </h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Finora AI does not store sensitive personal information such as passwords, CVVs, PINs, OTPs, or full bank account/card numbers. All logs are securely anonymized.
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            🚨 Human Escalation
          </h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            If your query requires human review, Dia will ask for your permission and raise a ticket. You will receive a unique reference ID (e.g., `FIN-2026-XXXX`) to track your support status.
          </p>
        </div>
      </div>

      <div className="mt-8 flex flex-col items-center justify-center gap-4 border-t border-slate-100 pt-6">
        {isConnected ? (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/20 p-6 shadow-sm w-full max-w-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 animate-pulse">Dia is Connected & Listening</span>
            <div className="relative flex size-24 items-center justify-center overflow-hidden rounded-full bg-emerald-100/30">
              <AudioVisualizer
                audioVisualizerType="aura"
                audioVisualizerColor="#019666ff"
                isChatOpen={false}
                className="absolute size-24"
              />
            </div>
            <button
              onClick={() => room.disconnect()}
              className="w-full rounded-xl bg-rose-600 py-3 font-bold text-white shadow-sm hover:bg-rose-700 active:scale-95"
            >
              End Conversation
            </button>
          </div>
        ) : (
          <button
            onClick={handleStartCall}
            disabled={connecting}
            className="rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 px-8 py-3.5 font-extrabold text-white shadow-md hover:opacity-90 active:scale-95 transition-all disabled:opacity-50"
          >
            {connecting ? 'Connecting to Dia...' : 'Start Conversation with Dia'}
          </button>
        )}
      </div>
    </div>
  );
}

interface TabsProps {
  appConfig: AppConfig;
}

function TabsContent({
  appConfig,
  activeTab,
  handleTabChange,
  originTab,
  setOriginTab,
  setActiveTab
}: {
  appConfig: AppConfig;
  activeTab: 'voice' | 'finance' | 'analytics' | 'settings' | 'help';
  handleTabChange: (tab: 'voice' | 'finance' | 'analytics' | 'settings' | 'help') => void;
  originTab: string;
  setOriginTab: React.Dispatch<React.SetStateAction<string>>;
  setActiveTab: React.Dispatch<React.SetStateAction<'voice' | 'finance' | 'analytics' | 'settings' | 'help'>>;
}) {
  const getTabClass = (tab: typeof activeTab) => {
    const base =
      'px-5 py-2.5 rounded-full font-bold text-sm tracking-wide transition-all duration-300 active:scale-95 shadow-sm border';
    if (activeTab === tab) {
      return `${base} bg-gradient-to-r from-emerald-600 to-indigo-600 text-white border-transparent shadow-emerald-500/10`;
    }
    return `${base} bg-white hover:bg-slate-50 text-slate-600 border-slate-200/80 hover:text-slate-900`;
  };

  return (
    <div className="flex h-full flex-col px-4 pb-12 md:px-8">
      {/* Tab selectors */}
      <div className="mx-auto mb-6 flex max-w-4xl flex-wrap justify-center gap-3">
        <button className={getTabClass('voice')} onClick={() => handleTabChange('voice')}>
          Voice Assistant
        </button>
        <button className={getTabClass('finance')} onClick={() => handleTabChange('finance')}>
          Finance Dashboard
        </button>
        <button className={getTabClass('analytics')} onClick={() => handleTabChange('analytics')}>
          Call Analytics
        </button>
        <button className={getTabClass('settings')} onClick={() => handleTabChange('settings')}>
          Settings
        </button>
        <button className={getTabClass('help')} onClick={() => handleTabChange('help')}>
          Help
        </button>
      </div>

      {/* Content area */}
      <div className="w-full flex-1">
        {activeTab === 'voice' && <App appConfig={appConfig} />}
        {activeTab === 'finance' && <FinanceDashboard />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
        {activeTab === 'settings' && <SettingsDashboard />}
        {activeTab === 'help' && <HelpDashboard />}
      </div>
    </div>
  );
}

export default function Tabs({ appConfig }: TabsProps) {
  const [activeTab, setActiveTab] = useState<'voice' | 'finance' | 'analytics' | 'settings' | 'help'>('voice');
  const [originTab, setOriginTab] = useState<string>('voice');

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    setOriginTab(tab);
  };

  const tokenSource = useMemo(() => {
    return TokenSource.endpoint(`/api/token?activeTab=${originTab}`);
  }, [originTab]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      <TabsContent
        appConfig={appConfig}
        activeTab={activeTab}
        handleTabChange={handleTabChange}
        originTab={originTab}
        setOriginTab={setOriginTab}
        setActiveTab={setActiveTab}
      />
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
