function fallbackCopyPlainText(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  document.body.removeChild(textarea);
  return ok;
}

/**
 * Copies the result of `dataPromise` (expected to resolve to { text, html? })
 * to the clipboard. Must be called synchronously from a user-gesture handler
 * (e.g. directly inside an onClick), with NO `await` beforehand — browsers
 * (notably Firefox) revoke clipboard-write permission the instant control
 * yields to an awaited call, so `navigator.clipboard.write()` has to be
 * invoked immediately. Passing lazy Blob promises (rather than an already-
 * awaited value) lets the underlying network request still happen async
 * without losing that permission window.
 */
export async function copyFromPromise(dataPromise) {
  if (navigator.clipboard?.write && window.ClipboardItem) {
    try {
      const item = new ClipboardItem({
        "text/plain": dataPromise.then((d) => new Blob([d.text], { type: "text/plain" })),
        "text/html": dataPromise.then((d) => new Blob([d.html || d.text], { type: "text/html" })),
      });
      await navigator.clipboard.write([item]);
      return { ok: true, data: await dataPromise };
    } catch {
      // fall through to plain-text paths below
    }
  }

  let data;
  try {
    data = await dataPromise;
  } catch (err) {
    return { ok: false, data: null, error: err };
  }

  try {
    await navigator.clipboard.writeText(data.text);
    return { ok: true, data };
  } catch {
    return { ok: fallbackCopyPlainText(data.text), data };
  }
}
