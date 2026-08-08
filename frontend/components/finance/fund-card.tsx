"use client";
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
    <div className="rounded-lg bg-gray-800 p-4 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-lg font-medium text-white mb-2 truncate" title={name}>
        {name}
      </h3>
      <p className="text-cyan-400 text-sm">NAV: {nav}</p>
      <p className="text-gray-400 text-xs">Updated: {date}</p>
    </div>
  );
};

export default FundCard;
