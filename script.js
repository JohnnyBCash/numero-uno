// Genesis block date for Bitcoin
const GENESIS_DATE = new Date('2009-01-03T00:00:00Z');

// Global variables
let chart;
let historicalData = [];

// Calculate days since genesis
function daysSinceGenesis(date) {
    const diff = date - GENESIS_DATE;
    return Math.floor(diff / (1000 * 60 * 60 * 24));
}

// Power law regression
function powerLawRegression(data) {
    // Convert to log space: log(price) = log(a) + β * log(days)
    const logData = data.map(point => ({
        x: Math.log(point.days),
        y: Math.log(point.price)
    })).filter(point => isFinite(point.x) && isFinite(point.y) && point.price > 0);

    const n = logData.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

    logData.forEach(point => {
        sumX += point.x;
        sumY += point.y;
        sumXY += point.x * point.y;
        sumX2 += point.x * point.x;
        sumY2 += point.y * point.y;
    });

    // Calculate slope (β) and intercept (log(a))
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Calculate R²
    const yMean = sumY / n;
    let ssRes = 0, ssTot = 0;

    logData.forEach(point => {
        const yPred = intercept + slope * point.x;
        ssRes += Math.pow(point.y - yPred, 2);
        ssTot += Math.pow(point.y - yMean, 2);
    });

    const r2 = 1 - (ssRes / ssTot);

    return {
        slope: slope,
        intercept: intercept,
        r2: r2,
        a: Math.exp(intercept)
    };
}

// Generate power law prediction
function predictPowerLaw(days, params) {
    return params.a * Math.pow(days, params.slope);
}

// Fetch Bitcoin historical data
async function fetchBitcoinData() {
    try {
        // Fetch data from CoinGecko - max available history
        const response = await fetch(
            'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=max&interval=daily'
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }

        const data = await response.json();
        
        // Process the data
        historicalData = data.prices.map(([timestamp, price]) => {
            const date = new Date(timestamp);
            const days = daysSinceGenesis(date);
            return {
                date: date,
                days: days,
                price: price
            };
        }).filter(point => point.days > 0 && point.price > 0);

        return historicalData;
    } catch (error) {
        console.error('Error fetching Bitcoin data:', error);
        return null;
    }
}

// Update statistics display
function updateStats(data, regression) {
    // Current price
    const currentPrice = data[data.length - 1].price;
    document.getElementById('currentPrice').textContent = 
        `$${currentPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

    // R² value
    document.getElementById('r2Value').textContent = 
        `${(regression.r2 * 100).toFixed(2)}%`;

    // Slope
    document.getElementById('slopeValue').textContent = 
        regression.slope.toFixed(3);

    // Days since genesis
    const today = new Date();
    const days = daysSinceGenesis(today);
    document.getElementById('daysSinceGenesis').textContent = 
        days.toLocaleString('en-US');
}

// Create chart
function createChart(data, regression) {
    const ctx = document.getElementById('powerLawChart').getContext('2d');

    // Generate power law line
    const minDays = Math.min(...data.map(d => d.days));
    const maxDays = Math.max(...data.map(d => d.days));
    
    const powerLawLine = [];
    for (let days = minDays; days <= maxDays; days += Math.floor((maxDays - minDays) / 500)) {
        const date = new Date(GENESIS_DATE.getTime() + days * 24 * 60 * 60 * 1000);
        powerLawLine.push({
            x: date,
            y: predictPowerLaw(days, regression)
        });
    }

    // Create chart
    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Bitcoin Price',
                    data: data.map(d => ({ x: d.date, y: d.price })),
                    borderColor: 'rgba(247, 147, 26, 0.8)',
                    backgroundColor: 'rgba(247, 147, 26, 0.1)',
                    pointRadius: 0,
                    borderWidth: 2,
                    tension: 0
                },
                {
                    label: 'Power Law Regression',
                    data: powerLawLine,
                    borderColor: 'rgba(0, 208, 132, 0.9)',
                    backgroundColor: 'rgba(0, 208, 132, 0.1)',
                    pointRadius: 0,
                    borderWidth: 3,
                    borderDash: [5, 5],
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#f7931a',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += '$' + context.parsed.y.toLocaleString('en-US', {
                                minimumFractionDigits: 0,
                                maximumFractionDigits: 0
                            });
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'year',
                        displayFormats: {
                            year: 'yyyy'
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0'
                    }
                },
                y: {
                    type: 'logarithmic',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0',
                        callback: function(value) {
                            if (value === 0.01 || value === 0.1 || value === 1 || value === 10 || 
                                value === 100 || value === 1000 || value === 10000 || 
                                value === 100000 || value === 1000000) {
                                return '$' + value.toLocaleString();
                            }
                            return null;
                        }
                    },
                    min: 0.01,
                    title: {
                        display: true,
                        text: 'Price (USD) - Log Scale',
                        color: '#ffffff',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
}

// Initialize application
async function init() {
    console.log('Fetching Bitcoin data...');
    
    const data = await fetchBitcoinData();
    
    if (!data || data.length === 0) {
        console.error('No data available');
        document.getElementById('currentPrice').textContent = 'Error loading data';
        document.getElementById('r2Value').textContent = 'N/A';
        document.getElementById('slopeValue').textContent = 'N/A';
        return;
    }

    console.log(`Loaded ${data.length} data points`);

    // Calculate power law regression
    const regression = powerLawRegression(data);
    console.log('Regression parameters:', regression);

    // Update UI
    updateStats(data, regression);
    createChart(data, regression);

    console.log('Initialization complete');
}

// Run on page load
document.addEventListener('DOMContentLoaded', init);

// Refresh data every 5 minutes
setInterval(init, 5 * 60 * 1000);
