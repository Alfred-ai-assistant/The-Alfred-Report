'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const res = await fetch('/alfred-report/latest.json', {
          cache: 'no-store',
        });
        if (res.ok) {
          const data = await res.json();
          setReport(data);
        }
      } catch (error) {
        console.error('Failed to fetch report:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, []);

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <h1 className="text-4xl font-bold mb-6">
        The Alfred Report
      </h1>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : !report ? (
        <p className="text-gray-400">
          Report unavailable.
        </p>
      ) : (
        <>
          <p className="text-gray-400 mb-4">
            {report.report_date}
          </p>

          <pre className="bg-zinc-900 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(report, null, 2)}
          </pre>
        </>
      )}
    </main>
  );
}