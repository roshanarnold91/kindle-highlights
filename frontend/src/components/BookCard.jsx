import { Link } from "react-router-dom";

const statusStyles = {
  none: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  partial: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  full: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
};

const statusLabels = { none: "Never copied", partial: "Partially copied", full: "Fully copied" };

function CardBody({ book }) {
  return (
    <>
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
    </>
  );
}

export default function BookCard({ book, selectMode, selected, onToggle }) {
  if (selectMode) {
    return (
      <button
        type="button"
        onClick={() => onToggle(book.id)}
        className={`relative flex flex-col overflow-hidden rounded-lg border-2 bg-white text-left shadow-sm transition hover:shadow-md dark:bg-gray-800 ${
          selected
            ? "border-blue-600 ring-2 ring-blue-300 dark:ring-blue-700"
            : "border-gray-200 dark:border-gray-800"
        }`}
      >
        <span
          className={`absolute right-2 top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full border text-xs font-bold ${
            selected
              ? "border-blue-600 bg-blue-600 text-white"
              : "border-gray-300 bg-white/90 text-transparent dark:border-gray-600 dark:bg-gray-900/80"
          }`}
        >
          ✓
        </span>
        <CardBody book={book} />
      </button>
    );
  }

  return (
    <Link
      to={`/books/${book.id}`}
      className="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition hover:shadow-md dark:border-gray-800 dark:bg-gray-800"
    >
      <CardBody book={book} />
    </Link>
  );
}
