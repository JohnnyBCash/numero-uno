# Bitcoin Power Law Website

A modern, interactive website that visualizes Bitcoin's price trajectory through power law regression analysis, similar to b1m.io.

## Features

- **Real-time Bitcoin Price Data**: Fetches historical and current price data from CoinGecko API
- **Power Law Regression**: Calculates and displays the power law relationship between time and price
- **Interactive Chart**: Logarithmic chart showing actual Bitcoin prices vs. power law prediction
- **Statistical Metrics**: 
  - R² accuracy score
  - Slope (β) coefficient
  - Current price
  - Days since Bitcoin genesis block
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Dark Theme**: Modern, eye-friendly dark interface with Bitcoin orange accents

## Power Law Model

The Bitcoin Power Law model suggests that Bitcoin's price follows the equation:

```
Price = a × Days^β
```

Where:
- `Days` = days since Bitcoin genesis block (January 3, 2009)
- `β` (beta) = the slope coefficient
- `a` = the scaling constant
- `R²` = coefficient of determination (measures model accuracy)

## Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Custom styling with CSS Grid and Flexbox
- **JavaScript (Vanilla)**: Core functionality
- **Chart.js**: Interactive chart rendering
- **CoinGecko API**: Real-time and historical Bitcoin price data

## Usage

Simply open `index.html` in a web browser. The application will:

1. Fetch historical Bitcoin price data from CoinGecko
2. Calculate power law regression parameters
3. Display interactive chart and statistics
4. Auto-refresh data every 5 minutes

## Local Development

No build process required! Just open the HTML file:

```bash
# Option 1: Open directly in browser
open index.html

# Option 2: Use a simple HTTP server
python -m http.server 8000
# Then visit http://localhost:8000
```

## Data Source

Historical price data is sourced from the [CoinGecko API](https://www.coingecko.com/en/api), which provides free access to cryptocurrency market data.

## License

MIT License - Feel free to use and modify for your own projects.

## Acknowledgments

- Inspired by [b1m.io](https://b1m.io)
- Bitcoin genesis block: January 3, 2009
- Power law research by Giovanni Santostasi and others in the Bitcoin community
