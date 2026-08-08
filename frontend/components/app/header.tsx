"use client";

import React from 'react';
import Image from 'next/image';
import { useSessionContext } from '@livekit/components-react';

export function Header() {
  const isConnected = false;
  const statusColor = isConnected ? 'text-[#10B981]' : 'text-[#F59E0B]';
  const statusText = isConnected ? 'Secure Session Active' : 'System Ready';

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-[#070B14] text-[#F8FAFC] shadow-md">
      <div className="flex items-center space-x-3">
        <Image src="/logo.svg" alt="VANTARA" width={40} height={40} priority />
        <div>
          <h1 className="text-xl font-bold">Finora AI</h1>
          <p className="text-sm opacity-80">AI Financial Services Assistant</p>
        </div>
      </div>
      <div className="flex items-center space-x-2 text-sm font-medium">
        <span className={statusColor}>●</span>
        <span>{statusText}</span>
        <span className="ml-2 opacity-70">🔒 Secure Voice Session</span>
      </div>
    </header>
  );
}
