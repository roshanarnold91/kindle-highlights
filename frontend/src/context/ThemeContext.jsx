import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext(null);

export const THEMES = ["light", "dark", "sepia", "midnight", "system"];
const DARK_FAMILY = new Set(["dark", "midnight"]);

function resolveTheme(theme) {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return theme;
}

function applyTheme(theme) {
  const resolved = resolveTheme(theme);
  document.documentElement.dataset.theme = resolved;
  document.documentElement.classList.toggle("dark", DARK_FAMILY.has(resolved));
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => localStorage.getItem("theme") || "system");

  useEffect(() => {
    applyTheme(theme);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = () => theme === "system" && applyTheme("system");
    mq.addEventListener("change", listener);
    return () => mq.removeEventListener("change", listener);
  }, [theme]);

  function setTheme(next) {
    setThemeState(next);
    localStorage.setItem("theme", next);
    applyTheme(next);
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
