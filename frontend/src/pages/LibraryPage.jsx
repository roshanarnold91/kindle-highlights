import { useEffect, useState } from "react";
import { api } from "../api/client";
import BookCard from "../components/BookCard";

export default function LibraryPage() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("recent");
  const [status, setStatus] = useState("all");

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ search, sort, status });
    api
      .get(`/books?${params.toString()}`)
      .then((data) => setBooks(data.books))
      .finally(() => setLoading(false));
  }, [search, sort, status]);

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Your Library</h1>
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
            <BookCard key={b.id} book={b} />
          ))}
        </div>
      )}
    </div>
  );
}
