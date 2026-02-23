import fs from 'fs';
import path from 'path';

export default async function Home() {
  let report = null;
  let error = null;

  try {
    const filePath = path.join(process.cwd(), 'public', 'alfred-report', 'latest.json');
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    report = JSON.parse(fileContent);
  } catch (e: any) {
    error = `Failed to read report: ${e.message}`;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-5xl font-bold mb-2">
            The Alfred Report
          </h1>
          {report && (
            <p className="text-gray-400 text-lg">
              {new Date(report.report_date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          )}
        </header>

        {error ? (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-red-200">
            {error}
          </div>
        ) : !report ? (
          <div className="text-gray-400">Report not available</div>
        ) : (
          <div className="space-y-8">
            {/* Render each section */}
            {Object.entries(report.sections || {}).map(([key, section]: [string, any]) => (
              <section key={key} className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                  {section.title}
                </h2>
                
                {section.summary && (
                  <p className="text-gray-300 mb-6 leading-relaxed">
                    {section.summary}
                  </p>
                )}

                {section.items && section.items.length > 0 && (
                  <div className="space-y-4">
                    {section.items.map((item: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                        {item.name && (
                          <h3 className="font-semibold text-gray-100 mb-2">
                            {item.name}
                          </h3>
                        )}
                        
                        {/* Weather-specific fields */}
                        {item.temperature && (
                          <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                            <div>
                              <span className="text-gray-400">Temp:</span>
                              <span className="ml-2 font-mono">{item.temperature}</span>
                            </div>
                            {item.forecast && (
                              <div>
                                <span className="text-gray-400">Forecast:</span>
                                <span className="ml-2">{item.forecast}</span>
                              </div>
                            )}
                            {item.wind && (
                              <div>
                                <span className="text-gray-400">Wind:</span>
                                <span className="ml-2">{item.wind}</span>
                              </div>
                            )}
                            {item.precipitation_chance && (
                              <div>
                                <span className="text-gray-400">Precip:</span>
                                <span className="ml-2">{item.precipitation_chance}</span>
                              </div>
                            )}
                          </div>
                        )}

                        {item.details && (
                          <p className="text-gray-400 text-sm">
                            {item.details}
                          </p>
                        )}

                        {/* Todoist-specific fields */}
                        {item.content && (
                          <div>
                            <p className="text-gray-300 mb-2">
                              {item.content}
                            </p>
                            {(item.due || item.overdue) && (
                              <div className="flex gap-4 text-xs text-gray-500">
                                {item.due && <span>Due: {item.due}</span>}
                                {item.overdue && <span className="text-red-400 font-semibold">OVERDUE</span>}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Generic fields */}
                        {!item.temperature && !item.content && item.summary && (
                          <p className="text-gray-400 text-sm">
                            {item.summary}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            ))}
          </div>
        )}

        <footer className="mt-12 pt-8 border-t border-slate-700 text-center text-gray-500 text-sm">
          <p>Generated at {report?.generated_at}</p>
        </footer>
      </div>
    </main>
  );
}
