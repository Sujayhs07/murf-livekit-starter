'use client';

import * as React from 'react';
import type { AppConfig } from '@/app-config';
import { ViewController } from '@/components/app/view-controller';

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  return (
    <main className="grid h-auto grid-cols-1 place-content-center py-4">
      <ViewController appConfig={appConfig} />
    </main>
  );
}
