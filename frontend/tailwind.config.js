const themedScale = (name) =>
  Object.fromEntries(
    [50, 100, 200, 300, 400, 500, 600, 700, 800, 900].map((shade) => [
      shade,
      `var(--${name}-${shade})`,
    ])
  );

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        white: "var(--color-white)",
        gray: themedScale("gray"),
        blue: themedScale("blue"),
      },
    },
  },
  plugins: [],
};
