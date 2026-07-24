import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import HighlightCard from "../components/HighlightCard";
import { copyText } from "../utils/clipboard";

const PREF_OPTIONS = [
  { value: "", label: "Use my default" },
  { value: "location", label: "Location only" },
  { value: "page", label: "Page only" },
  { value: "both", label: "Both" },
  { value: "neither", label: "Neither" },
];

export default function BookDetailPage() {
  const { bookId } = useParams();
  const [book, setBook] = useState(null);
  const [highlights, setHighlights] = useState([]);
  const [displayPref, setDisplayPref] = useState("both");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");

  const [type, setType] = useState("");
  const [copied, setCopied] = useState("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (type) params.set("type", type);
    if (copied) params.set("copied", copied);
    if (search) params.set("search", search);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);

    setLoading(true);
    api
      .get(`/books/${bookId}/highlights?${params.toString()}`)
      .then((data) => {
        setBook(data.book);
        setHighlights(data.highlights);
        setDisplayPref(data.display_pref);
      })
      .finally(() => setLoading(false));
  }, [bookId, type, copied, search, dateFrom, dateTo]);

  useEffect(() => {
    load();
  }, [load]);

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 2500);
  }

  async function handleCopyBook(mode) {
    const data = await api.post(`/books/${bookId}/copy`, { mode });
    const ok = await copyText(data.text);
    showToast(ok ? `Copied ${data.count} highlight(s) to clipboard` : "Copy failed");
    load();
  }

  async function handleCopyHighlight(highlight) {
    const data = await api.post(`/highlights/${highlight.id}/copy`);
    const ok = await copyText(data.text);
    showToast(ok ? "Copied to clipboard" : "Copy failed");
    load();
  }

  async function handlePrefOverride(e) {
    const value = e.target.value || null;
    await api.patch(`/books/${bookId}`, { display_pref_override: value });
    load();
  }

  async function handleEmailBook() {
    try {
      await api.post(`/settings/email/book/${bookId}`);
      showToast("Email sent");
    } catch (err) {
      showToast(err.message);
    }
  }

  if (loading && !book) return <p className="text-gray-400">Loading…</p>;
  if (!book) return null;

  return (
    <div>
      <Link to="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
        ← Back to library
      </Link>

      <div className="mt-3 mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <h1 className="text-2xl font-semibold">{book.title}</h1>
          <p className="text-gray-500 dark:text-gray-400">{book.author}</p>
          <p className="mt-1 text-sm text-gray-400">
            {book.total_count} entries · {book.copied_count} copied
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleCopyBook("all")}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Copy all
          </button>
          <button
            onClick={() => handleCopyBook("new")}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            Copy new only
          </button>
          <button
            onClick={handleEmailBook}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            Email me
          </button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
        <input
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="col-span-2 rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 md:col-span-2"
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <option value="">All types</option>
          <option value="highlight">Highlights</option>
          <option value="note">Notes</option>
          <option value="bookmark">Bookmarks</option>
        </select>
        <select
          value={copied}
          onChange={(e) => setCopied(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <option value="">Copied + uncopied</option>
          <option value="true">Copied only</option>
          <option value="false">Uncopied only</option>
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        />
      </div>

      <div className="mb-6">
        <label className="text-sm text-gray-500 dark:text-gray-400">
          Display preference for this book:{" "}
          <select
            defaultValue={book.display_pref_override || ""}
            onChange={handlePrefOverride}
            className="ml-2 rounded-md border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-gray-800"
          >
            {PREF_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex flex-col gap-3">
        {highlights.length === 0 ? (
          <p className="text-gray-400">No entries match your filters.</p>
        ) : (
          highlights.map((h) => (
            <HighlightCard key={h.id} highlight={h} displayPref={displayPref} onCopy={handleCopyHighlight} />
          ))
        )}
      </div>

      {toast && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 rounded-md bg-gray-900 px-4 py-2 text-sm text-white shadow-lg dark:bg-gray-100 dark:text-gray-900 md:bottom-6">
          {toast}
        </div>
      )}
    </div>
  );
}
