async function getReport() {
  const res = await fetch("/alfred-report/latest.json", {
    cache: "no-store",
  });

  if (!res.ok) {
    return null;
  }

  return res.json();
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