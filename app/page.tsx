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
          <h1 className="text-5xl font-bold mb-2">The Alfred Report</h1>
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

        {/* Table of Contents */}
        {report && report.sections && (
          <nav className="mb-12 bg-slate-800/30 border border-slate-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-200 mb-3">Contents</h2>
            <ul className="grid grid-cols-1 gap-2 text-sm">
              {Object.entries(report.sections)
                .filter(([key]) => key !== 'company_reddit_watch')
                .map(([key, section]: [string, any]) => (
                <li key={key}>
                  <a href={`#section-${key}`} className="text-cyan-400 hover:text-cyan-300">
                    → {section.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}

        {error ? (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 text-red-200">
            {error}
          </div>
        ) : !report ? (
          <div className="text-gray-400">Report not available</div>
        ) : (
          <div className="space-y-8">
            {/* AI Reddit Trending + Company Watch (nested) */}
            {report.sections?.ai_reddit_trending && (
              <>
                <section id="section-ai_reddit_trending" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                  <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.ai_reddit_trending.title}
                  </h2>
                  {report.sections.ai_reddit_trending.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.ai_reddit_trending.summary}
                    </p>
                  )}
                  {report.sections.ai_reddit_trending.items && report.sections.ai_reddit_trending.items.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.ai_reddit_trending.items.map((item: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                          <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-orange-400 hover:text-orange-300 mb-2 block hover:underline">
                            {item.title}
                          </a>
                          <div className="flex gap-3 flex-wrap items-center">
                            <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{item.subreddit}</span>
                            {item.matched_terms && item.matched_terms.length > 0 && (
                              <div className="flex gap-1">
                                {item.matched_terms.slice(0, 3).map((term: string) => (
                                  <span key={term} className="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded">
                                    {term}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                {/* Company Reddit Watch nested under AI Reddit */}
                {report.sections?.company_reddit_watch && (
                  <section className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 ml-4">
                    <h3 className="text-2xl font-bold mb-3 text-purple-400">
                      {report.sections.company_reddit_watch.title}
                    </h3>
                    {report.sections.company_reddit_watch.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.company_reddit_watch.summary}
                      </p>
                    )}
                    <div className="space-y-6">
                      {report.sections.company_reddit_watch.companies?.map((company: any) => (
                        <div key={company.company_name} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                          <h4 className="font-semibold text-gray-100 mb-2">
                            {company.company_name}
                            {company.ticker && <span className="text-gray-500 ml-2">({company.ticker})</span>}
                          </h4>
                          {company.items && company.items.length > 0 ? (
                            <div className="space-y-3">
                              {company.items.map((item: any, idx: number) => (
                                <div key={idx} className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:text-orange-300 hover:underline text-sm font-medium block mb-2">
                                    {item.title}
                                  </a>
                                  <div className="flex gap-2 flex-wrap text-xs">
                                    {item.subreddit && <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded">{item.subreddit}</span>}
                                    {item.matched_terms?.slice(0, 2).map((term: string) => (
                                      <span key={term} className="bg-blue-900 text-blue-200 px-2 py-1 rounded">{term}</span>
                                    ))}
                                    {item.topics?.slice(0, 2).map((topic: string) => (
                                      <span key={topic} className="bg-purple-900 text-purple-200 px-2 py-1 rounded">{topic}</span>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-gray-500 text-sm">No posts found today</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </>
            )}

            {/* Company Reddit Watch (special nested structure) -- OLD FALLBACK, REMOVE LATER */}
            {report.sections?.company_reddit_watch && !report.sections?.ai_reddit_trending && (
              <section id="section-company_reddit_watch" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                  {report.sections.company_reddit_watch.title}
                </h2>
                {report.sections.company_reddit_watch.summary && (
                  <p className="text-gray-300 mb-6 leading-relaxed">
                    {report.sections.company_reddit_watch.summary}
                  </p>
                )}
                <div className="space-y-6">
                  {report.sections.company_reddit_watch.companies?.map((company: any) => (
                    <div key={company.company_name} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                      <h3 className="font-semibold text-gray-100 mb-2">
                        {company.company_name}
                        {company.ticker && <span className="text-gray-500 ml-2">({company.ticker})</span>}
                      </h3>
                      {company.items && company.items.length > 0 ? (
                        <div className="space-y-3">
                          {company.items.map((item: any, idx: number) => (
                            <div key={idx} className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                              <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:text-orange-300 hover:underline text-sm font-medium block mb-2">
                                {item.title}
                              </a>
                              <div className="flex gap-2 flex-wrap text-xs">
                                {item.subreddit && <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded">{item.subreddit}</span>}
                                {item.matched_terms?.slice(0, 2).map((term: string) => (
                                  <span key={term} className="bg-blue-900 text-blue-200 px-2 py-1 rounded">{term}</span>
                                ))}
                                {item.topics?.slice(0, 2).map((topic: string) => (
                                  <span key={topic} className="bg-purple-900 text-purple-200 px-2 py-1 rounded">{topic}</span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">No posts found today</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* All other sections */}
            {Object.entries(report.sections || {})
              .filter(([key]) => !['company_reddit_watch', 'ai_reddit_trending'].includes(key))
              .map(([key, section]: [string, any]) => (
              <section key={key} id={`section-${key}`} className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
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
                        {/* Weather items */}
                        {item.name && item.temperature && (
                          <>
                            <h3 className="font-semibold text-gray-100 mb-2">
                              {item.name}
                            </h3>
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
                            {item.details && (
                              <p className="text-gray-400 text-sm">
                                {item.details}
                              </p>
                            )}
                          </>
                        )}

                        {/* Todoist items */}
                        {item.content && !item.title && (
                          <div>
                            <p className={`mb-2 ${item.completed ? 'line-through text-gray-500' : 'text-gray-300'}`}>
                              {item.completed && '✓ '}
                              {item.content}
                            </p>
                            {!item.completed && (item.due || item.overdue) && (
                              <div className="flex gap-4 text-xs text-gray-500">
                                {item.due && <span>Due: {item.due}</span>}
                                {item.overdue && <span className="text-red-400 font-semibold">OVERDUE</span>}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Kanban items */}
                        {item.status && (
                          <>
                            <div className="flex items-center gap-3 mb-3">
                              <span className={`font-semibold text-sm px-3 py-1 rounded ${
                                item.status === 'In progress' ? 'bg-blue-900/50 text-blue-200' :
                                item.status === 'Ready' ? 'bg-purple-900/50 text-purple-200' :
                                item.status === 'Backlog' ? 'bg-gray-700 text-gray-100' :
                                item.status === 'Done' ? 'bg-green-900/50 text-green-200' :
                                'bg-yellow-900/50 text-yellow-200'
                              }`}>
                                {item.status}
                              </span>
                              <span className="text-gray-400 text-sm">{item.count} card{item.count !== 1 ? 's' : ''}</span>
                            </div>
                            {item.cards && item.cards.length > 0 && (
                              <div className="space-y-2">
                                {item.cards.map((card: string, cardIdx: number) => (
                                  <div key={cardIdx} className="text-sm text-gray-400 pl-4 border-l border-gray-600">
                                    {card}
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        )}

                        {/* AI News items */}
                        {item.title && item.source && (
                          <>
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-cyan-300 hover:text-cyan-200 mb-2 block hover:underline">
                              {item.title}
                            </a>
                            {item.why_it_matters && (
                              <p className="text-gray-400 text-sm mb-2">
                                {item.why_it_matters}
                              </p>
                            )}
                            {item.tags && item.tags.length > 0 && (
                              <div className="flex gap-2 mb-2">
                                {item.tags.map((tag: string) => (
                                  <span key={tag} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>{item.source}</span>
                              {item.published_at && <span>{item.published_at.split('T')[0]}</span>}
                            </div>
                          </>
                        )}

                        {/* YouTube items */}
                        {item.title && item.channel && (
                          <>
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-red-400 hover:text-red-300 mb-2 block hover:underline">
                              {item.title}
                            </a>
                            <div className="text-sm text-gray-500">
                              <span>{item.channel}</span>
                              {item.published_at && <span className="ml-4">{item.published_at.split('T')[0]}</span>}
                            </div>
                          </>
                        )}

                        {/* Reddit AI Trending items */}
                        {item.title && item.subreddit && (
                          <>
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-orange-400 hover:text-orange-300 mb-2 block hover:underline">
                              {item.title}
                            </a>
                            <div className="flex gap-3 flex-wrap items-center">
                              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{item.subreddit}</span>
                              {item.matched_terms && item.matched_terms.length > 0 && (
                                <div className="flex gap-1">
                                  {item.matched_terms.slice(0, 3).map((term: string) => (
                                    <span key={term} className="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded">
                                      {term}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </>
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
