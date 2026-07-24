import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import HighlightCard from "../components/HighlightCard";
import MetadataMatchModal from "../components/MetadataMatchModal";
import { copyFromPromise } from "../utils/clipboard";

const PREF_OPTIONS = [
  { value: "", label: "Use my default" },
  { value: "location", label: "Location only" },
  { value: "page", label: "Page only" },
  { value: "both", label: "Both" },
  { value: "neither", label: "Neither" },
];

const TYPE_OPTIONS = [
  { value: "highlight", label: "Highlights" },
  { value: "note", label: "Notes" },
  { value: "bookmark", label: "Bookmarks" },
];

export default function BookDetailPage() {
  const { bookId } = useParams();
  const [book, setBook] = useState(null);
  const [highlights, setHighlights] = useState([]);
  const [displayPref, setDisplayPref] = useState("both");
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [showAbout, setShowAbout] = useState(false);

  const [selectedTypes, setSelectedTypes] = useState([]);
  const [copied, setCopied] = useState("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const buildFilterParams = useCallback(() => {
    const params = new URLSearchParams();
    selectedTypes.forEach((t) => params.append("type", t));
    if (copied) params.set("copied", copied);
    if (search) params.set("search", search);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    return params;
  }, [selectedTypes, copied, search, dateFrom, dateTo]);

  const load = useCallback(() => {
    setLoading(true);
    api
      .get(`/books/${bookId}/highlights?${buildFilterParams().toString()}`)
      .then((data) => {
        setBook(data.book);
        setHighlights(data.highlights);
        setDisplayPref(data.display_pref);
      })
      .finally(() => setLoading(false));
  }, [bookId, buildFilterParams]);

  function toggleType(value) {
    setSelectedTypes((prev) =>
      prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]
    );
  }

  function handleExport() {
    window.location.href = `/api/books/${bookId}/export?${buildFilterParams().toString()}`;
  }

  useEffect(() => {
    load();
  }, [load]);

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 2500);
  }

  async function handleCopyBook(mode) {
    const dataPromise = api.post(`/books/${bookId}/copy`, { mode, types: selectedTypes });
    const { ok, data } = await copyFromPromise(dataPromise);
    showToast(ok && data ? `Copied ${data.count} highlight(s) to clipboard` : "Copy failed");
    load();
  }

  async function handleResetCopied() {
    if (!window.confirm(`Mark all ${book.total_count} entries in this book as not copied?`)) return;
    await api.post(`/books/${bookId}/copy/reset`);
    showToast("Copied status reset");
    load();
  }

  async function handleCopyHighlight(highlight) {
    const dataPromise = api.post(`/highlights/${highlight.id}/copy`);
    const { ok, data } = await copyFromPromise(dataPromise);
    showToast(ok && data ? "Copied to clipboard" : "Copy failed");
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
          {(book.description || book.publisher || book.published_date) && (
            <div className="mt-2">
              <button
                onClick={() => setShowAbout((v) => !v)}
                className="text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                {showAbout ? "Hide" : "About this book"}
              </button>
              {showAbout && (
                <div className="mt-1 max-w-lg text-sm text-gray-600 dark:text-gray-300">
                  {book.description && <p className="mb-1">{book.description}</p>}
                  <p className="text-xs text-gray-400">
                    {[book.publisher, book.published_date].filter(Boolean).join(" · ")}
                  </p>
                </div>
              )}
            </div>
          )}
          <button
            onClick={() => setShowMetadataModal(true)}
            className="mt-2 text-xs font-medium text-blue-600 hover:underline dark:text-blue-400"
          >
            Edit cover / metadata
          </button>
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
          <button
            onClick={handleExport}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
          >
            Export
          </button>
          <button
            onClick={handleResetCopied}
            className="rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
          >
            Reset copied status
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
        <div className="col-span-2 flex flex-wrap items-center gap-1 sm:col-span-1">
          {TYPE_OPTIONS.map((opt) => {
            const active = selectedTypes.includes(opt.value);
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => toggleType(opt.value)}
                className={`rounded-full border px-2.5 py-1 text-xs font-medium transition ${
                  active
                    ? "border-blue-600 bg-blue-600 text-white"
                    : "border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
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

      {showMetadataModal && (
        <MetadataMatchModal
          book={book}
          onClose={() => setShowMetadataModal(false)}
          onMatched={(updatedBook) => {
            setBook(updatedBook);
            showToast("Book metadata updated");
          }}
        />
      )}
    </div>
  );
}
