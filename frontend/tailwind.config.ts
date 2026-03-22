import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],

  theme: {
    extend: {
      /* ЦВЕТА - используют CSS-переменные из variables.css */
      colors: {
        /* ─── Фоны ─── */
        "app-bg": "rgb(var(--color-bg) / <alpha-value>)",
        "app-surface": "rgb(var(--color-surface) / <alpha-value>)",
        "app-card": "rgb(var(--color-card) / <alpha-value>)",

        /* ─── Текст ─── */
        "app-text": "rgb(var(--color-text) / <alpha-value>)",
        "app-text-secondary":
          "rgb(var(--color-text-secondary) / <alpha-value>)",
        "app-text-inverse": "rgb(var(--color-text-inverse) / <alpha-value>)",

        /* ─── Границы ─── */
        "app-border": "rgb(var(--color-border) / <alpha-value>)",
        "app-border-strong": "rgb(var(--color-border-strong) / <alpha-value>)",
        "app-border-subtle": "rgb(var(--color-border-subtle) / <alpha-value>)",

        /* ─── Основные цвета (Primary) ─── */
        "app-primary": "rgb(var(--color-primary) / <alpha-value>)",
        "app-primary-hover": "rgb(var(--color-primary-hover) / <alpha-value>)",
        "app-primary-active":
          "rgb(var(--color-primary-active) / <alpha-value>)",
        "app-primary-subtle":
          "rgb(var(--color-primary-subtle) / <alpha-value>)",

        /* ─── Статусные цвета ─── */
        "app-success": "rgb(var(--color-success) / <alpha-value>)",
        "app-success-hover": "rgb(var(--color-success-hover) / <alpha-value>)",
        "app-success-subtle":
          "rgb(var(--color-success-subtle) / <alpha-value>)",

        "app-error": "rgb(var(--color-error) / <alpha-value>)",
        "app-error-hover": "rgb(var(--color-error-hover) / <alpha-value>)",
        "app-error-subtle": "rgb(var(--color-error-subtle) / <alpha-value>)",

        "app-warning": "rgb(var(--color-warning) / <alpha-value>)",
        "app-warning-hover": "rgb(var(--color-warning-hover) / <alpha-value>)",
        "app-warning-subtle":
          "rgb(var(--color-warning-subtle) / <alpha-value>)",

        "app-info": "rgb(var(--color-info) / <alpha-value>)",
        "app-info-hover": "rgb(var(--color-info-hover) / <alpha-value>)",
        "app-info-subtle": "rgb(var(--color-info-subtle) / <alpha-value>)",

        /* ─── Чат-сообщения ─── */
        "app-message-incoming":
          "rgb(var(--color-message-incoming) / <alpha-value>)",
        "app-message-outgoing":
          "rgb(var(--color-message-outgoing) / <alpha-value>)",
        "app-message-text-incoming":
          "rgb(var(--color-message-text-incoming) / <alpha-value>)",
        "app-message-text-outgoing":
          "rgb(var(--color-message-text-outgoing) / <alpha-value>)",
        "app-typing": "rgb(var(--color-typing) / <alpha-value>)",

        /* ─── Интерактивные элементы ─── */
        "app-focus-ring": "rgb(var(--color-focus-ring) / <alpha-value>)",
        "app-disabled": "rgb(var(--color-disabled) / <alpha-value>)",
        "app-disabled-text": "rgb(var(--color-disabled-text) / <alpha-value>)",

        /* ─── Аватары ─── */
        "app-avatar-1": "rgb(var(--color-avatar-1) / <alpha-value>)",
        "app-avatar-2": "rgb(var(--color-avatar-2) / <alpha-value>)",
        "app-avatar-3": "rgb(var(--color-avatar-3) / <alpha-value>)",
        "app-avatar-4": "rgb(var(--color-avatar-4) / <alpha-value>)",
        "app-avatar-5": "rgb(var(--color-avatar-5) / <alpha-value>)",
        "app-avatar-6": "rgb(var(--color-avatar-6) / <alpha-value>)",
      },

      /* ШРИФТЫ (системные, не требуют загрузки) */
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
          "Apple Color Emoji",
          "Segoe UI Emoji",
        ],

        mono: [
          "SF Mono",
          "Monaco",
          "Fira Code",
          "Menlo",
          "Courier New",
          "monospace",
        ],
      },

      /* РАЗМЕРЫ ШРИФТОВ */
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
      },

      /* ЭКРАНЫ (Breakpoints) */
      screens: {
        xs: "320px",
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1536px",
      },

      /* ОТСТУПЫ (Spacing) */
      spacing: {
        xs: "var(--spacing-xs)",
        sm: "var(--spacing-sm)",
        md: "var(--spacing-md)",
        lg: "var(--spacing-lg)",
        xl: "var(--spacing-xl)",
        "2xl": "var(--spacing-2xl)",
        "3xl": "var(--spacing-3xl)",
        gutter: "var(--gutter-mobile)",
      },

      /* BORDER RADIUS (Скругления) */
      borderRadius: {
        none: "0",
        sm: "var(--radius-sm)",
        base: "var(--radius-base)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "var(--radius-full)",
      },

      /* ТЕНИ (Box Shadows) */
      boxShadow: {
        xs: "var(--shadow-xs)",
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
        inset: "var(--shadow-inset)",
      },

      /* ПЕРЕХОДЫ И АНИМАЦИИ */
      transitionDuration: {
        fast: "var(--duration-fast)",
        normal: "var(--duration-normal)",
        slow: "var(--duration-slow)",
        slower: "var(--duration-slower)",
      },

      transitionTimingFunction: {
        in: "var(--ease-in)",
        out: "var(--ease-out)",
        "in-out": "var(--ease-in-out)",
        spring: "var(--ease-spring)",
      },

      /* АНИМАЦИИ */
      animation: {
        "slide-up": "slideUp 200ms ease-out",
        "slide-down": "slideDown 200ms ease-out",
        "fade-in": "fadeIn 200ms ease-out",
        "scale-in": "scaleIn 200ms ease-out",
        "bounce-in": "bounceIn 300ms cubic-bezier(0.34, 1.56, 0.64, 1)",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },

      keyframes: {
        slideUp: {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        slideDown: {
          from: { transform: "translateY(-10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        scaleIn: {
          from: { transform: "scale(0.95)", opacity: "0" },
          to: { transform: "scale(1)", opacity: "1" },
        },
        bounceIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "50%": { transform: "scale(1.05)" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: ".5" },
        },
      },

      /* Z-INDEX */
      zIndex: {
        hide: "-1",
        auto: "auto",
        base: "0",
        elevated: "10",
        sticky: "20",
        fixed: "30",
        dropdown: "1000",
        "modal-backdrop": "1040",
        modal: "1050",
        popover: "1060",
        tooltip: "1070",
        notification: "1080",
      },

      /* ВЫСОТА И ШИРИНА */
      width: {
        "screen-safe": "min(100vw, 100dvw)",
      },

      height: {
        sidebar: "calc(100vh - 64px)",
        "screen-safe": "min(100vh, 100dvh)",
      },

      /* МАКСИМАЛЬНАЯ ШИРИНА */
      maxWidth: {
        container: "1200px",
        "chat-message": "85%",
      },

      /* OPACITY */
      opacity: {
        0: "0",
        5: "0.05",
        10: "0.1",
        20: "0.2",
        30: "0.3",
        40: "0.4",
        50: "0.5",
        60: "0.6",
        70: "0.7",
        80: "0.8",
        90: "0.9",
        100: "1",
      },

      /* RING (Focus rings) */
      ringColor: {
        DEFAULT: "rgb(var(--color-primary))",
        "app-focus": "rgb(var(--color-focus-ring))",
      },

      ringWidth: {
        DEFAULT: "2px",
        0: "0px",
        1: "1px",
        2: "2px",
        4: "4px",
      },
    },
  },

  plugins: [],

  darkMode: ["class", '[data-theme="dark"]'],

  corePlugins: {
    preflight: true,
  },

  important: false,

  future: {
    respectDefaultRingColorOpacity: true,
  },
};

export default config;
