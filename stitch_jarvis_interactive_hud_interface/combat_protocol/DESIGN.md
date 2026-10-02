---
name: Combat Protocol
colors:
  surface: '#0a151b'
  surface-dim: '#0a151b'
  surface-bright: '#303b41'
  surface-container-lowest: '#050f15'
  surface-container-low: '#121d23'
  surface-container: '#162127'
  surface-container-high: '#212b32'
  surface-container-highest: '#2b363d'
  on-surface: '#d9e4ed'
  on-surface-variant: '#ebbbb4'
  inverse-surface: '#d9e4ed'
  inverse-on-surface: '#273238'
  outline: '#b18780'
  outline-variant: '#603e39'
  surface-tint: '#ffb4a8'
  primary: '#ffb4a8'
  on-primary: '#690100'
  primary-container: '#ff5540'
  on-primary-container: '#5c0000'
  inverse-primary: '#c00100'
  secondary: '#ffb4a8'
  on-secondary: '#620f08'
  secondary-container: '#85291e'
  on-secondary-container: '#ff9f90'
  tertiary: '#ffb3ae'
  on-tertiary: '#68000b'
  tertiary-container: '#ff5352'
  on-tertiary-container: '#5c0008'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad4'
  primary-fixed-dim: '#ffb4a8'
  on-primary-fixed: '#410000'
  on-primary-fixed-variant: '#930100'
  secondary-fixed: '#ffdad4'
  secondary-fixed-dim: '#ffb4a8'
  on-secondary-fixed: '#410000'
  on-secondary-fixed-variant: '#82271c'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ae'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930014'
  background: '#0a151b'
  on-background: '#d9e4ed'
  surface-variant: '#2b363d'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  body-md:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0.01em
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: 0.15em
  mono-data:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.02em
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 40px
  grid-columns: '12'
---

## Brand & Style

This design system represents a transition from standby monitoring to active tactical engagement. The brand personality is urgent, precise, and authoritative, designed to focus the user's attention on critical data and immediate threats.

The aesthetic blends **High-Contrast / Bold** elements with **Glassmorphism** and **Tactile** overlays. It leverages a "Heads-Up Display" (HUD) logic, where UI elements appear as light projections over a dark, deep-space void. The emotional response is one of heightened alertness—transforming the interface into a high-stakes command center. Visual indicators are sharp and digital, utilizing scanning lines, warning patterns (chevron stripes), and chromatic aberration to emphasize the "Combat Mode" state.

## Colors

The palette is strictly dominated by "Aggressive Red" to signal a state of emergency and combat readiness. 

- **Primary (#ff0000):** Used for active data points, critical borders, and interactive states. This color should always be accompanied by a subtle outer glow (bloom) to simulate a light-emitting display.
- **Surface (#0a151b):** The foundation of the UI. A deep, cold obsidian that provides maximum contrast for the red neon elements.
- **Alert Tints:** Secondary and tertiary reds are used for data visualization gradients and non-critical "warning" fills, ensuring the UI has depth without overwhelming the user with pure red.
- **Support:** Pure black (#000000) is used for high-level masking and deep shadowing to enhance the glassmorphic "floating" effect.

## Typography

Typography is treated as a tactical read-out. **Space Grotesk** is utilized for its geometric, technical character which excels in high-contrast environments.

- **Urgency through Casing:** All labels, navigation, and headers must be set in All-Caps to maintain an authoritative tone.
- **Data Readouts:** Numerical data should use the `mono-data` style, ensuring alignment and legibility during rapid value fluctuations.
- **Styling:** Headlines should occasionally incorporate a "stutter" or "glitch" effect in motion, but remain static and sharp in layout. Heavy use of letter-spacing on labels mimics military-grade hardware interfaces.

## Layout & Spacing

The layout follows a **Fluid HUD Grid** philosophy. Information is pushed to the periphery of the screen to leave the center clear for "targeting" or primary focal content.

- **The 4px Rule:** All spacing between elements must be a multiple of 4px to maintain a mathematical, technical precision.
- **Modular Panels:** Content is housed in "Targeting Modules" that snap to a 12-column grid on desktop. On mobile, these modules stack vertically with a 16px gutter.
- **Safety Margins:** Large margins on the edges of the screen simulate the boundaries of a visor or cockpit display.
- **Information Density:** High density is preferred. Elements are packed tightly to provide a "data-rich" environment, separated by thin 1px lines rather than large gaps of whitespace.

## Elevation & Depth

Depth is not achieved through traditional shadows, but through **Tonal Layers** and **Light Emission**.

- **Backdrop Blurs:** Use heavy backdrop blurs (20px+) on containers to separate them from the background noise while maintaining a sense of transparency.
- **Inner Glows:** Instead of drop shadows, use `inner-shadow` with the Primary Red to make panels look like they are energized or powered "on."
- **Warning Patterns:** The lowest elevation layer (the background) features a subtle "scanline" overlay (1px horizontal lines at 10% opacity).
- **Active Elevation:** When a component is "Active," it gains a 0 0 15px primary red outer glow, simulating heat and energy.

## Shapes

The shape language is **Sharp** and aggressive. 

- **Hard Angles:** All buttons, panels, and input fields have 0px corner radius. Rounded corners are perceived as "soft" and are prohibited in Combat Mode.
- **Chiselled Corners:** For primary containers, use a 45-degree "clipped corner" (dog-ear) effect on the top-right or bottom-left to emphasize a custom-machined, tactical aesthetic.
- **Lines:** Borders are strictly 1px or 2px. Avoid thick, heavy blocks of color; prefer outlined frames to maintain the "holographic" feel.

## Components

- **Tactical Buttons:** Rectangular with 1px borders. Default state is an outline; hover/active state is a solid red fill with black text. Include a small "bracket" icon in the corners to simulate a targeting reticle.
- **Status Chips:** Small, rectangular labels. Use "Caution Stripes" (diagonal red/black lines) for critical status chips.
- **Data Fields:** Input fields consist only of a bottom border and a label in `label-caps`. When focused, the bottom border glows and a cursor block (solid red rectangle) blinks.
- **Reticle Cards:** Cards do not have background fills by default—only 1px corner brackets. If background fill is required, use #ff0000 at 5% opacity.
- **Progress Bars:** Segmented into blocks rather than a continuous smooth fill to represent discrete data packets.
- **Warning Overlays:** Full-screen 1px red borders that pulse slowly (0.5Hz) when a "Threat Detected" state is active.