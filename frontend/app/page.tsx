import { headers } from 'next/headers';
import Image from 'next/image';
import { Header } from '@/components/app/header';
import Tabs from '@/components/app/tabs';
import { getAppConfig } from '@/lib/utils';

export default async function Page() {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-[#F1F5F9] via-[#E2E8F0] to-[#CBD5E1] p-4 text-[#0F172A] md:p-8">
      {/* 3D Styled App Shell */}
      <div className="w-full max-w-4xl overflow-hidden rounded-3xl border border-white/50 bg-white/80 shadow-[0_20px_50px_rgba(0,0,0,0.12)] backdrop-blur-xl">
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
