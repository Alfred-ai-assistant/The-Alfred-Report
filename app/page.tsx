export default function Home() {
  return (
    <>
      <main className="min-h-screen bg-black text-white p-10">
        <h1 className="text-4xl font-bold mb-6">
          The Alfred Report
        </h1>
        <p className="text-gray-400 mb-4" id="status">
          Loading report...
        </p>
        <div id="report" className="hidden">
          <pre id="json-output" className="bg-zinc-900 p-4 rounded text-sm overflow-x-auto"></pre>
        </div>
      </main>
      
      {/* Client-side JSON loader */}
      <script async>
        {`
          fetch('/alfred-report/latest.json')
            .then(r => r.json())
            .then(data => {
              document.getElementById('status').textContent = 'Report for ' + data.report_date;
              document.getElementById('report').classList.remove('hidden');
              document.getElementById('json-output').textContent = JSON.stringify(data, null, 2);
            })
            .catch(err => {
              document.getElementById('status').textContent = 'Failed to load: ' + err.message;
            });
        `}
      </script>
    </>
  );
}
