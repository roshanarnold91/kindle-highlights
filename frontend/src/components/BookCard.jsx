import { Link } from "react-router-dom";

const statusStyles = {
  none: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  partial: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  full: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
};

const statusLabels = { none: "Never copied", partial: "Partially copied", full: "Fully copied" };

export default function BookCard({ book }) {
  return (
    <Link
      to={`/books/${book.id}`}
      className="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition hover:shadow-md dark:border-gray-800 dark:bg-gray-800"
    >
      <div className="flex aspect-[2/3] items-center justify-center bg-gray-100 dark:bg-gray-800">
        {book.cover_url ? (
          <img src={book.cover_url} alt={book.title} className="h-full w-full object-cover" />
        ) : (
          <span className="p-4 text-center text-3xl">📕</span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <h3 className="line-clamp-2 text-sm font-semibold">{book.title}</h3>
        <p className="line-clamp-1 text-xs text-gray-500 dark:text-gray-400">{book.author || "Unknown author"}</p>
        <div className="mt-1 flex flex-wrap items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
          <span>{book.highlight_count} highlights</span>
          {book.note_count > 0 && <span>· {book.note_count} notes</span>}
        </div>
        <span
          className={`mt-2 inline-block w-fit rounded-full px-2 py-0.5 text-[11px] font-medium ${statusStyles[book.copy_status]}`}
        >
          {statusLabels[book.copy_status]}
        </span>
      </div>
    </Link>
  );
}
