'use client';

import React from 'react';

interface FundCardProps {
  name: string;
  nav: string | number;
  date: string;
}

/**
 * Simple card UI that displays a mutual‑fund name, its latest NAV and the date.
 * Uses the dark theme colors defined for the VANTARA site.
 */
const FundCard: React.FC<FundCardProps> = ({ name, nav, date }) => {
  return (
    <div className="rounded-lg bg-gray-800 p-4 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="mb-2 truncate text-lg font-medium text-white" title={name}>
        {name}
      </h3>
      <p className="text-sm text-cyan-400">NAV: {nav}</p>
      <p className="text-xs text-gray-400">Updated: {date}</p>
    </div>
  );
};

export default FundCard;
