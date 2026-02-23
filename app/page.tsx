export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white p-10">
      <h1 className="text-4xl font-bold mb-6">
        The Alfred Report
      </h1>
      <p className="text-gray-400 mb-4">
        Loading report data...
      </p>
      <div id="report-container">
        <p className="text-sm text-gray-500">
          Data will load below when JavaScript runs.
        </p>
      </div>

      <script dangerouslySetInnerHTML={{__html: `
        (async () => {
          try {
            const res = await fetch('/alfred-report/latest.json');
            const report = await res.json();
            const container = document.getElementById('report-container');
            if (container) {
              container.innerHTML = '<pre style="background: #27272a; padding: 1rem; border-radius: 0.5rem; font-size: 0.875rem; overflow-x: auto; color: #e4e4e7;">' + 
                JSON.stringify(report, null, 2) + 
                '</pre>';
            }
          } catch (error) {
            const container = document.getElementById('report-container');
            if (container) {
              container.innerHTML = '<p class="text-red-400">Failed to load report: ' + error.message + '</p>';
            }
          }
        })();
      `}} />
    </main>
  );
}
