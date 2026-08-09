'use client';

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import type { AppConfig } from '@/app-config';
import { App } from '@/components/app/app';

// Helper to check window existence for SSR safety
const isClient = () => typeof window !== 'undefined';

// Interactive & Database-backed Finance Dashboard component
function FinanceDashboard() {
  const [balance, setBalance] = useState(12345);
  const [amount, setAmount] = useState('');
  const [transactions, setTransactions] = useState<
    { id: number; type: 'add' | 'withdraw'; amount: number; time: string }[]
  >([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance);
        setTransactions(data.transactions);
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
            <option value="hi">Hindi</option>
            <option value="hi-en">Hinglish</option>
          </select>
        </div>
      </div>
    </div>
  );
}

// Help Dashboard component
function HelpDashboard() {
  return (
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-white/85 p-8 text-center text-slate-600 shadow-sm backdrop-blur-md">
      <h2 className="mb-2 bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-bold text-transparent">
        Help & Support
      </h2>
      <p className="mb-4 font-medium text-slate-400">How can we help you today?</p>
      <div className="space-y-3 text-left">
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
          <p className="font-bold text-slate-700">How do I access schemes?</p>
          <p className="mt-1 text-sm text-slate-500">
            Talk to Dia using the Voice Assistant tab to check eligibility instantly.
          </p>
        </div>
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
          <p className="font-bold text-slate-700">Is my data secure?</p>
          <p className="mt-1 text-sm text-slate-500">
            Yes, Finora AI never saves sensitive details like PINs, OTPs, or passwords.
          </p>
        </div>
      </div>
    </div>
  );
}

interface TabsProps {
  appConfig: AppConfig;
}

export default function Tabs({ appConfig }: TabsProps) {
  const [activeTab, setActiveTab] = useState<'voice' | 'finance' | 'settings' | 'help'>('voice');

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
        <button className={getTabClass('voice')} onClick={() => setActiveTab('voice')}>
          Voice Assistant
        </button>
        <button className={getTabClass('finance')} onClick={() => setActiveTab('finance')}>
          Finance Dashboard
        </button>
        <button className={getTabClass('settings')} onClick={() => setActiveTab('settings')}>
          Settings
        </button>
        <button className={getTabClass('help')} onClick={() => setActiveTab('help')}>
          Help
        </button>
      </div>

      {/* Content area */}
      <div className="w-full flex-1">
        {activeTab === 'voice' && <App appConfig={appConfig} />}
        {activeTab === 'finance' && <FinanceDashboard />}
        {activeTab === 'settings' && <SettingsDashboard />}
        {activeTab === 'help' && <HelpDashboard />}
      </div>
    </div>
  );
}
