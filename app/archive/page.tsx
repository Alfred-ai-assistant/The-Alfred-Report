import fs from 'fs';
import path from 'path';

export default async function Archive() {
  let index = null;
  let error = null;

  try {
    const indexPath = path.join(process.cwd(), 'public', 'alfred-report', 'index.json');
    const fileContent = fs.readFileSync(indexPath, 'utf-8');
    index = JSON.parse(fileContent);
  } catch (e: any) {
    error = `Failed to load archive index: ${e.message}`;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-black text-white p-8">
      <div className="max-w-2xl mx-auto">
        <header className="mb-12">
          <a href="/" className="text-cyan-400 hover:text-cyan-300 text-sm">
            ← Back to Latest Report
          </a>
          <h1 className="text-5xl font-bold mb-2 mt-4">Historical Reports</h1>
          <p className="text-gray-400 text-lg">
            Browse past editions of The Alfred Report
          </p>
        </header>

        {error ? (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-red-200">
            {error}
          </div>
        ) : !index || !index.reports || index.reports.length === 0 ? (
          <div className="text-gray-400">No historical reports available</div>
        ) : (
          <div className="space-y-3">
            {index.reports.map((report: any) => {
              const dateObj = new Date(report.date);
              const formattedDate = dateObj.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              });

              return (
                <a
                  key={report.date}
                  href={`/?date=${report.date}`}
                  className="block bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:bg-slate-800/80 hover:border-slate-600 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-cyan-400 mb-1">
                        {formattedDate}
                      </h2>
                      <p className="text-gray-400 text-sm">
                        Generated at 07:00 EST
                      </p>
                    </div>
                    <div className="text-gray-500">
                      <span className="text-xl">→</span>
                    </div>
                  </div>
                </a>
              );
            })}
          </div>
        )}

        <footer className="mt-16 pt-8 border-t border-slate-700 text-center text-gray-500 text-sm">
          <p>The Alfred Report Archives</p>
        </footer>
      </div>
    </main>
  );
}
