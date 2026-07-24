const typeIcons = { highlight: "🖍️", note: "📝", bookmark: "🔖" };

function formatDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function HighlightCard({ highlight, displayPref, onCopy }) {
  const showPage = displayPref === "page" || displayPref === "both";
  const showLocation = displayPref === "location" || displayPref === "both";

  const metaBits = [];
  if (showPage && highlight.page) metaBits.push(`Page ${highlight.page}`);
  if (showLocation && highlight.location) metaBits.push(`Location ${highlight.location}`);
  const dateStr = formatDate(highlight.date_added);
  if (dateStr) metaBits.push(dateStr);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-800">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {typeIcons[highlight.type]} {highlight.type}
        </span>
        {highlight.copied_at && (
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
            Copied
          </span>
        )}
      </div>

      {highlight.text && <p className="whitespace-pre-wrap text-sm">{highlight.text}</p>}
      {highlight.note && (
        <p className="mt-2 whitespace-pre-wrap rounded-md bg-amber-50 p-2 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
          {highlight.note}
        </p>
      )}

      <div className="mt-3 flex items-center justify-between gap-2">
        <span className="text-xs text-gray-400">{metaBits.join(" · ")}</span>
        <button
          onClick={() => onCopy(highlight)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-700"
        >
          Copy
        </button>
      </div>
    </div>
  );
}
