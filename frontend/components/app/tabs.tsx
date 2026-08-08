'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { App } from '@/components/app/app';
import type { AppConfig } from '@/app-config';

// Placeholder Finance Dashboard component
function FinanceDashboard() {
  const [balance, setBalance] = React.useState(12345);
  const [amount, setAmount] = React.useState('');

  const handleAdd = () => {
    const val = parseInt(amount, 10);
    if (!isNaN(val)) setBalance(prev => prev + val);
    setAmount('');
  };

  const handleWithdraw = () => {
    const val = parseInt(amount, 10);
    if (!isNaN(val) && val <= balance) setBalance(prev => prev - val);
    setAmount('');
  };

  return (
    <div className='p-4 text-[#F8FAFC]'>
      <h2 className='text-2xl font-semibold mb-4'>Finance Dashboard</h2>
      <p className='mb-2'>Current Balance: <span className='font-bold'>₹{balance.toLocaleString('en-IN')}</span></p>
      <div className='flex space-x-2 mb-4'>
        <input
          type='number'
          placeholder='Amount (₹)'
          value={amount}
          onChange={e => setAmount(e.target.value)}
          className='flex-1 p-2 rounded bg-gray-800 text-[#F8FAFC] focus:outline-none'
        />
        <button
          onClick={handleAdd}
          className='px-4 py-2 bg-[#10B981] rounded text-white'>Add</button>
        <button
          onClick={handleWithdraw}
          className='px-4 py-2 bg-red-600 rounded text-white'>Withdraw</button>
      </div>
    </div>
  );
}

// Placeholder Settings Dashboard component
function SettingsDashboard() {
  const [notifications, setNotifications] = React.useState(true);
  const [darkMode, setDarkMode] = React.useState(false);
  const [language, setLanguage] = React.useState('en');

  return (
    <div className='p-4 text-[#F8FAFC]'>
      <h2 className='text-2xl font-semibold mb-4'>Settings</h2>
      <div className='flex items-center justify-between mb-2'>
        <span>Enable notifications</span>
        <input type='checkbox' checked={notifications} onChange={() => setNotifications(!notifications)} className='toggle' />
      </div>
      <div className='flex items-center justify-between mb-2'>
        <span>Dark mode</span>
        <input type='checkbox' checked={darkMode} onChange={() => setDarkMode(!darkMode)} className='toggle' />
      </div>
      <div className='flex items-center justify-between'>
        <span>Language</span>
        <select value={language} onChange={e => setLanguage(e.target.value)} className='p-2 rounded bg-gray-800 text-[#F8FAFC]'>
          <option value='en'>English</option>
          <option value='hi'>Hindi</option>
        </select>
      </div>
    </div>
  );
}


function AnalyticsDashboard() {
  return (
    <div className='flex items-center justify-center h-full text-[#F8FAFC]'>
      <h2 className='text-2xl font-semibold'>Analytics (Coming Soon)</h2>
    </div>
  );
}

function HelpDashboard() {
  return (
    <div className='flex items-center justify-center h-full text-[#F8FAFC]'>
      <h2 className='text-2xl font-semibold'>Help (Coming Soon)</h2>
    </div>
  );
}

function ProfileDashboard() {
  return (
    <div className='flex items-center justify-center h-full text-[#F8FAFC]'>
      <h2 className='text-2xl font-semibold'>Profile (Coming Soon)</h2>
    </div>
  );
}

interface TabsProps {
 appConfig: AppConfig;
}

export default function Tabs({ appConfig }: TabsProps) {
  const [activeTab, setActiveTab] = useState<'voice' | 'finance' | 'settings' | 'analytics' | 'help' | 'profile'>('voice');

  return (
  <div className='flex flex-col h-full'>
    {/* Logo at top */}
    <div className='flex justify-center mt-4 mb-4'>
      <Image src={appConfig.logo} alt='logo' width={120} height={40} priority />
    </div>
    {/* Tab selectors */}
    <div className='flex justify-center space-x-4 mb-4'>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('voice')}>
        Voice Assistant
      </button>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('finance')}>
        Finance Dashboard
      </button>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('settings')}>
        Settings
      </button>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('analytics')}>
        Analytics
      </button>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('help')}>
        Help
      </button>
      <button
        className="px-4 py-2 rounded bg-gray-800 text-[#F8FAFC] hover:bg-[#10B981] hover:text-white"
        onClick={() => setActiveTab('profile')}>
        Profile
      </button> </div>
 {/* Content area */}
 <div className='flex-1'>
  {activeTab === 'voice' && <App appConfig={appConfig} />}
  {activeTab === 'finance' && <FinanceDashboard />}
  {activeTab === 'settings' && <SettingsDashboard />}
  {activeTab === 'analytics' && <AnalyticsDashboard />}
  {activeTab === 'help' && <HelpDashboard />}
  {activeTab === 'profile' && <ProfileDashboard />}
 </div>
 </div>
 );
}
