'use client';

import React from 'react';
import { cn } from '@/lib/shadcn/utils';

export type AgentFaceState = 'connecting' | 'initializing' | 'listening' | 'speaking' | 'thinking' | 'disconnected' | 'idle';

interface AgentFaceProps {
  state: AgentFaceState;
  className?: string;
}

export function AgentFace({ state, className }: AgentFaceProps) {
  // Determine color theme based on state
  const getColors = () => {
    switch (state) {
      case 'connecting':
      case 'initializing':
        return {
          bg: 'bg-amber-500/10 border-amber-500/30',
          glow: 'shadow-amber-500/20',
          accent: 'fill-amber-500 stroke-amber-500',
        };
      case 'listening':
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          glow: 'shadow-emerald-500/30 animate-pulse',
          accent: 'fill-emerald-500 stroke-emerald-500',
        };
      case 'speaking':
        return {
          bg: 'bg-indigo-500/10 border-indigo-500/30',
          glow: 'shadow-indigo-500/40 shadow-[0_0_25px_rgba(99,102,241,0.5)]',
          accent: 'fill-indigo-500 stroke-indigo-500',
        };
      case 'thinking':
        return {
          bg: 'bg-purple-500/10 border-purple-500/30',
          glow: 'shadow-purple-500/30 animate-pulse',
          accent: 'fill-purple-500 stroke-purple-500',
        };
      case 'disconnected':
        return {
          bg: 'bg-slate-500/5 border-slate-500/20',
          glow: 'shadow-slate-500/5',
          accent: 'fill-slate-400 stroke-slate-400',
        };
      case 'idle':
      default:
        return {
          bg: 'bg-sky-500/10 border-sky-500/30',
          glow: 'shadow-sky-500/20',
          accent: 'fill-sky-500 stroke-sky-500',
        };
    }
  };

  const colors = getColors();

  // Return SVG path/shapes for different mouth expressions
  const renderMouth = () => {
    switch (state) {
      case 'connecting':
      case 'initializing':
      case 'thinking':
        // A straight line that moves slightly (pulsing)
        return (
          <path
            d="M 28 55 Q 40 55 52 55"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="transition-all duration-500 fill-none"
          />
        );
      case 'listening':
        // An open "O" shape indicating listening
        return (
          <path
            d="M 33 55 Q 40 62 47 55 Q 40 48 33 55"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="transition-all duration-500 fill-none"
          />
        );
      case 'speaking':
        // Animated talking mouth wave shape
        return (
          <path
            d="M 28 55 Q 34 46 40 55 T 52 55"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="animate-[talking_0.4s_infinite_alternate] transition-all duration-300 fill-none"
          />
        );
      case 'disconnected':
        // Muted neutral line
        return (
          <path
            d="M 32 55 L 48 55"
            strokeWidth="3"
            strokeLinecap="round"
            className="transition-all duration-500 fill-none"
          />
        );
      case 'idle':
      default:
        // A friendly curved smile
        return (
          <path
            d="M 28 50 Q 40 62 52 50"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="transition-all duration-500 fill-none"
          />
        );
    }
  };

  // Eyes rendering
  const renderEyes = () => {
    if (state === 'disconnected') {
      // Sleepy/closed eyes
      return (
        <>
          <path d="M 20 38 Q 26 44 32 38" strokeWidth="3" strokeLinecap="round" className="fill-none" />
          <path d="M 48 38 Q 54 44 60 38" strokeWidth="3" strokeLinecap="round" className="fill-none" />
        </>
      );
    }

    if (state === 'speaking') {
      // Happy squinting eyes
      return (
        <>
          <path d="M 20 40 Q 26 34 32 40" strokeWidth="3.5" strokeLinecap="round" className="fill-none" />
          <path d="M 48 40 Q 54 34 60 40" strokeWidth="3.5" strokeLinecap="round" className="fill-none" />
        </>
      );
    }

    if (state === 'thinking' || state === 'connecting' || state === 'initializing') {
      // Eyes looking left and right or blinking
      return (
        <>
          <circle cx="26" cy="38" r="4.5" className="animate-[blink_4s_infinite]" />
          <circle cx="54" cy="38" r="4.5" className="animate-[blink_4s_infinite]" />
        </>
      );
    }

    // Default friendly open eyes
    return (
      <>
        <circle cx="26" cy="38" r="5" className="animate-[blink_5s_infinite]" />
        <circle cx="54" cy="38" r="5" className="animate-[blink_5s_infinite]" />
      </>
    );
  };

  return (
    <div
      className={cn(
        'relative flex size-24 items-center justify-center rounded-full border-2 backdrop-blur-md transition-all duration-500 shadow-lg',
        colors.bg,
        colors.glow,
        className
      )}
    >
      <svg
        viewBox="0 0 80 80"
        className={cn('size-16 transition-all duration-500', colors.accent)}
      >
        {/* Render Eyes */}
        <g className="stroke-current fill-current transition-all duration-500">
          {renderEyes()}
        </g>
        {/* Render Mouth */}
        <g className="stroke-current transition-all duration-500">
          {renderMouth()}
        </g>
      </svg>

      {/* Tailwind local animations style injection */}
      <style jsx global>{`
        @keyframes blink {
          0%, 90%, 100% { transform: scaleY(1); }
          95% { transform: scaleY(0.1); }
        }
        @keyframes talking {
          0% { d: path("M 28 55 Q 40 45 52 55"); }
          100% { d: path("M 28 55 Q 40 65 52 55"); }
        }
      `}</style>
    </div>
  );
}
