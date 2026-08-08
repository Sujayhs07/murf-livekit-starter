import React from 'react';
import styles from '@/components/AvatarOrb.module.css';

export type AgentState = 'ready' | 'connecting' | 'listening' | 'speaking' | 'ended';

interface AvatarOrbProps {
  state: AgentState;
}

export const AvatarOrb: React.FC<AvatarOrbProps> = ({ state }) => {
  const className = `${styles.orb} ${styles[state]}`;
  return <div className={className} aria-label="AI avatar" />;
};
