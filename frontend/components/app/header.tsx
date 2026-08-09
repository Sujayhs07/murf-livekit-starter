'use client';

import React from 'react';
import Image from 'next/image';
import { useSessionContext } from '@livekit/components-react';

export function Header() {
  const isConnected = false;
  const statusColor = isConnected ? 'text-[#10B981]' : 'text-[#F59E0B]';
  const statusText = isConnected ? 'Secure Session Active' : 'System Ready';

  return (
    <header className="flex flex-col md:flex-row items-center justify-between px-8 py-5 bg-white/70 backdrop-blur-md text-[#1E293B] border-b border-slate-200/60">
      <div className="flex items-center space-x-4 mb-4 md:mb-0">
        {/* 3D styled layered logo container */}
        <div className="relative p-2.5 bg-gradient-to-br from-white to-slate-100 rounded-2xl shadow-[4px_4px_10px_rgba(0,0,0,0.15),-2px_-2px_10px_rgba(255,255,255,0.8)] border border-slate-200/50 transform hover:scale-105 hover:rotate-2 transition-all duration-300">
          <Image src="/logo.svg" alt="VANTARA" width={44} height={44} priority />
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-transparent">Finora AI</h1>
          <p className="text-xs font-bold text-slate-400">AI Financial Services Assistant</p>
        </div>
      </div>
      <div className="flex items-center space-x-3 text-sm font-semibold text-slate-600 bg-slate-50/80 px-4 py-2.5 rounded-2xl border border-slate-100 shadow-inner">
        <span className={statusColor}>●</span>
        <span className="font-bold text-slate-700">{statusText}</span>
        <span className="ml-1 opacity-90 text-xs px-2.5 py-1 bg-white border border-slate-200/40 rounded-xl font-mono shadow-sm">🔒 Secure Voice Session</span>
      </div>
    </header>
  );
}
