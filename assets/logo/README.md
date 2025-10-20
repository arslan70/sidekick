# SideKick AI Logo Assets

This directory contains all logo assets for the SideKick AI project in various formats and sizes.

## Design Concept

The logo represents the **Orchestrator concept** - a central orchestrator node (orange) connected to 7 worker agents (blue), visualizing the hierarchical multi-agent architecture that powers SideKick AI.

### Color Palette
- **AWS Orange**: `#FF9900` - Central orchestrator node
- **Tech Blue**: `#0066CC` - Worker agent nodes
- **AI Purple**: `#7B3FF2` - Accent color for "AI" text

### Typography
- **Font**: Inter (sans-serif)
- **Weights**: 300 (Light), 400 (Regular), 600 (Semi-Bold), 700 (Bold), 800 (Extra-Bold)

## Directory Structure

```
assets/logo/
├── vector/          # SVG source files
├── png/             # PNG exports in various sizes
├── favicon/         # Favicon formats for web
├── social/          # Social media assets
└── README.md        # This file
```

## File Inventory

### Vector Files (SVG)
Located in `vector/`

- **sidekick-logo.svg** - Full color logo with text (2000×500px)
- **sidekick-icon.svg** - Icon only, no text (512×512px)
- **sidekick-logo-monochrome.svg** - Grayscale version for print

### PNG Exports
Located in `png/`

#### Full Logo
- `sidekick-logo-2000x500.png` - High-resolution for README header
- `sidekick-logo-1000x250.png` - Medium resolution
- `sidekick-logo-mono-2000x500.png` - Monochrome version

#### Icon Variations
- `sidekick-icon-1024x1024.png` - Extra large
- `sidekick-icon-512x512.png` - Large
- `sidekick-icon-256x256.png` - Medium
- `sidekick-icon-128x128.png` - Small
- `sidekick-icon-64x64.png` - Tiny
- `sidekick-icon-32x32.png` - Micro
- `sidekick-icon-16x16.png` - Favicon size

### Favicon Formats
Located in `favicon/`

- `favicon.ico` - Multi-size ICO (16×16, 32×32, 48×48)
- `favicon-16x16.png` - Standard favicon
- `favicon-32x32.png` - Retina favicon
- `apple-touch-icon.png` - iOS home screen (180×180)
- `android-chrome-192x192.png` - Android home screen
- `android-chrome-512x512.png` - Android splash screen

### Social Media Assets
Located in `social/`

- `og-image.png` - Open Graph image (1200×630) for Facebook, LinkedIn
- `twitter-card.png` - Twitter card image (1200×675)
- `linkedin-banner.png` - LinkedIn banner (1200×627)
- `github-social-preview.png` - GitHub social preview (1280×640)

## Usage Guidelines

### README Header
```markdown
![SideKick AI Logo](assets/logo/png/sidekick-logo-2000x500.png)
```

### Favicon (HTML)
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

### Open Graph Meta Tags
```html
<meta property="og:image" content="https://yourdomain.com/assets/logo/social/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
```

### Twitter Card
```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://yourdomain.com/assets/logo/social/twitter-card.png">
```

## Testing Checklist

- [x] Logo legible at 16×16 pixels (favicon size)
- [x] Logo legible at 512×512 pixels (icon size)
- [x] Logo works on light backgrounds (white)
- [x] Logo works on dark backgrounds (use monochrome version)
- [x] All PNG files generated correctly
- [x] Favicon ICO contains multiple sizes
- [x] Social media images have correct dimensions

## Regenerating Assets

To regenerate all logo assets from SVG sources:

```bash
python scripts/generate_logo_assets.py
```

This script requires:
- Python 3.7+
- `cairosvg` package
- `Pillow` (PIL) package

Install dependencies:
```bash
pip install cairosvg pillow
```

## License

These logo assets are part of the SideKick AI project and are subject to the project's license terms.

---

**Generated**: October 2025  
**For**: AWS AI Agent Global Hackathon Submission
