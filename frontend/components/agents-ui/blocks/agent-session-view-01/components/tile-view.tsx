import React, { useMemo } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  type TrackReference,
  VideoTrack,
  useLocalParticipant,
  useTracks,
  useVoiceAssistant,
  useRemoteParticipants,
} from '@livekit/components-react';
import { cn } from '@/lib/shadcn/utils';
import { AudioVisualizer } from './audio-visualizer';
import { AgentFace } from '@/components/agents-ui/AgentFace';

const ANIMATION_TRANSITION: MotionProps['transition'] = {
  type: 'spring',
  stiffness: 675,
  damping: 75,
  mass: 1,
};

const tileViewClassNames = {
  // GRID
  // 2 Columns x 3 Rows
  grid: [
    'h-full w-full',
    'grid gap-x-2 place-content-center',
    'grid-cols-[1fr_1fr] grid-rows-[90px_1fr_90px]',
  ],
  // Agent
  // chatOpen: true,
  // hasSecondTile: true
  // layout: Column 1 / Row 1
  // align: x-end y-center
  agentChatOpenWithSecondTile: ['col-start-1 row-start-1', 'self-center justify-self-end'],
  // Agent
  // chatOpen: true,
  // hasSecondTile: false
  // layout: Column 1 / Row 1 / Column-Span 2
  // align: x-center y-center
  agentChatOpenWithoutSecondTile: ['col-start-1 row-start-1', 'col-span-2', 'place-content-center'],
  // Agent
  // chatOpen: false
  // layout: Column 1 / Row 1 / Column-Span 2 / Row-Span 3
  // align: x-center y-center
  agentChatClosed: ['col-start-1 row-start-1', 'col-span-2 row-span-3', 'place-content-center'],
  // Second tile
  // chatOpen: true,
  // hasSecondTile: true
  // layout: Column 2 / Row 1
  // align: x-start y-center
  secondTileChatOpen: ['col-start-2 row-start-1', 'self-center justify-self-start'],
  // Second tile
  // chatOpen: false,
  // hasSecondTile: false
  // layout: Column 2 / Row 2
  // align: x-end y-end
  secondTileChatClosed: ['col-start-2 row-start-3', 'place-content-end'],
};

export function useLocalTrackRef(source: Track.Source) {
  const { localParticipant } = useLocalParticipant();
  const publication = localParticipant.getTrackPublication(source);
  const trackRef = useMemo<TrackReference | undefined>(
    () => (publication ? { source, participant: localParticipant, publication } : undefined),
    [source, publication, localParticipant]
  );
  return trackRef;
}

interface TileLayoutProps {
  chatOpen: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerWaveLineWidth?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerBarCount?: number;
}

export function TileLayout({
  chatOpen,
  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerWaveLineWidth,
}: TileLayoutProps) {
  const { videoTrack: agentVideoTrack, state: agentState } = useVoiceAssistant();
  const remoteParticipants = useRemoteParticipants();
  const agentParticipant = remoteParticipants[0];
  const agentMetadata = agentParticipant?.metadata || 'Dia';
  const [screenShareTrack] = useTracks([Track.Source.ScreenShare]);
  const cameraTrack: TrackReference | undefined = useLocalTrackRef(Track.Source.Camera);

  const isCameraEnabled = cameraTrack && !cameraTrack.publication.isMuted;
  const isScreenShareEnabled = screenShareTrack && !screenShareTrack.publication.isMuted;
  const hasSecondTile = isCameraEnabled || isScreenShareEnabled;

  const animationDelay = chatOpen ? 0 : 0.15;
  const isAvatar = agentVideoTrack !== undefined;
  const videoWidth = agentVideoTrack?.publication.dimensions?.width ?? 0;
  const videoHeight = agentVideoTrack?.publication.dimensions?.height ?? 0;

  // Compute status badge details
  const getBadgeDetails = () => {
    const isConnecting = agentState === 'connecting' || agentState === 'initializing';
    const isDisconnected = agentState === 'disconnected';

    if (isConnecting) {
      return {
        statusText: 'Connecting to Dia...',
        roleText: 'Setting up secure line',
        theme: 'connecting',
      };
    }
    if (isDisconnected) {
      return {
        statusText: 'Disconnected',
        roleText: 'Session ended',
        theme: 'disconnected',
      };
    }
    if (agentMetadata === 'connecting_to_krishna') {
      return {
        statusText: 'Connecting to Krishna...',
        roleText: 'Govt Scheme Specialist Handoff',
        theme: 'connecting',
      };
    }
    if (agentMetadata === 'connecting_to_dia') {
      return {
        statusText: 'Connecting to Dia...',
        roleText: 'Financial Assistant Handoff',
        theme: 'connecting',
      };
    }
    if (agentMetadata === 'Krishna') {
      return {
        statusText: 'Krishna',
        roleText: 'Govt Scheme Specialist',
        theme: 'krishna',
      };
    }
    return {
      statusText: 'Dia',
      roleText: 'Financial Assistant',
      theme: 'dia',
    };
  };

  const badge = getBadgeDetails();

  return (
    <div className="absolute inset-x-0 top-8 bottom-32 z-50 md:top-12 md:bottom-40">
      <div className="relative mx-auto h-full max-w-2xl px-4 md:px-0">
        <div className={cn(tileViewClassNames.grid)}>
          {/* Agent */}
          <div
            className={cn([
              'grid',
              !chatOpen && tileViewClassNames.agentChatClosed,
              chatOpen && hasSecondTile && tileViewClassNames.agentChatOpenWithSecondTile,
              chatOpen && !hasSecondTile && tileViewClassNames.agentChatOpenWithoutSecondTile,
            ])}
          >
            <div className="flex flex-col items-center justify-center gap-5">
              <AnimatePresence mode="popLayout">
                {!isAvatar && (
                  // Audio Agent
                  <motion.div
                    key="agent"
                    layoutId="agent"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{
                      ...ANIMATION_TRANSITION,
                      delay: animationDelay,
                    }}
                    className={cn('relative aspect-square h-[90px]')}
                  >
                    <AudioVisualizer
                      key="audio-visualizer"
                      initial={{ scale: 1 }}
                      animate={{ scale: chatOpen ? 0.2 : 1 }}
                      transition={{
                        ...ANIMATION_TRANSITION,
                        delay: animationDelay,
                      }}
                      audioVisualizerType={audioVisualizerType}
                      audioVisualizerColor={audioVisualizerColor}
                      audioVisualizerColorShift={audioVisualizerColorShift}
                      audioVisualizerBarCount={audioVisualizerBarCount}
                      audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
                      audioVisualizerRadialRadius={audioVisualizerRadialRadius}
                      audioVisualizerGridRowCount={audioVisualizerGridRowCount}
                      audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
                      audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
                      isChatOpen={chatOpen}
                      className={cn(
                        'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
                        'bg-background rounded-[50px] border border-transparent transition-[border,drop-shadow]',
                        chatOpen && 'border-input shadow-2xl/10 delay-200'
                      )}
                      style={{ color: audioVisualizerColor }}
                    />
                    <AgentFace
                      state={agentState as any}
                      className={cn(
                        'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 transition-all duration-300',
                        chatOpen ? 'scale-[0.55]' : 'scale-100'
                      )}
                    />
                  </motion.div>
                )}

                {isAvatar && (
                  // Avatar Agent
                  <motion.div
                    key="avatar"
                    layoutId="avatar"
                    initial={{
                      scale: 1,
                      opacity: 1,
                      maskImage:
                        'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 20px, transparent 20px)',
                      filter: 'blur(20px)',
                    }}
                    animate={{
                      maskImage:
                        'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 500px, transparent 500px)',
                      filter: 'blur(0px)',
                      borderRadius: chatOpen ? 6 : 12,
                    }}
                    transition={{
                      ...ANIMATION_TRANSITION,
                      delay: animationDelay,
                      maskImage: {
                        duration: 1,
                      },
                      filter: {
                        duration: 1,
                      },
                    }}
                    className={cn(
                      'overflow-hidden bg-black drop-shadow-xl/80',
                      chatOpen ? 'h-[90px]' : 'h-auto w-full'
                    )}
                  >
                    <VideoTrack
                      width={videoWidth}
                      height={videoHeight}
                      trackRef={agentVideoTrack}
                      className={cn(chatOpen && 'size-[90px] object-cover')}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Status & Identity Badge */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={badge.theme + badge.statusText}
                  initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
                  animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                  exit={{ opacity: 0, y: -12, filter: 'blur(4px)' }}
                  transition={{ duration: 0.3, ease: 'easeOut' }}
                  className={cn(
                    "flex flex-col items-center justify-center px-4 py-2 rounded-2xl border backdrop-blur-md transition-all duration-300 shadow-md w-60",
                    badge.theme === 'dia' && "bg-indigo-500/10 border-indigo-500/20 text-indigo-600 dark:text-indigo-400 shadow-indigo-500/5",
                    badge.theme === 'krishna' && "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400 shadow-amber-500/5",
                    badge.theme === 'connecting' && "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 shadow-emerald-500/5",
                    badge.theme === 'disconnected' && "bg-slate-500/10 border-slate-500/20 text-slate-500 dark:text-slate-400"
                  )}
                >
                  <div className="flex items-center gap-2">
                    {badge.theme === 'connecting' ? (
                      <div className="size-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    ) : badge.theme === 'disconnected' ? (
                      <div className="size-2.5 rounded-full bg-slate-400" />
                    ) : (
                      <div className="relative flex size-2.5 items-center justify-center">
                        <span className={cn(
                          "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                          badge.theme === 'dia' ? "bg-indigo-400" : "bg-amber-400"
                        )} />
                        <span className={cn(
                          "relative inline-flex rounded-full size-2.5",
                          badge.theme === 'dia' ? "bg-indigo-500" : "bg-amber-500"
                        )} />
                      </div>
                    )}
                    <span className="text-sm font-extrabold tracking-wide">{badge.statusText}</span>
                  </div>
                  <span className="text-[10px] font-bold opacity-80 uppercase tracking-widest mt-0.5">{badge.roleText}</span>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          <div
            className={cn([
              'grid',
              chatOpen && tileViewClassNames.secondTileChatOpen,
              !chatOpen && tileViewClassNames.secondTileChatClosed,
            ])}
          >
            {/* Camera & Screen Share */}
            <AnimatePresence>
              {((cameraTrack && isCameraEnabled) || (screenShareTrack && isScreenShareEnabled)) && (
                <motion.div
                  key="camera"
                  layout="position"
                  layoutId="camera"
                  initial={{
                    opacity: 0,
                    scale: 0,
                  }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                  }}
                  exit={{
                    opacity: 0,
                    scale: 0,
                  }}
                  transition={{
                    ...ANIMATION_TRANSITION,
                    delay: animationDelay,
                  }}
                  className="aspect-square size-[90px] drop-shadow-lg/20"
                >
                  <VideoTrack
                    trackRef={cameraTrack || screenShareTrack}
                    width={(cameraTrack || screenShareTrack)?.publication.dimensions?.width ?? 0}
                    height={(cameraTrack || screenShareTrack)?.publication.dimensions?.height ?? 0}
                    className="bg-muted aspect-square size-[90px] rounded-md object-cover"
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
