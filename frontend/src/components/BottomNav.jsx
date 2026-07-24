import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const items = [
  { to: "/", label: "Library", icon: "📚" },
  { to: "/upload", label: "Upload", icon: "⬆️" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function BottomNav() {
  const { user } = useAuth();
  const links = user?.is_admin ? [...items, { to: "/admin", label: "Admin", icon: "🛠️" }] : items;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-20 border-t border-gray-200 bg-white/95 backdrop-blur dark:border-gray-800 dark:bg-gray-900/95 md:hidden">
      <div className="flex justify-around">
        {links.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex min-w-[64px] flex-col items-center gap-0.5 py-2 text-xs ${
                isActive ? "text-blue-600 dark:text-blue-400" : "text-gray-500 dark:text-gray-400"
              }`
            }
          >
            <span className="text-xl leading-none">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
