import { useEffect, useState } from "react";
import { api } from "../api/client";

function bytesToHuman(n) {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB"];
  let val = n;
  let i = -1;
  do {
    val /= 1024;
    i++;
  } while (val >= 1024 && i < units.length - 1);
  return `${val.toFixed(1)} ${units[i]}`;
}

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [usage, setUsage] = useState([]);
  const [logs, setLogs] = useState([]);
  const [smtp, setSmtp] = useState(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newIsAdmin, setNewIsAdmin] = useState(false);

  function refresh() {
    api.get("/admin/users").then((d) => setUsers(d.users));
    api.get("/admin/storage").then((d) => setUsage(d.usage));
    api.get("/admin/import-logs").then((d) => setLogs(d.logs));
    api.get("/admin/smtp").then((d) => setSmtp(d.smtp));
  }

  useEffect(refresh, []);

  function flash(setter, text) {
    setter(text);
    setTimeout(() => setter(""), 3000);
  }

  async function handleCreateUser(e) {
    e.preventDefault();
    try {
      await api.post("/admin/users", { username: newUsername, password: newPassword, is_admin: newIsAdmin });
      setNewUsername("");
      setNewPassword("");
      setNewIsAdmin(false);
      flash(setMsg, "User created");
      refresh();
    } catch (e2) {
      flash(setErr, e2.message);
    }
  }

  async function toggleDisabled(user) {
    try {
      await api.patch(`/admin/users/${user.id}`, { disabled: !user.disabled });
      refresh();
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  async function resetPassword(user) {
    const pw = prompt(`New password for ${user.username} (min 8 chars):`);
    if (!pw) return;
    try {
      await api.patch(`/admin/users/${user.id}`, { new_password: pw });
      flash(setMsg, "Password reset");
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  async function deleteUser(user) {
    if (!confirm(`Permanently delete ${user.username} and all their data?`)) return;
    try {
      await api.del(`/admin/users/${user.id}`);
      flash(setMsg, "User deleted");
      refresh();
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  async function saveSmtp(patch) {
    try {
      await api.put("/admin/smtp", patch);
      flash(setMsg, "Saved");
      api.get("/admin/smtp").then((d) => setSmtp(d.smtp));
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold">Admin Panel</h1>

      {msg && <div className="mb-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-300">{msg}</div>}
      {err && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">{err}</div>}

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Users</h2>
        <form onSubmit={handleCreateUser} className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-4">
          <input
            placeholder="Username"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <input
            placeholder="Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={newIsAdmin} onChange={(e) => setNewIsAdmin(e.target.checked)} />
            Admin
          </label>
          <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700">
            Create user
          </button>
        </form>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              <tr>
                <th className="px-3 py-2">Username</th>
                <th className="px-3 py-2">Admin</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100 dark:border-gray-800">
                  <td className="px-3 py-2">{u.username}</td>
                  <td className="px-3 py-2">{u.is_admin ? "Yes" : "No"}</td>
                  <td className="px-3 py-2">{u.disabled ? "Disabled" : "Active"}</td>
                  <td className="flex flex-wrap gap-2 px-3 py-2">
                    <button onClick={() => toggleDisabled(u)} className="text-blue-600 hover:underline dark:text-blue-400">
                      {u.disabled ? "Enable" : "Disable"}
                    </button>
                    <button onClick={() => resetPassword(u)} className="text-blue-600 hover:underline dark:text-blue-400">
                      Reset password
                    </button>
                    <button onClick={() => deleteUser(u)} className="text-red-600 hover:underline dark:text-red-400">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Storage usage</h2>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            <tr>
              <th className="px-3 py-2">User</th>
              <th className="px-3 py-2">Books</th>
              <th className="px-3 py-2">Highlights</th>
              <th className="px-3 py-2">Upload storage</th>
            </tr>
          </thead>
          <tbody>
            {usage.map((u) => (
              <tr key={u.user_id} className="border-t border-gray-100 dark:border-gray-800">
                <td className="px-3 py-2">{u.username}</td>
                <td className="px-3 py-2">{u.book_count}</td>
                <td className="px-3 py-2">{u.highlight_count}</td>
                <td className="px-3 py-2">{bytesToHuman(u.upload_bytes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {smtp && (
        <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <h2 className="mb-3 font-semibold">App-wide SMTP fallback</h2>
          <p className="mb-3 text-xs text-gray-400">Used for users who haven't configured their own SMTP settings.</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <input
              placeholder="SMTP server"
              defaultValue={smtp.server}
              onBlur={(e) => saveSmtp({ server: e.target.value })}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
            <input
              placeholder="Port"
              type="number"
              defaultValue={smtp.port}
              onBlur={(e) => saveSmtp({ port: e.target.value })}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
            <input
              placeholder="Email"
              defaultValue={smtp.email}
              onBlur={(e) => saveSmtp({ email: e.target.value })}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
            <input
              placeholder={smtp.password_set ? "Password (saved — leave blank to keep)" : "Password"}
              type="password"
              onBlur={(e) => e.target.value && saveSmtp({ password: e.target.value })}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
            />
            <label className="block text-xs text-gray-500 dark:text-gray-400 sm:col-span-2">
              Encryption
              <select
                defaultValue={smtp.use_ssl ? "ssl" : smtp.use_tls ? "starttls" : "none"}
                onChange={(e) => {
                  const v = e.target.value;
                  saveSmtp({ use_ssl: v === "ssl", use_tls: v === "starttls" });
                }}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
              >
                <option value="starttls">STARTTLS (usually port 587)</option>
                <option value="ssl">SSL/TLS (usually port 465)</option>
                <option value="none">None</option>
              </select>
            </label>
          </div>
        </section>
      )}

      <section className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Import logs (all users)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              <tr>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">File</th>
                <th className="px-3 py-2">Imported</th>
                <th className="px-3 py-2">Duplicates</th>
                <th className="px-3 py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-t border-gray-100 dark:border-gray-800">
                  <td className="px-3 py-2">{l.username}</td>
                  <td className="px-3 py-2">{l.filename}</td>
                  <td className="px-3 py-2">{l.imported_count}</td>
                  <td className="px-3 py-2">{l.duplicate_count}</td>
                  <td className="px-3 py-2">{new Date(l.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
