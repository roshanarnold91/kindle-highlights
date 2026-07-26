import { useEffect, useState } from "react";
import { api } from "../api/client";
import BookCard from "../components/BookCard";
import SendEmailModal from "../components/SendEmailModal";

export default function LibraryPage() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("recent");
  const [status, setStatus] = useState("all");

  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [exporting, setExporting] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ search, sort, status });
    api
      .get(`/books?${params.toString()}`)
      .then((data) => setBooks(data.books))
      .finally(() => setLoading(false));
  }, [search, sort, status]);

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 3500);
  }

  function toggleSelectMode() {
    setSelectMode((v) => !v);
    setSelectedIds(new Set());
  }

  function toggleBook(id) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleBulkExport() {
    setExporting(true);
    try {
      const res = await fetch("/api/books/export-bulk", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ book_ids: Array.from(selectedIds) }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error((data && data.error) || "Export failed");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `highlights-export-${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast(`Exported ${selectedIds.size} book(s) as PDFs`);
    } catch (err) {
      showToast(err.message);
    } finally {
      setExporting(false);
    }
  }

  async function handleBulkEmail({ to, subject }) {
    const result = await api.post("/settings/email/bulk", {
      book_ids: Array.from(selectedIds),
      to,
      subject,
    });
    const sentCount = result.sent.length;
    const failedCount = result.failed.length;
    showToast(
      failedCount
        ? `Sent ${sentCount} email(s), ${failedCount} failed`
        : `Sent ${sentCount} email(s)`
    );
    toggleSelectMode();
  }

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Your Library</h1>
        <button
          onClick={toggleSelectMode}
          className={`w-fit rounded-md border px-3 py-2 text-sm font-medium ${
            selectMode
              ? "border-blue-600 bg-blue-600 text-white"
              : "border-gray-300 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
          }`}
        >
          {selectMode ? "Cancel selection" : "Select books"}
        </button>
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <input
          placeholder="Search by title or author…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <option value="recent">Recently highlighted</option>
          <option value="title">Title A-Z</option>
          <option value="author">Author</option>
          <option value="most_highlights">Most highlights</option>
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <option value="all">All books</option>
          <option value="never_copied">Never copied</option>
          <option value="partially_copied">Partially copied</option>
          <option value="fully_copied">Fully copied</option>
        </select>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : books.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-10 text-center text-gray-400 dark:border-gray-700">
          No books yet. Upload your <em>My Clippings.txt</em> to get started.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {books.map((b) => (
            <BookCard
              key={b.id}
              book={b}
              selectMode={selectMode}
              selected={selectedIds.has(b.id)}
              onToggle={toggleBook}
            />
          ))}
        </div>
      )}

      {selectMode && selectedIds.size > 0 && (
        <div className="fixed bottom-20 left-1/2 flex -translate-x-1/2 items-center gap-3 rounded-full border border-gray-200 bg-white px-4 py-2 shadow-lg dark:border-gray-700 dark:bg-gray-800 md:bottom-6">
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <button
            onClick={handleBulkExport}
            disabled={exporting}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {exporting ? "Exporting…" : "Export as PDFs"}
          </button>
          <button
            onClick={() => setShowEmailModal(true)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-700"
          >
            Email each
          </button>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-36 left-1/2 -translate-x-1/2 rounded-md bg-gray-900 px-4 py-2 text-sm text-white shadow-lg dark:bg-gray-100 dark:text-gray-900 md:bottom-20">
          {toast}
        </div>
      )}

      {showEmailModal && (
        <SendEmailModal
          defaultSubject="Highlights: {title}"
          subjectHint="Use {title} to insert each book's title — one email is sent per selected book."
          submitLabel={`Send ${selectedIds.size} email(s)`}
          sendingLabel="Sending…"
          onClose={() => setShowEmailModal(false)}
          onSend={handleBulkEmail}
        />
      )}
    </div>
  );
}
