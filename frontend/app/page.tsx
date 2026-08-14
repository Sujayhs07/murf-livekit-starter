import { headers } from 'next/headers';
import Image from 'next/image';
import { Header } from '@/components/app/header';
import Tabs from '@/components/app/tabs';
import { getAppConfig } from '@/lib/utils';

export default async function Page() {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-[#F1F5F9] via-[#E2E8F0] to-[#CBD5E1] dark:from-[#090D16] dark:via-[#111827] dark:to-[#090D16] p-4 text-[#0F172A] dark:text-slate-100 md:p-8 transition-colors duration-300">
      {/* 3D Styled App Shell */}
      <div className="w-full max-w-4xl overflow-hidden rounded-3xl border border-white/50 dark:border-slate-800/60 bg-white/80 dark:bg-slate-950/75 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.15)] dark:shadow-[0_30px_70px_rgba(0,0,0,0.55)] backdrop-blur-xl transition-all duration-300">
        {/* Header */}
        <Header />
        {/* Tabs for Voice / Finance */}
        <div className="p-4 md:p-6">
          <Tabs appConfig={appConfig} />
        </div>
      </div>
    </div>
  );
}
