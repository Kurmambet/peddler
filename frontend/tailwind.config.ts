import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        // ==========================================
        // Backgrounds (Telegram Dark)
        // ==========================================
        "bg-primary": "#0a0e27", // Main background (very dark)
        "bg-secondary": "#1a1f3a", // Secondary background (slightly lighter)
        "bg-tertiary": "#242d47", // Tertiary (inputs, cards, modals)
        "bg-hover": "#2d3758", // Hover state for interactive elements

        // ==========================================
        // Messages
        // ==========================================
        "msg-own": "#0084ff", // Own message (Telegram blue)
        "msg-other": "#262d3d", // Other's message background
        "msg-own-text": "#ffffff", // Own message text
        "msg-other-text": "#ffffff", // Other's message text

        // ==========================================
        // Text Colors
        // ==========================================
        "text-primary": "#ffffff", // Primary text
        "text-secondary": "#a0a7b8", // Secondary text (timestamps, subtitles)
        "text-tertiary": "#8a91a8", // Tertiary text (more muted)
        "text-muted": "#6a7184", // Very muted

        // ==========================================
        // Accent Colors
        // ==========================================
        "accent-blue": "#0084ff", // Primary action (Telegram blue)
        "accent-blue-hover": "#0073e6",
        "accent-blue-active": "#0066cc",
        "accent-green": "#31a24c", // Success
        "accent-red": "#ff4757", // Destructive/Error
        "accent-yellow": "#ffa502", // Warning
        "accent-gray": "#5a5f7a", // Secondary actions

        // ==========================================
        // Borders
        // ==========================================
        "border-light": "#3a4158", // Light border
        "border-dark": "#262d3d", // Dark border
        "border-subtle": "#1a1f3a", // Subtle border

        // ==========================================
        // Status
        // ==========================================
        "status-online": "#31a24c", // Online indicator
        "status-away": "#ffa502", // Away indicator
        "status-offline": "#5a5f7a", // Offline indicator
        "status-unread": "#0084ff", // Unread badge
      },

      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["Fira Code", "monospace"],
      },

      fontSize: {
        xs: ["12px", { lineHeight: "16px", fontWeight: "400" }], // Timestamps
        sm: ["13px", { lineHeight: "18px", fontWeight: "400" }], // Secondary text
        base: ["15px", { lineHeight: "20px", fontWeight: "400" }], // Chat text
        lg: ["17px", { lineHeight: "22px", fontWeight: "400" }], // Headers
        xl: ["19px", { lineHeight: "24px", fontWeight: "500" }], // Main titles
        "2xl": ["24px", { lineHeight: "32px", fontWeight: "600" }], // Page titles
      },

      spacing: {
        0: "0",
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        5: "20px",
        6: "24px",
        8: "32px",
        10: "40px",
        12: "48px",
      },

      borderRadius: {
        none: "0",
        sm: "6px",
        base: "8px",
        md: "12px",
        lg: "16px",
        full: "9999px",
      },

      boxShadow: {
        xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        sm: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      },

      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
        slow: "350ms",
      },

      screens: {
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
      },
    },
  },
  plugins: [],
} satisfies Config;
