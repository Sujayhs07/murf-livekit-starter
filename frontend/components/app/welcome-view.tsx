import { Microphone } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';

function GlowingMic() {
  return (
    <div className="relative mb-8 flex items-center justify-center">
      {/* Outer ripple effects */}
      <div className="absolute size-32 animate-ping rounded-full bg-emerald-500/10 opacity-75 duration-3000" />
      <div className="absolute size-24 animate-pulse rounded-full bg-indigo-500/20 duration-2000" />

      {/* Inner visualizer bar-style icons container */}
      <div className="relative flex size-20 items-center justify-center rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-600 shadow-lg shadow-indigo-500/30">
        <Microphone className="size-10 animate-bounce text-white duration-1500" weight="fill" />
      </div>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="flex flex-col items-center justify-center px-4 py-8">
      <section className="mx-auto flex max-w-md flex-col items-center justify-center rounded-3xl border border-slate-200/80 bg-white/70 p-10 text-center shadow-xl backdrop-blur-md transition-all duration-300 hover:shadow-2xl">
        <GlowingMic />

        <h3 className="bg-gradient-to-r from-emerald-600 to-indigo-600 bg-clip-text text-2xl font-extrabold tracking-tight text-transparent">
          Talk to Dia
        </h3>

        <p className="mt-2 max-w-xs text-sm font-semibold text-slate-500">
          Your warm and friendly AI Financial Assistant representing the NFLC.
        </p>

        {/* Feature Tags */}
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <span className="rounded-full border border-slate-200/40 bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            🇮🇳 Hindi / Hinglish / English
          </span>
          <span className="rounded-full border border-slate-200/40 bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            📊 Govt Schemes
          </span>
          <span className="rounded-full border border-slate-200/40 bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            🛡️ Safe Banking
          </span>
        </div>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 w-64 rounded-full bg-gradient-to-r from-emerald-600 to-indigo-600 text-sm font-extrabold tracking-wider text-white uppercase shadow-md transition-all duration-200 hover:scale-105 active:scale-95"
        >
          {startButtonText}
        </Button>
      </section>

      <div className="mt-8 flex w-full items-center justify-center">
        <p className="max-w-prose pt-1 text-xs leading-5 font-semibold text-pretty text-slate-400 md:text-sm">
          Need help getting set up? Check out the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="text-indigo-600 underline"
          >
            Voice AI quickstart
          </a>
          .
        </p>
      </div>
    </div>
  );
};
