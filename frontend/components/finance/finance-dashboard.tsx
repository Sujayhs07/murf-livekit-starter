import React, { useEffect, useState } from 'react';
import FundCard from './fund-card';

/**
 * FinanceDashboard component
 * Fetches a list of mutual fund schemes from the public API and displays them.
 * The API base URL is provided via NEXT_PUBLIC_FINANCE_API environment variable.
 */
const FinanceDashboard: React.FC = () => {
  const [funds, setFunds] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFunds = async () => {
      try {
        // Example: fetching a sample scheme (e.g., 120539) – replace with dynamic list as needed.
        const baseUrl = process.env.NEXT_PUBLIC_FINANCE_API;
        if (!baseUrl) {
          throw new Error('Finance API base URL not configured');
        }
        const response = await fetch(`${baseUrl}120539`);
        if (!response.ok) {
          throw new Error('Failed to fetch finance data');
        }
        const data = await response.json();
        // The API returns an object with a "data" array containing NAV history.
        // We'll map it to a simple fund representation.
        const latest = data?.data?.[data.data.length - 1];
        const fundInfo = {
          name: data?.meta?.scheme_name || 'Unknown Fund',
          nav: latest?.nav || 'N/A',
          date: latest?.date || 'N/A',
        };
        setFunds([fundInfo]);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchFunds();
  }, []);

  if (loading) return <div className="p-4 text-gray-200">Loading finance dashboard...</div>;
  if (error) return <div className="p-4 text-red-400">Error: {error}</div>;

  return (
    <div className="p-6">
      <h2 className="mb-4 text-2xl font-semibold text-white">Finance Dashboard</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {funds.map((fund, idx) => (
          <FundCard key={idx} name={fund.name} nav={fund.nav} date={fund.date} />
        ))}
      </div>
    </div>
  );
};

export default FinanceDashboard;
