/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Ink — primary text and dark surfaces (deep teal-slate, not pure black)
        ink: {
          DEFAULT: "#16202A",
          900: "#0F1720",
          800: "#16202A",
          700: "#22303C",
          600: "#33475A",
        },
        // Slate — secondary text, muted UI
        slate: {
          500: "#5A6B7B",
          400: "#8595A3",
          300: "#AEBAC5",
        },
        // Paper / surfaces — cool, crisp (deliberately not warm cream)
        paper: "#F6F8FA",
        surface: "#FFFFFF",
        line: "#E3E7EC",
        // Brand — archival teal (reading-room patina), used with restraint
        brand: {
          DEFAULT: "#1B6E63",
          700: "#155A51",
          600: "#1B6E63",
          500: "#238A7C",
          50: "#E8F2F0",
        },
        // Status semantics for document badges
        status: {
          uploaded: "#5A6B7B",
          processing: "#B4771F",
          ready: "#1B6E63",
          failed: "#B4322A",
        },
      },
      fontFamily: {
        serif: ['"IBM Plex Serif"', "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.04em" }],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 23, 32, 0.04), 0 1px 3px rgba(16, 23, 32, 0.06)",
        panel: "0 8px 24px rgba(16, 23, 32, 0.10)",
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};
