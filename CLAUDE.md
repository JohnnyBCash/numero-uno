# CLAUDE.md - AI Assistant Guide

This document provides essential context for AI assistants working with this codebase.

## Project Overview

**Bitcoin Power Law Website** - A modern, interactive web application that visualizes Bitcoin's price trajectory through power law regression analysis. The site displays real-time Bitcoin prices, statistical metrics, and an interactive chart comparing actual prices against the power law prediction model.

## Codebase Structure

```
numero-uno/
├── index.html       # Main HTML entry point with semantic markup
├── styles.css       # All CSS styling with CSS custom properties
├── script.js        # Core JavaScript logic (vanilla JS, no frameworks)
├── package.json     # Project metadata and npm scripts
├── README.md        # Project documentation
├── FEATURES.md      # Detailed feature overview
├── QUICKSTART.md    # Beginner-friendly setup guide
└── .gitignore       # Git ignore patterns
```

## Technology Stack

- **HTML5**: Semantic markup, no templating
- **CSS3**: Custom properties (CSS variables), Grid, Flexbox, responsive design
- **Vanilla JavaScript**: ES6+, async/await, no build process
- **Chart.js 4.4.1**: Loaded via CDN for chart rendering
- **date-fns adapter**: Chart.js time-series support (CDN)
- **CoinGecko API**: Free API for Bitcoin price data (no auth required)

## Key Files and Their Responsibilities

### `index.html`
- Entry point loaded in browser
- Loads Chart.js and date-fns adapter from CDN
- Contains stat cards, chart container, and info section
- References `styles.css` and `script.js`

### `styles.css`
- CSS custom properties defined in `:root` for theming
- Color scheme: dark background (#0a0a0a), Bitcoin orange accent (#f7931a)
- Responsive breakpoints at 768px for mobile
- Key classes: `.container`, `.stats-container`, `.stat-card`, `.chart-container`

### `script.js`
Core functionality organized as:
- **Constants**: `GENESIS_DATE` (January 3, 2009)
- **`daysSinceGenesis(date)`**: Calculates days since Bitcoin genesis
- **`powerLawRegression(data)`**: Implements linear regression in log space
- **`predictPowerLaw(days, params)`**: Generates price predictions
- **`fetchBitcoinData()`**: Async function fetching from CoinGecko API
- **`updateStats(data, regression)`**: Updates DOM stat cards
- **`createChart(data, regression)`**: Renders Chart.js visualization
- **`init()`**: Main initialization, called on DOMContentLoaded
- Auto-refresh: Data refreshes every 5 minutes via `setInterval`

## Development Workflow

### Running Locally

```bash
# Option 1: Python HTTP server (recommended)
python3 -m http.server 8000
# Visit http://localhost:8000

# Option 2: Using npm script
npm start
# or
npm run serve

# Option 3: Open index.html directly in browser
# (Some features may not work due to CORS)
```

### No Build Process Required
This is a static site with no compilation, bundling, or transpilation needed. Edit files directly and refresh browser.

## API Integration

### CoinGecko API
- **Endpoint**: `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart`
- **Parameters**: `vs_currency=usd&days=max&interval=daily`
- **No authentication required**
- **Rate limits**: Be mindful of CoinGecko's free tier limits
- **Response format**: `{ prices: [[timestamp, price], ...] }`

## Code Conventions

### JavaScript
- Use `const` for constants, `let` for variables
- Async/await for asynchronous operations
- Arrow functions for callbacks
- Template literals for string interpolation
- DOM updates via `document.getElementById().textContent`

### CSS
- Use CSS custom properties for colors/theming (defined in `:root`)
- Mobile-first responsive design with `@media (max-width: 768px)`
- BEM-like class naming (e.g., `.stat-card`, `.stat-label`, `.stat-value`)
- Prefer Grid/Flexbox over floats

### HTML
- Semantic elements (`<header>`, `<footer>`, `<section>`)
- Accessibility: meaningful text in elements
- Scripts loaded at end of body or with appropriate loading strategy

## Key Constants and Configuration

```javascript
// Bitcoin genesis block date (script.js:2)
const GENESIS_DATE = new Date('2009-01-03T00:00:00Z');

// Auto-refresh interval (script.js:279)
setInterval(init, 5 * 60 * 1000); // 5 minutes
```

### CSS Theme Variables (styles.css:1-11)
```css
:root {
    --bg-primary: #0a0a0a;
    --bg-secondary: #1a1a1a;
    --bg-card: #252525;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --accent: #f7931a;        /* Bitcoin orange */
    --accent-hover: #ff9d2e;
    --border: #333333;
    --success: #00d084;
}
```

## Common Tasks

### Modifying the Power Law Model
Edit `powerLawRegression()` in `script.js:15-55` to adjust regression calculation.

### Adding New Statistics
1. Add HTML element in `index.html` within `.stats-container`
2. Update `updateStats()` function in `script.js:95-114`
3. Style with `.stat-card` class in `styles.css`

### Changing Chart Appearance
Modify the Chart.js configuration in `createChart()` at `script.js:117-246`.

### Updating Color Theme
Change CSS custom properties in `:root` at `styles.css:1-11`.

### Adjusting Refresh Interval
Modify the `setInterval` call at `script.js:279`.

## Error Handling

The app handles errors gracefully:
- API failures display "Error loading data" in stat cards
- Console logging for debugging (`console.log`, `console.error`)
- Data validation filters out invalid/zero values

## Deployment

Static site deployable to:
- **GitHub Pages**: Enable in repo Settings > Pages
- **Netlify/Vercel/Cloudflare Pages**: Connect repo for auto-deploy
- **Any static host**: Upload HTML, CSS, JS files

No server-side processing required.

## Important Notes for AI Assistants

1. **No build process**: Changes take effect immediately on browser refresh
2. **CDN dependencies**: Chart.js loaded from CDN, not local files
3. **API rate limits**: CoinGecko free tier has rate limits; avoid excessive requests
4. **Browser compatibility**: Targets modern browsers (ES6+ support required)
5. **No tests**: Project currently has no automated test suite
6. **Single page**: Entire application is one page (`index.html`)

## Mathematical Model Reference

The Power Law equation: `Price = a × Days^β`

Where:
- `Days` = days since Bitcoin genesis (January 3, 2009)
- `β` (beta) = slope coefficient (typically ~5.5)
- `a` = scaling constant
- `R²` = coefficient of determination (model accuracy, typically >95%)

Regression is performed in log space:
```
log(price) = log(a) + β × log(days)
```

## File Modification Guidelines

- **HTML changes**: Edit `index.html` directly
- **Styling changes**: Edit `styles.css`, use existing custom properties
- **Logic changes**: Edit `script.js`, maintain existing function structure
- **New dependencies**: Add via CDN in `index.html` `<head>` section
