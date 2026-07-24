import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const THEME_OPTIONS = [
  { value: "system", label: "System", swatch: "linear-gradient(135deg, #f9fafb 50%, #111827 50%)" },
  { value: "light", label: "Light", swatch: "#f9fafb" },
  { value: "dark", label: "Dark", swatch: "#111827" },
  { value: "sepia", label: "Sepia", swatch: "#f3ead9" },
  { value: "midnight", label: "Midnight", swatch: "#0b1120" },
];

export default function SettingsPage() {
  const { updateUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    api.get("/settings").then((data) => setSettings(data.user));
  }, []);

  function flash(setter, text) {
    setter(text);
    setTimeout(() => setter(""), 3000);
  }

  async function save(patch) {
    try {
      const data = await api.put("/settings", patch);
      setSettings(data.user);
      updateUser(data.user);
      flash(setMsg, "Saved");
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault();
    try {
      await api.post("/auth/change-password", { current_password: currentPassword, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      flash(setMsg, "Password updated");
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  async function handleTestEmail() {
    try {
      await api.post("/settings/test-email");
      flash(setMsg, "Test email sent");
    } catch (e) {
      flash(setErr, e.message);
    }
  }

  if (!settings) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-xl font-semibold">Settings</h1>

      {msg && <div className="mb-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-300">{msg}</div>}
      {err && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">{err}</div>}

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Profile</h2>
        <label className="mb-3 block text-sm">
          Display name
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
            defaultValue={settings.display_name}
            onBlur={(e) => save({ display_name: e.target.value })}
          />
        </label>

        <form onSubmit={handleChangePassword} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <input
            type="password"
            placeholder="Current password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 sm:col-span-2">
            Change password
          </button>
        </form>
      </section>

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Display preferences</h2>
        <label className="mb-3 block text-sm">
          Default location/page display
          <select
            defaultValue={settings.display_pref}
            onChange={(e) => save({ display_pref: e.target.value })}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          >
            <option value="location">Location only</option>
            <option value="page">Page only</option>
            <option value="both">Both</option>
            <option value="neither">Neither</option>
          </select>
        </label>
        <div className="text-sm">
          <p className="mb-2">Theme</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            {THEME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  setTheme(opt.value);
                  save({ theme: opt.value });
                }}
                className={`flex flex-col items-center gap-1.5 rounded-md border p-2 text-xs font-medium transition ${
                  theme === opt.value
                    ? "border-blue-600 ring-1 ring-blue-600"
                    : "border-gray-300 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-600"
                }`}
              >
                <span
                  className="h-8 w-full rounded border border-gray-300 dark:border-gray-600"
                  style={{ background: opt.swatch }}
                />
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Email (SMTP)</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <input
            placeholder="SMTP server (e.g. smtp.gmail.com)"
            defaultValue={settings.smtp_server}
            onBlur={(e) => save({ smtp_server: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <input
            placeholder="Port (e.g. 587)"
            type="number"
            defaultValue={settings.smtp_port}
            onBlur={(e) => save({ smtp_port: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <input
            placeholder="Email address"
            defaultValue={settings.smtp_email}
            onBlur={(e) => save({ smtp_email: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <input
            placeholder={settings.smtp_password_set ? "App password (saved — leave blank to keep)" : "App password"}
            type="password"
            onBlur={(e) => e.target.value && save({ smtp_password: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input
              type="checkbox"
              defaultChecked={settings.smtp_use_tls}
              onChange={(e) => save({ smtp_use_tls: e.target.checked })}
            />
            Use STARTTLS
          </label>
        </div>
        <button
          onClick={handleTestEmail}
          className="mt-3 rounded-md border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-700"
        >
          Send test email
        </button>
      </section>

      <section className="mb-8 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
        <h2 className="mb-3 font-semibold">Notifications</h2>
        <label className="mb-3 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            defaultChecked={settings.weekly_digest_enabled}
            onChange={(e) => save({ weekly_digest_enabled: e.target.checked })}
          />
          Weekly digest of new highlights
        </label>
        <div className="mb-3 grid grid-cols-2 gap-3">
          <select
            defaultValue={settings.weekly_digest_day}
            onChange={(e) => save({ weekly_digest_day: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          >
            {DAYS.map((d, i) => (
              <option key={d} value={i}>
                {d}
              </option>
            ))}
          </select>
          <input
            type="time"
            defaultValue={settings.weekly_digest_time}
            onBlur={(e) => save({ weekly_digest_time: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            defaultChecked={settings.copy_notification_enabled}
            onChange={(e) => save({ copy_notification_enabled: e.target.checked })}
          />
          Email me when I copy highlights
        </label>
      </section>
    </div>
  );
}
