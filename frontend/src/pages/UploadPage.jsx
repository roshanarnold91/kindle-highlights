import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

export default function UploadPage() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState([]);
  const inputRef = useRef(null);

  function loadLogs() {
    api.get("/import/logs").then((data) => setLogs(data.logs));
  }

  useEffect(() => {
    loadLogs();
  }, []);

  async function uploadFile(file) {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const data = await api.post("/import", form);
      setResult(data.log);
      loadLogs();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    uploadFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold">Upload Clippings</h1>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition ${
          dragging
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
        }`}
      >
        <span className="text-4xl">📄</span>
        <p className="mt-3 font-medium">Drop your "My Clippings.txt" here</p>
        <p className="mt-1 text-sm text-gray-400">or tap to choose a file</p>
        <input
          ref={inputRef}
          type="file"
          accept=".txt"
          className="hidden"
          onChange={(e) => uploadFile(e.target.files?.[0])}
        />
      </div>

      {uploading && <p className="mt-4 text-gray-400">Importing…</p>}

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-300">
          Imported {result.imported_count} new entries across {result.book_count} book(s).{" "}
          {result.duplicate_count} duplicate(s) skipped.
        </div>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Import History</h2>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            <tr>
              <th className="px-3 py-2">File</th>
              <th className="px-3 py-2">Imported</th>
              <th className="px-3 py-2">Duplicates</th>
              <th className="px-3 py-2">Books</th>
              <th className="px-3 py-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-t border-gray-100 dark:border-gray-800">
                <td className="px-3 py-2">{l.filename}</td>
                <td className="px-3 py-2">{l.imported_count}</td>
                <td className="px-3 py-2">{l.duplicate_count}</td>
                <td className="px-3 py-2">{l.book_count}</td>
                <td className="px-3 py-2">{new Date(l.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-gray-400">
                  No imports yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
