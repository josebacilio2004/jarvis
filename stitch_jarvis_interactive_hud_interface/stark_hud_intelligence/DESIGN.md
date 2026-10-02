---
name: Stark HUD Intelligence
colors:
  surface: '#0a151b'
  surface-dim: '#0a151b'
  surface-bright: '#303a42'
  surface-container-lowest: '#060f16'
  surface-container-low: '#131d23'
  surface-container: '#172127'
  surface-container-high: '#212b32'
  surface-container-highest: '#2c363d'
  on-surface: '#d9e4ed'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#d9e4ed'
  inverse-on-surface: '#283239'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#a6c8ff'
  on-secondary: '#00315f'
  secondary-container: '#3a92f7'
  on-secondary-container: '#002a53'
  tertiary: '#daf0ff'
  on-tertiary: '#1f333e'
  tertiary-container: '#bed4e2'
  on-tertiary-container: '#485c68'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#d5e3ff'
  secondary-fixed-dim: '#a6c8ff'
  on-secondary-fixed: '#001c3b'
  on-secondary-fixed-variant: '#004786'
  tertiary-fixed: '#d0e6f4'
  tertiary-fixed-dim: '#b4cad7'
  on-tertiary-fixed: '#081e28'
  on-tertiary-fixed-variant: '#354955'
  background: '#0a151b'
  on-background: '#d9e4ed'
  surface-variant: '#2c363d'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  body-fixed:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.2em
  data-numeral:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: -0.05em
spacing:
  unit: 4px
  gutter: 16px
  margin-edge: 32px
  panel-padding: 12px
---

## Brand & Style

The design system is a high-fidelity tactical Heads-Up Display (HUD) inspired by advanced aerospace and combat intelligence interfaces. It evokes a sense of hyper-precision, immense processing power, and futuristic sophistication. The aesthetic is built on "holographic functionalism"—every element must look like it is projected in a 3D space, serving a specific diagnostic or tactical purpose.

The visual style blends **Cyberpunk** and **Military HUD** movements. It utilizes deep layering, transparent glass panels, and "glow-wire" aesthetics to create depth. Atmospheric elements like scanlines, micro-grids, and peripheral data streams reinforce the immersion of being inside an advanced suit of armor.

## Colors

The palette is anchored in a "Deep Space" black base to ensure maximum contrast for glowing elements. 

- **Primary (Neon Cyan):** Used for active UI elements, focal points, and primary data readouts. It should have a subtle outer glow (0 0 8px).
- **Secondary (Interface Blue):** Used for supporting text, secondary borders, and inactive states.
- **Tertiary (Deep Tech Blue):** Used for background fills of containers to provide a sense of "glass" thickness without losing the black background.
- **Neutral:** Pure deep black. Used for the primary canvas to minimize eye strain and simulate a transparent visor.

All colors should be applied with varying opacities (usually 20% to 80%) to simulate the transparency of holographic projections.

## Typography

The typography system relies on a dual-font approach to balance futuristic geometry with technical legibility.

- **Headlines & Display:** Using **Space Grotesk** provides a wide, geometric, and aggressive tech look for titles and major status indicators.
- **Technical Data & Body:** Using **JetBrains Mono** ensures that coordinates, logs, and data streams remain perfectly aligned and legible, mimicking a command-line interface or tactical readout.

**Styling Note:** Use `text-shadow: 0 0 5px #00e5ff88` for primary headlines to simulate light emission from a holographic display.

## Layout & Spacing

This design system uses a **No Grid / Peripheral Layout** philosophy. Content is anchored to the corners and edges of the viewport to keep the center "Field of Vision" clear for primary interaction.

- **Peripheral Anchoring:** Critical system stats (Battery, Oxygen, Network) occupy the corners.
- **Center-Focus:** Circular gauges and crosshairs are centered but use high transparency to avoid obstructing the "view."
- **Modular Data Blocks:** Smaller data modules should be separated by 16px gutters.
- **Scanline Overlay:** A persistent, very low-opacity (2%) horizontal scanline pattern should cover the entire layout to add texture.

## Elevation & Depth

Hierarchy is achieved through **Backdrop Blurs** and **Tonal Glows** rather than traditional shadows.

- **Z-Axis Layering:** Use `backdrop-filter: blur(10px)` on panels to separate them from the background noise.
- **Glow Borders:** Instead of shadows, use inner and outer glows. A container is "elevated" if its border glow is more intense.
- **Wireframes:** Use 1px borders with varying opacities. A "active" panel has a 100% opacity primary color border; a "background" panel has a 20% opacity tertiary color border.
- **Parallax:** For high-fidelity implementations, UI modules should have a slight parallax effect based on cursor or head movement.

## Shapes

The shape language is **Sharp** and **Angular**. Rounded corners are avoided to maintain a military, high-precision aesthetic. 

- **Channeled Corners:** Instead of rounding, use 45-degree chamfers on panel corners.
- **Circular Geometry:** Status rings and arc-reactor-inspired modules must be perfectly circular, often composed of multiple concentric rings with gaps (dashed strokes) to imply rotation and mechanical complexity.

## Components

### Circular Gauges & Status Rings
The core of the HUD. These should be built using SVG with dashed strokes. Use CSS animations to create constant, slow rotation of different ring segments in opposing directions.

### Minimal Holographic Buttons
Buttons are 1px wireframe boxes. On hover, the box fills with a 10% primary color tint and the border glow intensifies. There is no solid fill in the default state.

### Data Visualization Modules
Line charts and histograms should be rendered as thin 1px lines without area fills. Use the secondary color for data lines and the primary color for the current value indicator.

### Input Fields
Inputs are marked with a "bracket" style border (top-left and bottom-right corners only). A flickering vertical pipe `|` serves as the cursor to maintain the terminal/monospaced aesthetic.

### Rotating Status Rings
Small rotating icons that appear next to loading data. Use a segmented circle that "fills" as data is processed.

### Warning Overlays
When in a "warning" state, the UI border glows should pulse in the `status_alert` color, and a low-opacity red tint should wash over the peripheral modules.