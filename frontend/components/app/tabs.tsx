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
import { translations } from '@/components/app/translations';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();
  return null;
}

// Helper to check window existence for SSR safety
const isClient = () => typeof window !== 'undefined';

// Interactive & Database-backed Finance Dashboard component
function FinanceDashboard({ language }: { language: string }) {
  const t = translations[language as keyof typeof translations] || translations.en;
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
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl p-6 text-slate-800 dark:text-slate-100 card-3d">
      <h2 className="mb-4 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold text-transparent">
        {t.financeDashboard}
      </h2>

      <div className="mb-6 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/50 p-4 shadow-inner">
        <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{t.currentBalance}</p>
        <p className="mt-1 text-3xl font-black text-slate-900 dark:text-white">
          ₹{balance.toLocaleString('en-IN')}
        </p>
      </div>

      <div className="mb-6 flex space-x-3">
        <input
          type="number"
          placeholder={t.amountPlaceholder}
          value={amount}
          disabled={loading}
          onChange={(e) => setAmount(e.target.value)}
          className="flex-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 font-semibold text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none shadow-xs"
        />
        <button
          onClick={handleAdd}
          disabled={loading}
          className="rounded-xl bg-emerald-600 px-6 py-3 font-bold text-white shadow-md shadow-emerald-600/10 transition-all hover:bg-emerald-700 hover:shadow-lg active:translate-y-0.5 active:scale-98 disabled:opacity-55"
        >
          {t.add}
        </button>
        <button
          onClick={handleWithdraw}
          disabled={loading}
          className="rounded-xl bg-rose-600 px-6 py-3 font-bold text-white shadow-md shadow-rose-600/10 transition-all hover:bg-rose-700 hover:shadow-lg active:translate-y-0.5 active:scale-98 disabled:opacity-55"
        >
          {t.withdraw}
        </button>
      </div>

      <div>
        <h3 className="text-md mb-3 font-bold text-slate-700 dark:text-slate-300">{t.transactionHistory}</h3>
        {transactions.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-500 italic">{t.noTransactions}</p>
        ) : (
          <div className="max-h-40 space-y-2 overflow-y-auto pr-2">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between rounded-lg border border-slate-100/80 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 p-2.5 text-sm"
              >
                <span className="font-semibold text-slate-500 dark:text-slate-400">{tx.time}</span>
                <span
                  className={
                    tx.type === 'add' ? 'font-extrabold text-emerald-600 dark:text-emerald-400' : 'font-extrabold text-rose-600 dark:text-rose-400'
                  }
                >
                  {tx.type === 'add' ? '+' : '-'} ₹{tx.amount.toLocaleString('en-IN')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 border-t border-slate-200/60 dark:border-slate-800/60 pt-6">
        <h3 className="text-md mb-3 font-bold text-slate-700 dark:text-slate-300">{t.supportTickets}</h3>
        {escalations.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-500 italic">{t.noSupportRequests}</p>
        ) : (
          <div className="max-h-60 space-y-3 overflow-y-auto pr-2 animate-fadeIn">
            {escalations.map((esc) => (
              <div
                key={esc.reference_id}
                className="rounded-lg border border-slate-200/80 dark:border-slate-800 bg-slate-50/55 dark:bg-slate-900/40 p-3 text-sm shadow-sm hover:border-emerald-200 dark:hover:border-emerald-800/80 transition-all"
              >
                <div className="flex items-center justify-between font-bold mb-1">
                  <span className="text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">{esc.reference_id}</span>
                  <span className={`px-2 py-0.5 rounded text-xs tracking-wider uppercase font-bold ${esc.urgency === 'EMERGENCY' ? 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800/60 animate-pulse' :
                      esc.urgency === 'HIGH' ? 'bg-orange-100 text-orange-700 border border-orange-200 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800/60' :
                      esc.urgency === 'MEDIUM' ? 'bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60' :
                      'bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-350 dark:border-slate-700'
                    }`}>
                    {esc.urgency} {t.urgency}
                  </span>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">{esc.timestamp} • Status: <span className="font-semibold text-slate-700 dark:text-slate-300">{esc.status}</span></div>
                <div className="space-y-1 text-slate-750 dark:text-slate-200">
                  <div><strong>{t.reason}:</strong> {esc.reason.replace('_', ' ').toUpperCase()}</div>
                  <div><strong>{t.languageLabel}:</strong> {esc.language}</div>
                  <div><strong>{t.followUp}:</strong> {esc.preferred_followup}</div>
                  <div className="text-slate-600 dark:text-slate-300 mt-1 bg-white/70 dark:bg-slate-900/60 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs italic">{esc.summary}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsDashboard({ language }: { language: string }) {
  const t = translations[language as keyof typeof translations] || translations.en;
  const { isConnected, start } = useSessionContext();
  const room = useRoomContext();
  const [connecting, setConnecting] = useState(false);
  const [analytics, setAnalytics] = useState({
    total_calls: 0,
    successful_calls: 0,
    failed_calls: 0,
    total_handoffs: 0,
    specialist_handoffs: 0,
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
    <div className="mx-auto mt-8 max-w-4xl p-6 text-slate-800 dark:text-slate-100 card-3d">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold text-transparent">
            {t.analyticsTitle}
          </h2>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            {t.analyticsSub}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isConnected ? (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-100 dark:border-emerald-800/40 bg-emerald-50/50 dark:bg-emerald-950/30 px-3 py-1.5 shadow-sm">
              <div className="relative flex size-10 items-center justify-center overflow-hidden rounded-full bg-emerald-100/50 dark:bg-emerald-900/30">
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
                {t.disconnect}
              </button>
            </div>
          ) : (
            <button
              onClick={handleStartCall}
              disabled={connecting}
              className="rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md transition-all hover:opacity-90 active:translate-y-0.5 active:scale-98 disabled:opacity-50"
            >
              {connecting ? t.connecting : t.talkToDia}
            </button>
          )}
          <button
            onClick={() => {
              setLoading(true);
              fetchAnalyticsData();
            }}
            disabled={loading}
            className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2.5 text-xs font-bold text-slate-600 dark:text-slate-300 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-800 active:translate-y-0.5 active:scale-98 disabled:opacity-55"
          >
            {loading ? t.refreshing : t.refresh}
          </button>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/40 p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{t.totalCalls}</p>
          <p className="mt-2 text-3xl font-black text-slate-900 dark:text-white">{analytics.total_calls}</p>
        </div>

        <div className="rounded-xl border border-emerald-100 dark:border-emerald-950 bg-emerald-50/50 dark:bg-emerald-950/20 p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">{t.successfulCalls}</p>
          <p className="mt-2 text-3xl font-black text-emerald-700 dark:text-emerald-300">{analytics.successful_calls}</p>
        </div>

        <div className="rounded-xl border border-rose-100 dark:border-rose-950 bg-rose-50/50 dark:bg-rose-950/20 p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">{t.failedCalls}</p>
          <p className="mt-2 text-3xl font-black text-rose-700 dark:text-rose-300">{analytics.failed_calls}</p>
        </div>

        <div className="rounded-xl border border-indigo-100 dark:border-indigo-950 bg-indigo-50/50 dark:bg-indigo-950/20 p-4 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">{t.successRate}</p>
          <p className="mt-2 text-3xl font-black text-indigo-700 dark:text-indigo-300">{successRate}%</p>
        </div>
      </div>

      <div className="mb-8 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-900/20 p-6 shadow-sm">
        <h3 className="mb-4 text-sm font-extrabold uppercase tracking-wider text-slate-400 dark:text-slate-500">{t.agentHandoffs}</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-xs">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{t.agentHandoffs}</p>
            <p className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{analytics.total_handoffs || 0}</p>
          </div>
          <div className="rounded-xl border border-indigo-100 dark:border-indigo-900/40 bg-indigo-50/40 dark:bg-indigo-950/30 p-4 shadow-xs">
            <p className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">{t.specialistHandoffs}</p>
            <p className="mt-2 text-2xl font-black text-indigo-700 dark:text-indigo-300">{analytics.specialist_handoffs || 0}</p>
          </div>
          <div className="rounded-xl border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/30 p-4 shadow-xs">
            <p className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">{t.handoffRate}</p>
            <p className="mt-2 text-2xl font-black text-emerald-700 dark:text-emerald-300">
              {analytics.total_calls > 0 ? Math.round(((analytics.specialist_handoffs || 0) / analytics.total_calls) * 100) : 0}%
            </p>
          </div>
        </div>
      </div>

      <div>
        <h3 className="mb-4 text-lg font-bold text-slate-700 dark:text-slate-300">{t.recentCalls}</h3>
        {history.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 dark:border-slate-800 p-8 text-center">
            <p className="text-sm text-slate-400 dark:text-slate-500 italic">{t.noCalls}</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/10">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-200/60 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="p-3.5">{t.callId}</th>
                  <th className="p-3.5">{t.time}</th>
                  <th className="p-3.5">{t.duration}</th>
                  <th className="p-3.5">{t.languageLabel}</th>
                  <th className="p-3.5">{t.channel}</th>
                  <th className="p-3.5">{t.agent}</th>
                  <th className="p-3.5">{t.handoff}</th>
                  <th className="p-3.5">{t.outcome}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {history.map((call) => (
                  <tr key={call.call_id} className="hover:bg-slate-50/80 dark:hover:bg-slate-900/40 transition-colors">
                    <td className="p-3.5 font-bold text-slate-700 dark:text-slate-300">{call.call_id}</td>
                    <td className="p-3.5 text-slate-500 dark:text-slate-400">{formatTime(call.started_at)}</td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300 font-semibold">{formatDuration(call.duration_seconds)}</td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300">{call.language}</td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300 capitalize">{call.channel}</td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300 font-semibold">
                      {call.handoff_occurred ? 'Dia → Government Scheme Specialist' : 'Dia'}
                    </td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300">
                      {call.handoff_occurred ? t.yes : t.no}
                    </td>
                    <td className="p-3.5">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${call.outcome === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/80'
                            : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/80'
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
function SettingsDashboard({
  notifications,
  setNotifications,
  darkMode,
  setDarkMode,
  language,
  setLanguage,
}: {
  notifications: boolean;
  setNotifications: React.Dispatch<React.SetStateAction<boolean>>;
  darkMode: boolean;
  setDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
  language: string;
  setLanguage: React.Dispatch<React.SetStateAction<string>>;
}) {
  const t = translations[language as keyof typeof translations] || translations.en;

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
    <div className="mx-auto mt-8 max-w-2xl p-6 text-slate-800 dark:text-slate-100 card-3d">
      <h2 className="mb-6 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold text-transparent">
        {t.settings}
      </h2>

      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/40 p-3">
          <span className="font-semibold text-slate-700 dark:text-slate-200">{t.enableNotifications}</span>
          <input
            type="checkbox"
            checked={notifications}
            onChange={handleNotificationsChange}
            className="size-5 cursor-pointer accent-emerald-600"
          />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/40 p-3">
          <span className="font-semibold text-slate-700 dark:text-slate-200">{t.darkMode}</span>
          <input
            type="checkbox"
            checked={darkMode}
            onChange={handleDarkModeChange}
            className="size-5 cursor-pointer accent-emerald-600"
          />
        </div>

        <div className="flex items-center justify-between rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/40 p-3">
          <span className="font-semibold text-slate-700 dark:text-slate-200">{t.languageSelect}</span>
          <select
            value={language}
            onChange={handleLanguageChange}
            className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 font-medium text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none"
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="kn">Kannada</option>
          </select>
        </div>
      </div>
    </div>
  );
}

// Help Dashboard component
function HelpDashboard({ language }: { language: string }) {
  const t = translations[language as keyof typeof translations] || translations.en;
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
    <div className="mx-auto mt-8 max-w-2xl p-8 text-slate-800 dark:text-slate-100 card-3d">
      <div className="text-center mb-8">
        <h2 className="mb-2 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold text-transparent">
          {t.helpTitle}
        </h2>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          {t.helpSub}
        </p>
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 p-4">
          <h3 className="font-bold text-slate-850 dark:text-slate-100 flex items-center gap-2">
            {t.diaHeading}
          </h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {t.diaDesc}
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 p-4">
          <h3 className="font-bold text-slate-855 dark:text-slate-100 flex items-center gap-2">
            {t.tasksHeading}
          </h3>
          <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-350 list-disc pl-5">
            <li>{t.task1}</li>
            <li>{t.task2}</li>
            <li>{t.task3}</li>
            <li>{t.task4}</li>
          </ul>
        </div>

        <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 p-4">
          <h3 className="font-bold text-slate-850 dark:text-slate-100 flex items-center gap-2">
            {t.privacyHeading}
          </h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {t.privacyDesc}
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 p-4">
          <h3 className="font-bold text-slate-850 dark:text-slate-100 flex items-center gap-2">
            {t.escalationHeading}
          </h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {t.escalationDesc}
          </p>
        </div>
      </div>

      <div className="mt-8 flex flex-col items-center justify-center gap-4 border-t border-slate-100 dark:border-slate-800 pt-6">
        {isConnected ? (
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/20 dark:bg-emerald-950/20 p-6 shadow-sm w-full max-w-sm animate-float">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 animate-pulse">{t.listening}</span>
            <div className="relative flex size-24 items-center justify-center overflow-hidden rounded-full bg-emerald-100/30 dark:bg-emerald-900/20 animate-pulse-glow">
              <AudioVisualizer
                audioVisualizerType="aura"
                audioVisualizerColor="#019666ff"
                isChatOpen={false}
                className="absolute size-24"
              />
            </div>
            <button
              onClick={() => room.disconnect()}
              className="w-full rounded-xl bg-rose-600 py-3 font-bold text-white shadow-md hover:bg-rose-700 active:scale-95 transition-all"
            >
              {t.endConversation}
            </button>
          </div>
        ) : (
          <button
            onClick={handleStartCall}
            disabled={connecting}
            className="rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 px-8 py-3.5 font-extrabold text-white shadow-md hover:opacity-90 active:translate-y-0.5 active:scale-98 transition-all disabled:opacity-50"
          >
            {connecting ? t.connecting : t.startConversation}
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
  setActiveTab,
  notifications,
  setNotifications,
  darkMode,
  setDarkMode,
  language,
  setLanguage,
}: {
  appConfig: AppConfig;
  activeTab: 'voice' | 'finance' | 'analytics' | 'settings' | 'help';
  handleTabChange: (tab: 'voice' | 'finance' | 'analytics' | 'settings' | 'help') => void;
  originTab: string;
  setOriginTab: React.Dispatch<React.SetStateAction<string>>;
  setActiveTab: React.Dispatch<React.SetStateAction<'voice' | 'finance' | 'analytics' | 'settings' | 'help'>>;
  notifications: boolean;
  setNotifications: React.Dispatch<React.SetStateAction<boolean>>;
  darkMode: boolean;
  setDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
  language: string;
  setLanguage: React.Dispatch<React.SetStateAction<string>>;
}) {
  const t = translations[language as keyof typeof translations] || translations.en;
  const getTabClass = (tab: typeof activeTab) => {
    const base =
      'px-5 py-2.5 rounded-full font-bold text-sm tracking-wide transition-all duration-300 active:translate-y-0.5 active:shadow-inner border';
    if (activeTab === tab) {
      return `${base} bg-gradient-to-r from-emerald-600 to-indigo-600 text-white border-transparent shadow-lg shadow-emerald-500/25`;
    }
    return `${base} bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/80 text-slate-650 dark:text-slate-200 border-slate-200/80 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white shadow-sm`;
  };

  return (
    <div className="flex h-full flex-col px-4 pb-12 md:px-8">
      {/* Tab selectors */}
      <div className="mx-auto mb-6 flex max-w-4xl flex-wrap justify-center gap-3">
        <button className={getTabClass('voice')} onClick={() => handleTabChange('voice')}>
          {t.voiceAssistant}
        </button>
        <button className={getTabClass('finance')} onClick={() => handleTabChange('finance')}>
          {t.financeDashboard}
        </button>
        <button className={getTabClass('analytics')} onClick={() => handleTabChange('analytics')}>
          {t.callAnalytics}
        </button>
        <button className={getTabClass('settings')} onClick={() => handleTabChange('settings')}>
          {t.settings}
        </button>
        <button className={getTabClass('help')} onClick={() => handleTabChange('help')}>
          {t.help}
        </button>
      </div>

      {/* Content area */}
      <div className="w-full flex-1">
        {activeTab === 'voice' && <App appConfig={appConfig} />}
        {activeTab === 'finance' && <FinanceDashboard language={language} />}
        {activeTab === 'analytics' && <AnalyticsDashboard language={language} />}
        {activeTab === 'settings' && (
          <SettingsDashboard
            notifications={notifications}
            setNotifications={setNotifications}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            language={language}
            setLanguage={setLanguage}
          />
        )}
        {activeTab === 'help' && <HelpDashboard language={language} />}
      </div>
    </div>
  );
}

export default function Tabs({ appConfig }: TabsProps) {
  const [activeTab, setActiveTab] = useState<'voice' | 'finance' | 'analytics' | 'settings' | 'help'>('voice');
  const [originTab, setOriginTab] = useState<string>('voice');

  // Lifted settings states
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

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    setOriginTab(tab);
  };

  const tokenSource = useMemo(() => {
    return TokenSource.endpoint(
      `/api/token?activeTab=${originTab}&notifications=${notifications}&darkMode=${darkMode}&language=${language}`
    );
  }, [originTab, notifications, darkMode, language]);

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
        notifications={notifications}
        setNotifications={setNotifications}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        language={language}
        setLanguage={setLanguage}
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
