import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import BottomNav from "./BottomNav";

const links = [
  { to: "/", label: "Library" },
  { to: "/upload", label: "Upload" },
  { to: "/settings", label: "Settings" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navLinks = user?.is_admin ? [...links, { to: "/admin", label: "Admin" }] : links;

  return (
    <div className="min-h-screen bg-gray-50 pb-16 text-gray-900 dark:bg-gray-900 dark:text-gray-100 md:pb-0">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur dark:border-gray-800 dark:bg-gray-900/95">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="text-lg font-semibold">📖 Kindle Highlights</span>
          <nav className="hidden items-center gap-4 md:flex">
            {navLinks.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                className={({ isActive }) =>
                  `text-sm font-medium ${
                    isActive ? "text-blue-600 dark:text-blue-400" : "text-gray-600 dark:text-gray-300"
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
            <span className="text-sm text-gray-400">{user?.display_name || user?.username}</span>
            <button
              onClick={logout}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
            >
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
      <BottomNav />
    </div>
  );
}
