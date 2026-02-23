import fs from 'fs';
import path from 'path';

export default async function Home() {
  let report = null;
  let error = null;

  try {
    // Read the latest JSON file at build/render time
    const filePath = path.join(process.cwd(), 'public', 'alfred-report', 'latest.json');
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    report = JSON.parse(fileContent);
  } catch (e: any) {
    error = `Failed to read report: ${e.message}`;
  }

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <h1 className="text-4xl font-bold mb-6">
        The Alfred Report
      </h1>

      {error ? (
        <p className="text-red-400 mb-4">{error}</p>
      ) : !report ? (
        <p className="text-gray-400 mb-4">Report not available</p>
      ) : (
        <>
          <p className="text-gray-400 mb-4">
            {report.report_date} • {report.timezone}
          </p>
          <pre className="bg-zinc-900 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(report, null, 2)}
          </pre>
        </>
      )}
    </main>
  );
}
