import type { UmsPublicSettings } from "@/lib/ums-settings"

function getFontFamilyString(font: string) {
  switch (font.toLowerCase()) {
    case "inter":
      return '"Inter", "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
    case "roboto":
      return '"Roboto", "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
    case "outfit":
      return '"Outfit", "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
    case "arial":
      return 'Arial, "Helvetica Neue", Helvetica, sans-serif'
    case "helvetica":
      return 'Helvetica, "Helvetica Neue", Arial, sans-serif'
    default:
      return '"Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
  }
}

function fontWeightValue(weight: string) {
  switch (weight) {
    case "normal":
      return "400"
    case "medium":
      return "500"
    case "semibold":
      return "600"
    default:
      return "500"
  }
}

function shadowValue(shadow: string) {
  switch (shadow) {
    case "none":
      return "none"
    case "light":
      return "0 1px 2px 0 rgba(0,0,0,0.03), 0 1px 6px -1px rgba(0,0,0,0.02), 0 1px 3px 0 rgba(0,0,0,0.04)"
    case "default":
      return "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06), 0 1px 2px 0 rgba(0,0,0,0.04)"
    case "strong":
      return "0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05), 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)"
    default:
      return "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06), 0 1px 2px 0 rgba(0,0,0,0.04)"
  }
}

function avatarRadiusValue(shape: string) {
  switch (shape) {
    case "circle":
      return "9999px"
    case "rounded":
      return "0.5rem"
    case "square":
      return "0"
    default:
      return "9999px"
  }
}

function avatarSizeValue(size: string) {
  switch (size) {
    case "sm":
      return "1.5rem"
    case "md":
      return "2rem"
    case "lg":
      return "2.5rem"
    default:
      return "2rem"
  }
}

export function UmsStyleInject({ settings }: { settings: UmsPublicSettings }) {
  const ui = settings.uiCustomization

  const customCss = `
    /* ── Light mode overrides ── */
    :root {
      ${ui.button_color ? `--primary: ${ui.button_color};` : ""}
      ${ui.button_text_color ? `--primary-foreground: ${ui.button_text_color};` : ""}
      ${ui.secondary_button_color ? `--secondary: ${ui.secondary_button_color};` : ""}
      ${ui.secondary_button_text_color ? `--secondary-foreground: ${ui.secondary_button_text_color};` : ""}
      ${ui.button_border_radius ? `--radius: ${ui.button_border_radius};` : ""}
      ${ui.primary_text_color ? `--foreground: ${ui.primary_text_color};` : ""}
      ${ui.background_color ? `--background: ${ui.background_color};` : ""}
      ${ui.icon_size ? `--ums-icon-size: ${ui.icon_size};` : ""}
      ${ui.icon_color ? `--ums-icon-color: ${ui.icon_color};` : ""}
      ${ui.sidebar_font_size ? `--ums-sidebar-font-size: ${ui.sidebar_font_size};` : ""}
      ${ui.sidebar_font_weight ? `--ums-sidebar-font-weight: ${fontWeightValue(ui.sidebar_font_weight)};` : ""}
      ${ui.sidebar_icon_size ? `--ums-sidebar-icon-size: ${ui.sidebar_icon_size};` : ""}
      ${ui.sidebar_width ? `--ums-sidebar-width: ${ui.sidebar_width};` : ""}
      ${ui.card_border_radius ? `--ums-card-border-radius: ${ui.card_border_radius};` : ""}
      ${ui.card_shadow ? `--ums-card-shadow: ${shadowValue(ui.card_shadow)};` : ""}
      ${ui.avatar_shape ? `--ums-avatar-border-radius: ${avatarRadiusValue(ui.avatar_shape)};` : ""}
      ${ui.avatar_size ? `--ums-avatar-size: ${avatarSizeValue(ui.avatar_size)};` : ""}
      --radius-xl: var(--ums-card-border-radius, 0.75rem);
      --card: ${ui.card_background_color || "oklch(1 0 0)"};
    }

    /* ── Dark mode overrides ── */
    .dark {
      --primary: ${ui.dark_button_color || "#fafafa"};
      --primary-foreground: ${ui.dark_button_text_color || "#18181b"};
      --secondary: ${ui.dark_secondary_button_color || "#27272a"};
      --secondary-foreground: ${ui.dark_secondary_button_text_color || "#fafafa"};
      --foreground: ${ui.dark_primary_text_color || "#fafafa"};
      --background: ${ui.dark_background_color || "#09090b"};
      --card: ${ui.dark_background_color || "#09090b"};
      ${ui.dark_accent_color ? `--accent: ${ui.dark_accent_color};` : ""}
      ${ui.dark_icon_color ? `--ums-icon-color: ${ui.dark_icon_color};` : ""}
    }

    /* ── Body font ── */
    body {
      ${ui.font_family ? `font-family: ${getFontFamilyString(ui.font_family)} !important;` : ""}
      ${ui.font_size_base ? `font-size: ${ui.font_size_base}px !important;` : ""}
    }

    /* ── Global icon styling ── */
    .lucide {
      ${ui.icon_size ? `width: var(--ums-icon-size); height: var(--ums-icon-size);` : ""}
      ${ui.icon_color ? `stroke: var(--ums-icon-color);` : ""}
    }
    [data-ums-chatbot] .lucide {
      stroke: currentColor;
    }

    /* ── Icons inside buttons use button text color ── */
    button .lucide,
    [role="button"] .lucide,
    .lucide.inline-flex {
      stroke: currentColor;
    }

    /* ── Sidebar styling ── */
    [data-sidebar] {
      font-size: var(--ums-sidebar-font-size, 14px);
      font-weight: var(--ums-sidebar-font-weight, 500);
    }
    [data-sidebar] .lucide {
      width: var(--ums-sidebar-icon-size, 16px);
      height: var(--ums-sidebar-icon-size, 16px);
    }

    /* ── Card box shadow ── */
    [data-slot="card"] {
      box-shadow: var(--ums-card-shadow, 0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06), 0 1px 2px 0 rgba(0,0,0,0.04));
    }

    /* ── Avatar shape and size ── */
    [data-slot="avatar"] {
      border-radius: var(--ums-avatar-border-radius, 9999px) !important;
    }

    /* ── Table stripe color ── */
    ${
      ui.table_stripe_color
        ? `tr:nth-child(even) { background-color: ${ui.table_stripe_color} !important; }`
        : ""
    }

    /* ── Modal overlay opacity ── */
    [data-slot="alert-dialog-overlay"] {
      background: rgba(0,0,0,${Number(ui.modal_overlay_opacity ?? 50) / 100}) !important;
      backdrop-filter: blur(0px) !important;
    }

    /* ── Sticky header ── */
    ${ui.sticky_header ? "header.ums-sticky-header { position: sticky !important; top: 0 !important; z-index: 30 !important; background: color-mix(in srgb, var(--background) 85%, transparent) !important; backdrop-filter: blur(8px) !important; -webkit-backdrop-filter: blur(8px) !important; border-bottom: 1px solid color-mix(in srgb, var(--border) 50%, transparent) !important; }" : ""}

    /* ── Dashboard background image ── */
    ${
      ui.dashboard_background_image_url
        ? `
      .bg-campus {
        background: url('${ui.dashboard_background_image_url}') center/cover no-repeat fixed !important;
      }
      [data-slot="sidebar-inset"] {
        background: url('${ui.dashboard_background_image_url}') center/cover no-repeat fixed !important;
      }
    `
        : ""
    }
  `

  return <style dangerouslySetInnerHTML={{ __html: customCss }} />
}
