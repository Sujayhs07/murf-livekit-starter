import { Header } from '@/components/app/header';
import Image from 'next/image';
import { headers } from 'next/headers';
import { getAppConfig } from '@/lib/utils';
import Tabs from '@/components/app/tabs';

export default async function Page() {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);

  return (
    <div className="min-h-screen bg-[#070B14] text-[#F8FAFC]">
      {/* Logo at top */}
      <div className="flex justify-center py-4">
        <Image src="/logo.svg" alt="Vantara Logo" width={80} height={80} priority />
      </div>
      {/* Header (status bar) */}
      <Header />
      {/* Tabs for Voice / Finance */}
      <Tabs appConfig={appConfig} />
    </div>
  );
}
