# Bitcoin Power Law Website - Feature Overview

## 🎯 Core Functionality

### 1. Power Law Regression Analysis
- Implements the mathematical model: `Price = a × Days^β`
- Calculates regression in logarithmic space for accuracy
- Computes R² coefficient to measure model fit
- Determines slope (β) coefficient

### 2. Real-Time Data Integration
- Fetches complete historical Bitcoin price data from CoinGecko API
- Updates current price automatically
- Auto-refresh every 5 minutes
- Graceful error handling

### 3. Interactive Visualization
- Logarithmic chart showing Bitcoin price history
- Power law trend line overlay
- Responsive Chart.js implementation
- Tooltip with formatted price data
- Time-series x-axis with year labels

## 📊 Displayed Metrics

1. **Current Price**: Real-time Bitcoin price in USD
2. **R² Accuracy**: Statistical measure of model fit (typically >95%)
3. **Slope (β)**: Power law coefficient (typically ~5.5)
4. **Days Since Genesis**: Time elapsed since January 3, 2009

## 🎨 Design Features

### Color Scheme
- Background: Dark gradient (#0a0a0a to #1a1a1a)
- Accent: Bitcoin orange (#f7931a)
- Text: White primary, gray secondary
- Cards: Dark (#252525) with subtle borders

### Responsive Layout
- Desktop: 4-column stats grid
- Tablet: 2-column layout
- Mobile: Single column, optimized spacing
- Chart adapts to container width

### Visual Effects
- Hover animations on stat cards
- Gradient text for main heading
- Smooth transitions
- Pulsing loading animation

## 🔧 Technical Stack

### Frontend
- **HTML5**: Semantic, accessible markup
- **CSS3**: Modern layouts (Grid, Flexbox)
- **Vanilla JavaScript**: No framework dependencies
- **Chart.js 4.4.1**: Professional charting
- **date-fns adapter**: Time-series support

### API Integration
- **CoinGecko API**: Free, no authentication required
- **Endpoint**: `/api/v3/coins/bitcoin/market_chart`
- **Parameters**: `vs_currency=usd`, `days=max`, `interval=daily`

## 📈 Mathematical Implementation

### Power Law Regression Algorithm

```javascript
// Transform to log space
log(price) = log(a) + β × log(days)

// Linear regression on transformed data
β = (n×ΣXY - ΣX×ΣY) / (n×ΣX² - (ΣX)²)
log(a) = (ΣY - β×ΣX) / n

// R² calculation
R² = 1 - (SSres / SStot)
```

### Prediction Function
```javascript
predictedPrice = a × days^β
```

## 🌐 Browser Compatibility

- ✅ Chrome/Edge (Chromium-based)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## 📱 Mobile Optimizations

- Touch-friendly interface
- Optimized font sizes
- Reduced padding on small screens
- Responsive chart height
- Single-column layout

## 🚀 Performance Features

- Minimal dependencies (only Chart.js)
- No build process required
- Efficient data processing
- Optimized chart rendering
- Lazy data refresh (5-min intervals)

## 🔮 Future Enhancement Ideas

1. **Additional Models**
   - Stock-to-Flow model overlay
   - Rainbow chart bands
   - Support/resistance levels

2. **Extended Analytics**
   - Historical R² over time
   - Prediction intervals
   - Volatility metrics

3. **User Customization**
   - Adjustable time ranges
   - Color theme toggle
   - Export chart as image

4. **Social Features**
   - Share current stats
   - Twitter integration
   - Price alerts

## 📦 Deployment Options

### Static Hosting
- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages

### Local Server
```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve

# PHP
php -S localhost:8000
```

## 🔒 Privacy & Security

- No user tracking
- No cookies
- Client-side processing only
- No sensitive data storage
- HTTPS recommended for production

## 📄 License & Attribution

- **License**: MIT
- **Data**: CoinGecko API
- **Inspiration**: b1m.io
- **Author**: johnny-cash
