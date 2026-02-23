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
      <script>
        {`
          (function() {
            try {
              const url = new URL('/alfred-report/latest.json', window.location.origin).href;
              console.log('Fetching:', url);
              document.getElementById('status').textContent = 'Fetching from: ' + url;
              
              fetch(url)
                .then(r => {
                  console.log('Response:', r.status, r.statusText);
                  document.getElementById('status').textContent = 'Got response: ' + r.status;
                  if (!r.ok) throw new Error('HTTP ' + r.status);
                  return r.json();
                })
                .then(data => {
                  console.log('Data loaded:', data.report_date);
                  document.getElementById('status').textContent = 'Report for ' + data.report_date;
                  document.getElementById('report').classList.remove('hidden');
                  document.getElementById('json-output').textContent = JSON.stringify(data, null, 2);
                })
                .catch(err => {
                  console.error('Fetch error:', err);
                  document.getElementById('status').textContent = 'Error: ' + (err.message || 'unknown') + ' (' + err.name + ')';
                });
            } catch (e) {
              console.error('Script error:', e);
              document.getElementById('status').textContent = 'Script error: ' + e.message;
            }
          })();
        `}
      </script>
    </>
  );
}
