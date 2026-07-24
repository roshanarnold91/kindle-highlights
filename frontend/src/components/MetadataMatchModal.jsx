import { useState } from "react";
import { api } from "../api/client";

const SOURCE_LABELS = { google: "Google Books", openlibrary: "Open Library" };

export default function MetadataMatchModal({ book, onClose, onMatched }) {
  const [query, setQuery] = useState(`${book.title} ${book.author || ""}`.trim());
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(e) {
    e.preventDefault();
    setSearching(true);
    setError("");
    try {
      const data = await api.get(`/books/${book.id}/metadata-search?q=${encodeURIComponent(query)}`);
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }

  async function handlePick(candidate) {
    const updated = await api.post(`/books/${book.id}/metadata-match`, candidate);
    onMatched(updated.book);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-5 shadow-xl dark:bg-gray-800">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Match book metadata</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSearch} className="mb-4 flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
            placeholder="Search by title/author…"
          />
          <button
            type="submit"
            disabled={searching}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </form>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {results.map((r, i) => (
            <button
              key={`${r.source}-${r.source_id}-${i}`}
              onClick={() => handlePick(r)}
              className="flex flex-col overflow-hidden rounded-md border border-gray-200 text-left hover:border-blue-500 dark:border-gray-700"
            >
              <div className="flex aspect-[2/3] items-center justify-center bg-gray-100 dark:bg-gray-900">
                {r.cover_url ? (
                  <img src={r.cover_url} alt={r.title} className="h-full w-full object-cover" />
                ) : (
                  <span className="text-2xl">📕</span>
                )}
              </div>
              <div className="p-2">
                <p className="line-clamp-2 text-xs font-medium text-gray-900 dark:text-gray-100">{r.title}</p>
                <p className="line-clamp-1 text-[11px] text-gray-500 dark:text-gray-400">{r.author}</p>
                <span className="mt-1 inline-block rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500 dark:bg-gray-700 dark:text-gray-300">
                  {SOURCE_LABELS[r.source] || r.source}
                </span>
              </div>
            </button>
          ))}
        </div>

        {!searching && results.length === 0 && (
          <p className="text-sm text-gray-400">Search above to find the right cover and details.</p>
        )}
      </div>
    </div>
  );
}
