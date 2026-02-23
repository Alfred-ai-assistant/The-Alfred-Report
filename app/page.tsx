async function getReport() {
  try {
    // Try absolute URL first (for Vercel SSR)
    const baseUrl = process.env.VERCEL_URL 
      ? `https://${process.env.VERCEL_URL}`
      : "http://localhost:3000";
    
    const url = `${baseUrl}/alfred-report/latest.json`;
    const res = await fetch(url, {
      cache: "no-store",
    });

    if (!res.ok) {
      console.error(`Fetch failed: ${res.status} ${res.statusText}`);
      return null;
    }

    return res.json();
  } catch (error) {
    console.error("Failed to fetch report:", error);
    return null;
  }
}

export default async function Home() {
  const report = await getReport();

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <h1 className="text-4xl font-bold mb-6">
        The Alfred Report
      </h1>

      {!report ? (
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