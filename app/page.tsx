import fs from 'fs';
import path from 'path';

interface PageProps {
  searchParams?: {
    date?: string;
  };
}

export default async function Home({ searchParams }: PageProps) {
  let report = null;
  let error = null;
  let viewDate = searchParams?.date || null;

  try {
    let filePath: string = path.join(process.cwd(), 'public', 'alfred-report', 'latest.json');
    
    if (viewDate) {
      // Validate date format YYYY-MM-DD
      if (!/^\d{4}-\d{2}-\d{2}$/.test(viewDate)) {
        error = 'Invalid date format. Use YYYY-MM-DD.';
      } else {
        filePath = path.join(process.cwd(), 'public', 'alfred-report', 'daily', `${viewDate}.json`);
      }
    }

    if (filePath && !error) {
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      report = JSON.parse(fileContent);
    }
  } catch (e: any) {
    error = `Failed to read report: ${e.message}`;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-black text-white p-4 md:p-8">
      {/* Widen container for larger screens */}
      <div className="max-w-full mx-4 md:mx-8">
        <header className="mb-8 md:mb-12">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl md:text-5xl font-bold">The Alfred Report</h1>
            <a href="/archive" className="text-cyan-400 hover:text-cyan-300 text-sm font-medium">
              View Archives →
            </a>
          </div>
          {report && (
            <p className="text-gray-400 text-lg">
              {new Date(report.report_date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
              {viewDate && viewDate !== report.report_date && ' (archived)'}
            </p>
          )}
        </header>

        {/* Table of Contents - hidden on iMac (xl) */}
        {report && report.sections && (
          <nav className="mb-8 md:mb-12 bg-slate-800/30 border border-slate-700 rounded-lg p-6 xl:hidden">
            <h2 className="text-lg font-semibold text-gray-200 mb-3">Contents</h2>
            <ul className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2 text-sm">
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
          /* 
           * Layout strategy:
           * - Mobile/iPad: grid with col-start/row-start for positioning
           * - iMac (xl): flexbox with 3 independent columns that stack vertically without gaps
           */
          <>
            {/* iMac Layout (xl): 3 independent flex columns */}
            <div className="hidden xl:flex xl:gap-8 xl:items-start">
              {/* LEFT COLUMN */}
              <div className="flex-1 flex flex-col gap-0">
                {report.sections?.ai_news && (
                  <section id="section-ai_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.ai_news.title}
                    </h2>
                    {report.sections.ai_news.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.ai_news.summary}
                      </p>
                    )}
                    {report.sections.ai_news.items && report.sections.ai_news.items.length > 0 && (
                      <div className="space-y-4">
                        {report.sections.ai_news.items.map((item: any, idx: number) => (
                          <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-cyan-300 hover:text-cyan-200 mb-2 block hover:underline">
                              {item.title}
                            </a>
                            {item.why_it_matters && (
                              <p className="text-gray-400 text-sm mb-2">
                                {item.why_it_matters}
                              </p>
                            )}
                            {item.tags && item.tags.length > 0 && (
                              <div className="flex gap-2 mb-2 flex-wrap">
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
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}

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
                                  <div className="flex gap-1 flex-wrap">
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

                    {report.sections?.company_reddit_watch && (
                      <section className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
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
              </div>

              {/* MIDDLE COLUMN */}
              <div className="flex-1 flex flex-col gap-0">
                {report.sections?.youtube && (
                  <section id="section-youtube" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.youtube.title}
                    </h2>
                    {report.sections.youtube.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.youtube.summary}
                      </p>
                    )}
                    {report.sections.youtube.items && report.sections.youtube.items.length > 0 && (
                      <div className="grid grid-cols-2 gap-4">
                        {report.sections.youtube.items.map((item: any, idx: number) => (
                          <a
                            key={idx}
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group block bg-slate-900/60 rounded-lg overflow-hidden border border-slate-700/50 hover:border-red-500/60 transition-all duration-200 hover:shadow-lg hover:shadow-red-900/20"
                          >
                            <div className="relative aspect-video bg-black overflow-hidden">
                              {item.thumbnail ? (
                                <img
                                  src={item.thumbnail}
                                  alt={item.title}
                                  className="w-full h-full object-cover group-hover:opacity-80 transition-opacity duration-200"
                                />
                              ) : (
                                <div className="w-full h-full bg-slate-800 flex items-center justify-center">
                                  <span className="text-gray-600 text-sm">No thumbnail</span>
                                </div>
                              )}
                              <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center shadow-xl opacity-85 group-hover:opacity-100 group-hover:scale-110 transition-all duration-200">
                                  <svg className="w-5 h-5 text-white ml-1" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M8 5v14l11-7z"/>
                                  </svg>
                                </div>
                              </div>
                            </div>
                            <div className="p-3">
                              <p className="font-semibold text-gray-100 text-sm leading-snug mb-2 line-clamp-2 group-hover:text-red-300 transition-colors duration-200">
                                {item.title}
                              </p>
                              <div className="flex items-center justify-between text-xs text-gray-500">
                                <span className="truncate mr-2">{item.channel}</span>
                                {item.published_at && (
                                  <span className="shrink-0">{item.published_at.split('T')[0]}</span>
                                )}
                              </div>
                            </div>
                          </a>
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {report.sections?.portfolio_news && (
                  <section id="section-portfolio_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.portfolio_news.title}
                    </h2>
                    {report.sections.portfolio_news.tickers && report.sections.portfolio_news.tickers.length > 0 && (
                      <div className="space-y-6">
                        {report.sections.portfolio_news.tickers.map((ticker: any, tidx: number) => (
                          <div key={tidx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                            <h3 className="font-bold text-green-400 mb-3">
                              {ticker.symbol}
                            </h3>
                            {ticker.top_stories && ticker.top_stories.length > 0 && (
                              <div className="space-y-3 mb-3">
                                {ticker.top_stories.map((story: any, sidx: number) => (
                                  <div key={sidx} className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                                    <a href={story.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-cyan-300 hover:text-cyan-200 mb-2 block hover:underline">
                                      [{story.score.toFixed(1)}] {story.headline}
                                    </a>
                                    {story.tags && story.tags.length > 0 && (
                                      <div className="flex gap-2 mb-2 flex-wrap">
                                        {story.tags.map((tag: string) => (
                                          <span key={tag} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                                            {tag}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                    <p className="text-gray-400 text-xs">
                                      {story.why_ranked} • {story.source}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                            {ticker.glance && ticker.glance.length > 0 && (
                              <div className="bg-slate-700/30 rounded p-3 border border-slate-700/50 text-sm">
                                <p className="text-gray-400 font-semibold mb-2">Worth a glance:</p>
                                <div className="space-y-1">
                                  {ticker.glance.map((item: any, gidx: number) => (
                                    <p key={gidx} className="text-gray-400 text-xs">
                                      [{item.score.toFixed(1)}] {item.headline}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {report.sections?.watchlist_news && (
                  <section id="section-watchlist_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.watchlist_news.title}
                    </h2>
                    {report.sections.watchlist_news.tickers && report.sections.watchlist_news.tickers.length > 0 && (
                      <div className="space-y-6">
                        {report.sections.watchlist_news.tickers.map((ticker: any, tidx: number) => (
                          <div key={tidx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                            <h3 className="font-bold text-green-400 mb-3">
                              {ticker.symbol}
                            </h3>
                            {ticker.top_stories && ticker.top_stories.length > 0 && (
                              <div className="space-y-3 mb-3">
                                {ticker.top_stories.map((story: any, sidx: number) => (
                                  <div key={sidx} className="bg-slate-800/50 rounded p-3 border border-slate-700/50">
                                    <a href={story.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-cyan-300 hover:text-cyan-200 mb-2 block hover:underline">
                                      [{story.score.toFixed(1)}] {story.headline}
                                    </a>
                                    {story.tags && story.tags.length > 0 && (
                                      <div className="flex gap-2 mb-2 flex-wrap">
                                        {story.tags.map((tag: string) => (
                                          <span key={tag} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                                            {tag}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                    <p className="text-gray-400 text-xs">
                                      {story.why_ranked} • {story.source}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                            {ticker.glance && ticker.glance.length > 0 && (
                              <div className="bg-slate-700/30 rounded p-3 border border-slate-700/50 text-sm">
                                <p className="text-gray-400 font-semibold mb-2">Worth a glance:</p>
                                <div className="space-y-1">
                                  {ticker.glance.map((item: any, gidx: number) => (
                                    <p key={gidx} className="text-gray-400 text-xs">
                                      [{item.score.toFixed(1)}] {item.headline}
                                    </p>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}
              </div>

              {/* RIGHT COLUMN */}
              <div className="flex-1 flex flex-col gap-0">
                {report.sections?.weather && (
                  <section id="section-weather" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.weather.title}
                    </h2>
                    {report.sections.weather.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.weather.summary}
                      </p>
                    )}
                    {report.sections.weather.items && report.sections.weather.items.length > 0 && (
                      <div className="space-y-4">
                        {report.sections.weather.items.map((item: any, idx: number) => (
                          <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
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
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {report.sections?.todoist && (
                  <section id="section-todoist" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.todoist.title}
                    </h2>
                    {report.sections.todoist.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.todoist.summary}
                      </p>
                    )}
                    {report.sections.todoist.items && report.sections.todoist.items.length > 0 && (
                      <div className="space-y-4">
                        {report.sections.todoist.items.map((item: any, idx: number) => (
                          <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
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
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {report.sections?.kanban && (
                  <section id="section-kanban" className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <h2 className="text-3xl font-bold mb-3 text-cyan-400">
                      {report.sections.kanban.title}
                    </h2>
                    {report.sections.kanban.summary && (
                      <p className="text-gray-300 mb-6 leading-relaxed">
                        {report.sections.kanban.summary}
                      </p>
                    )}
                    {report.sections.kanban.items && report.sections.kanban.items.length > 0 && (
                      <div className="space-y-4">
                        {report.sections.kanban.items.map((item: any, idx: number) => (
                          <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
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
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                )}
              </div>
            </div>

            {/* Mobile/Tablet Layout (md and below): Original grid layout */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 items-start xl:hidden">

              {/* Weather */}
              {report.sections?.weather && (
                <section id="section-weather" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-2 md:row-start-1">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.weather.title}
                  </h2>
                  {report.sections.weather.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.weather.summary}
                    </p>
                  )}
                  {report.sections.weather.items && report.sections.weather.items.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.weather.items.map((item: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                          <h3 className="font-semibold text-gray-100 mb-2">{item.name}</h3>
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
                            <p className="text-gray-400 text-sm">{item.details}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* Todoist */}
              {report.sections?.todoist && (
                <section id="section-todoist" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-2 md:row-start-2">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.todoist.title}
                  </h2>
                  {report.sections.todoist.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.todoist.summary}
                    </p>
                  )}
                  {report.sections.todoist.items && report.sections.todoist.items.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.todoist.items.map((item: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
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
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* Kanban */}
              {report.sections?.kanban && (
                <section id="section-kanban" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-1">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.kanban.title}
                  </h2>
                  {report.sections.kanban.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.kanban.summary}
                    </p>
                  )}
                  {report.sections.kanban.items && report.sections.kanban.items.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.kanban.items.map((item: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
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
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* AI News */}
              {report.sections?.ai_news && (
                <section id="section-ai_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-2">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.ai_news.title}
                  </h2>
                  {report.sections.ai_news.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.ai_news.summary}
                    </p>
                  )}
                  {report.sections.ai_news.items && report.sections.ai_news.items.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.ai_news.items.map((item: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/50 rounded p-4 border border-slate-700/50">
                          <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-cyan-300 hover:text-cyan-200 mb-2 block hover:underline">
                            {item.title}
                          </a>
                          {item.why_it_matters && (
                            <p className="text-gray-400 text-sm mb-2">
                              {item.why_it_matters}
                            </p>
                          )}
                          {item.tags && item.tags.length > 0 && (
                            <div className="flex gap-2 mb-2 flex-wrap">
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
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* YouTube */}
              {report.sections?.youtube && (
                <section id="section-youtube" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-3">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.youtube.title}
                  </h2>
                  {report.sections.youtube.summary && (
                    <p className="text-gray-300 mb-6 leading-relaxed">
                      {report.sections.youtube.summary}
                    </p>
                  )}
                  {report.sections.youtube.items && report.sections.youtube.items.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {report.sections.youtube.items.map((item: any, idx: number) => (
                        <a
                          key={idx}
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group block bg-slate-900/60 rounded-lg overflow-hidden border border-slate-700/50 hover:border-red-500/60 transition-all duration-200 hover:shadow-lg hover:shadow-red-900/20"
                        >
                          <div className="relative aspect-video bg-black overflow-hidden">
                            {item.thumbnail ? (
                              <img
                                src={item.thumbnail}
                                alt={item.title}
                                className="w-full h-full object-cover group-hover:opacity-80 transition-opacity duration-200"
                              />
                            ) : (
                              <div className="w-full h-full bg-slate-800 flex items-center justify-center">
                                <span className="text-gray-600 text-sm">No thumbnail</span>
                              </div>
                            )}
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center shadow-xl opacity-85 group-hover:opacity-100 group-hover:scale-110 transition-all duration-200">
                                <svg className="w-5 h-5 text-white ml-1" viewBox="0 0 24 24" fill="currentColor">
                                  <path d="M8 5v14l11-7z"/>
                                </svg>
                              </div>
                            </div>
                          </div>
                          <div className="p-3">
                            <p className="font-semibold text-gray-100 text-sm leading-snug mb-2 line-clamp-2 group-hover:text-red-300 transition-colors duration-200">
                              {item.title}
                            </p>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span className="truncate mr-2">{item.channel}</span>
                              {item.published_at && (
                                <span className="shrink-0">{item.published_at.split('T')[0]}</span>
                              )}
                            </div>
                          </div>
                        </a>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* Reddit */}
              {report.sections?.ai_reddit_trending && (
                <div className="md:col-start-1 md:row-start-4 space-y-6">
                  <section id="section-ai_reddit_trending" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8">
                    <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
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
                                <div className="flex gap-1 flex-wrap">
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

                  {report.sections?.company_reddit_watch && (
                    <section className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 ml-0 md:ml-4">
                      <h3 className="text-xl md:text-2xl font-bold mb-3 text-purple-400">
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
                </div>
              )}

              {report.sections?.company_reddit_watch && !report.sections?.ai_reddit_trending && (
                <section id="section-company_reddit_watch" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-4">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
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

              {/* Portfolio News */}
              {report.sections?.portfolio_news && (
                <section id="section-portfolio_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-5">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.portfolio_news.title}
                  </h2>
                  {report.sections.portfolio_news.tickers && report.sections.portfolio_news.tickers.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.portfolio_news.tickers.map((ticker: any, tidx: number) => (
                        <div key={tidx} className="bg-slate-900/50 rounded p-3 border border-slate-700/50">
                          <h3 className="font-bold text-green-400 mb-2 text-sm">
                            {ticker.symbol}
                          </h3>
                          {ticker.top_stories && ticker.top_stories.length > 0 && (
                            <div className="space-y-2 mb-2">
                              {ticker.top_stories.slice(0, 2).map((story: any, sidx: number) => (
                                <div key={sidx} className="text-xs">
                                  <a href={story.url} target="_blank" rel="noopener noreferrer" className="text-cyan-300 hover:text-cyan-200 hover:underline block mb-1">
                                    [{story.score.toFixed(1)}] {story.headline}
                                  </a>
                                  <p className="text-gray-500 text-xs">{story.why_ranked}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {/* Watchlist News */}
              {report.sections?.watchlist_news && (
                <section id="section-watchlist_news" className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 md:p-8 md:col-start-1 md:row-start-6">
                  <h2 className="text-2xl md:text-3xl font-bold mb-3 text-cyan-400">
                    {report.sections.watchlist_news.title}
                  </h2>
                  {report.sections.watchlist_news.tickers && report.sections.watchlist_news.tickers.length > 0 && (
                    <div className="space-y-4">
                      {report.sections.watchlist_news.tickers.map((ticker: any, tidx: number) => (
                        <div key={tidx} className="bg-slate-900/50 rounded p-3 border border-slate-700/50">
                          <h3 className="font-bold text-green-400 mb-2 text-sm">
                            {ticker.symbol}
                          </h3>
                          {ticker.top_stories && ticker.top_stories.length > 0 && (
                            <div className="space-y-2 mb-2">
                              {ticker.top_stories.slice(0, 2).map((story: any, sidx: number) => (
                                <div key={sidx} className="text-xs">
                                  <a href={story.url} target="_blank" rel="noopener noreferrer" className="text-cyan-300 hover:text-cyan-200 hover:underline block mb-1">
                                    [{story.score.toFixed(1)}] {story.headline}
                                  </a>
                                  <p className="text-gray-500 text-xs">{story.why_ranked}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}
            </div>
          </>
        )}

        <footer className="mt-12 pt-8 border-t border-slate-700 text-center text-gray-500 text-sm">
          <p>Generated at {report?.generated_at}</p>
        </footer>
      </div>
    </main>
  );
}
