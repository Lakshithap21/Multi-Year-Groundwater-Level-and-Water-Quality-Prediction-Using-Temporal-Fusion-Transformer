import sys

html_content = """<!DOCTYPE html>
<html lang="en" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Groundwater Forecasting System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
                    },
                    colors: {
                        primary: {
                            50: '#eff6ff',
                            100: '#dbeafe',
                            400: '#60a5fa',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                        },
                        darkbase: '#0f172a',
                        darkcard: '#1e293b'
                    },
                    animation: {
                        'fade-in': 'fadeIn 0.5s ease-out',
                        'slide-up': 'slideUp 0.5s ease-out forwards',
                    },
                    keyframes: {
                        fadeIn: {
                            '0%': { opacity: '0' },
                            '100%': { opacity: '1' },
                        },
                        slideUp: {
                            '0%': { opacity: '0', transform: 'translateY(20px)' },
                            '100%': { opacity: '1', transform: 'translateY(0)' },
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body {
            transition: background-color 0.4s ease, color 0.4s ease;
        }
        .glassmorphism {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .dark .glassmorphism {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        /* Custom stylings for inputs to match themes */
        select {
            appearance: none;
            background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236B7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
            background-position: right 0.5rem center;
            background-repeat: no-repeat;
            background-size: 1.5em 1.5em;
        }
        .dark select {
            background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%239CA3AF' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
            background-color: #0f172a;
            color: #f8fafc;
        }
        /* Year selector active ring */
        .year-btn.active {
            @apply ring-2 ring-primary-500 bg-primary-500 text-white shadow-lg shadow-primary-500/30 border-transparent transform -translate-y-1;
        }
        .dark .year-btn.active {
            @apply ring-primary-400 bg-primary-600 shadow-primary-500/20;
        }
    </style>
</head>
<body class="bg-slate-50 dark:bg-darkbase text-slate-800 dark:text-slate-200 antialiased min-h-screen relative overflow-x-hidden">

    <!-- Decorative background elements -->
    <div class="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary-400/20 dark:bg-primary-900/20 blur-[100px] pointer-events-none z-0"></div>
    <div class="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-teal-400/20 dark:bg-teal-900/20 blur-[100px] pointer-events-none z-0"></div>

    <div class="container mx-auto px-6 py-10 relative z-10 max-w-6xl">
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-center mb-12 animate-fade-in gap-6">
            <div>
                <h1 class="text-4xl md:text-5xl font-bold tracking-tight text-slate-900 dark:text-white mb-2">
                    <span class="text-primary-600 dark:text-primary-400">Groundwater</span> Forecast
                </h1>
                <p class="text-slate-500 dark:text-slate-400 text-lg">AI-Powered Predictions & Water Management</p>
            </div>
            <button id="themeToggle" class="p-3 rounded-full bg-white dark:bg-darkcard shadow-sm hover:shadow-md transition duration-300 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300">
                <svg id="sunIcon" class="w-6 h-6 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                <svg id="moonIcon" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path></svg>
            </button>
        </header>

        <!-- Controls -->
        <div class="glassmorphism rounded-2xl p-6 md:p-8 shadow-xl shadow-slate-200/50 dark:shadow-none mb-10 animate-slide-up" style="animation-delay: 0.1s;">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div>
                    <label for="state" class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 uppercase tracking-wide">Select State</label>
                    <select id="state" class="w-full bg-white dark:bg-darkbase border border-slate-300 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all shadow-sm">
                        <option value="">-- Choose State --</option>
                        {% for state in states %}
                        <option value="{{ state }}">{{ state }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label for="district" class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 uppercase tracking-wide">Select District</label>
                    <select id="district" disabled class="w-full bg-white dark:bg-darkbase border border-slate-300 dark:border-slate-600 rounded-xl px-4 py-3 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
                        <option value="">-- Choose District --</option>
                    </select>
                </div>
            </div>

            <div class="mb-8">
                <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wide">Forecast Period</label>
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <button class="year-btn active border dark:border-slate-600 rounded-xl py-3 px-2 text-center transition-all bg-white dark:bg-darkcard text-slate-600 dark:text-slate-300 hover:border-primary-400 hover:shadow-md" data-years="1">
                        <div class="font-bold">1 Year</div>
                        <div class="text-xs opacity-75 mt-1">(2024)</div>
                    </button>
                    <button class="year-btn border dark:border-slate-600 rounded-xl py-3 px-2 text-center transition-all bg-white dark:bg-darkcard text-slate-600 dark:text-slate-300 hover:border-primary-400 hover:shadow-md" data-years="2">
                        <div class="font-bold">2 Years</div>
                        <div class="text-xs opacity-75 mt-1">(2024-2025)</div>
                    </button>
                    <button class="year-btn border dark:border-slate-600 rounded-xl py-3 px-2 text-center transition-all bg-white dark:bg-darkcard text-slate-600 dark:text-slate-300 hover:border-primary-400 hover:shadow-md" data-years="3">
                        <div class="font-bold">3 Years</div>
                        <div class="text-xs opacity-75 mt-1">(2024-2026)</div>
                    </button>
                    <button class="year-btn border dark:border-slate-600 rounded-xl py-3 px-2 text-center transition-all bg-white dark:bg-darkcard text-slate-600 dark:text-slate-300 hover:border-primary-400 hover:shadow-md" data-years="4">
                        <div class="font-bold">4 Years</div>
                        <div class="text-xs opacity-75 mt-1">(2024-2027)</div>
                    </button>
                    <button class="year-btn border dark:border-slate-600 rounded-xl py-3 px-2 text-center transition-all bg-white dark:bg-darkcard text-slate-600 dark:text-slate-300 hover:border-primary-400 hover:shadow-md" data-years="5">
                        <div class="font-bold">5 Years</div>
                        <div class="text-xs opacity-75 mt-1">(2024-2028)</div>
                    </button>
                </div>
            </div>

            <button id="forecastBtn" disabled class="w-full py-4 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-bold text-lg shadow-lg shadow-primary-500/30 transition-all transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:focus:ring-offset-darkbase active:scale-[0.98]">
                Generate AI Forecast
            </button>
        </div>

        <!-- States -->
        <div id="error" class="hidden animate-fade-in bg-red-100 dark:bg-red-900/30 border-l-4 border-red-500 text-red-700 dark:text-red-400 p-5 rounded-r-xl shadow-sm mb-8 font-medium"></div>
        
        <div id="loading" class="hidden py-16 text-center animate-fade-in">
            <div class="inline-block relative w-16 h-16">
                <div class="absolute top-0 left-0 w-full h-full border-4 border-primary-200 dark:border-primary-900 rounded-full"></div>
                <div class="absolute top-0 left-0 w-full h-full border-4 border-primary-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p class="mt-4 text-slate-500 dark:text-slate-400 font-medium">Analyzing neural networks for predictions...</p>
        </div>

        <!-- ALERTS SECTION -->
        <div id="alertsContainer" class="hidden mb-10 animate-slide-up" style="animation-delay: 0.2s;">
            <div class="flex items-center gap-3 mb-6 border-b border-red-200 dark:border-red-900/50 pb-4">
                <span class="text-red-500 dark:text-red-400 text-2xl">⚠️</span>
                <h2 class="text-2xl font-bold text-slate-800 dark:text-slate-200">Critical Alerts</h2>
            </div>
            <div id="alertsList" class="space-y-4"></div>
        </div>

        <!-- RESULTS SECTION -->
        <div id="results" class="hidden animate-slide-up" style="animation-delay: 0.3s;">
            <div class="glassmorphism rounded-2xl p-6 md:p-8 shadow-xl shadow-slate-200/50 dark:shadow-none mb-10">
                <div class="border-b border-slate-200 dark:border-slate-700 pb-5 mb-8 flex flex-col md:flex-row justify-between items-start md:items-end">
                    <div>
                        <h2 class="text-2xl md:text-3xl font-bold text-slate-800 dark:text-white">Analysis Results</h2>
                        <p id="location-info" class="text-primary-600 dark:text-primary-400 mt-2 font-medium text-lg"></p>
                    </div>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mt-4 md:mt-0 bg-slate-100 dark:bg-slate-800 py-1.5 px-3 rounded-md">Using 4-year sliding window for predictions</p>
                </div>

                <div id="latest-metrics" class="mb-10"></div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="glassmorphism bg-white/50 dark:bg-darkcard/50 rounded-xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm transition-all hover:shadow-md">
                        <h3 class="text-lg font-semibold text-center text-slate-700 dark:text-slate-300 mb-4">Water Level</h3>
                        <div id="wl-chart" class="w-full h-80"></div>
                    </div>
                    <div class="glassmorphism bg-white/50 dark:bg-darkcard/50 rounded-xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm transition-all hover:shadow-md">
                        <h3 class="text-lg font-semibold text-center text-slate-700 dark:text-slate-300 mb-4">pH Level</h3>
                        <div id="ph-chart" class="w-full h-80"></div>
                    </div>
                    <div class="glassmorphism bg-white/50 dark:bg-darkcard/50 rounded-xl p-5 border border-slate-100 dark:border-slate-700/50 shadow-sm transition-all hover:shadow-md lg:col-span-2">
                        <h3 class="text-lg font-semibold text-center text-slate-700 dark:text-slate-300 mb-4">Nitrate Concentration</h3>
                        <div id="no3-chart" class="w-full h-80 lg:h-96"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Theme switching logic
        const themeToggleBtn = document.getElementById('themeToggle');
        const sunIcon = document.getElementById('sunIcon');
        const moonIcon = document.getElementById('moonIcon');
        const html = document.documentElement;

        // Check for saved theme preference or use OS preference
        if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            html.classList.add('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            html.classList.remove('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }

        themeToggleBtn.addEventListener('click', function() {
            // toggle icons
            sunIcon.classList.toggle('hidden');
            moonIcon.classList.toggle('hidden');

            if (html.classList.contains('dark')) {
                html.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            } else {
                html.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            }
            
            // Redraw charts if they exist to match theme
            if (currentCharts.length > 0) {
                // simulate click to recreate charts with new theme
                document.getElementById('forecastBtn').click();
            }
        });

        function getChartThemeSettings() {
            const isDark = document.documentElement.classList.contains('dark');
            return {
                textColor: isDark ? '#94a3b8' : '#475569',
                gridColor: isDark ? '#334155' : '#e2e8f0',
                titleColor: isDark ? '#f8fafc' : '#1e293b',
                plotBg: 'rgba(0,0,0,0)',
                paperBg: 'rgba(0,0,0,0)',
                legendBg: isDark ? 'rgba(30, 41, 59, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                legendBorder: isDark ? '#334155' : '#e2e8f0',
                historicalLine: isDark ? '#94a3b8' : '#64748b'
            };
        }

        // Application State
        let selectedYears = 1;
        let currentState = '';
        let currentDistrict = '';
        let currentCharts = [];

        // Clear previous charts function
        function clearPreviousCharts() {
            currentCharts.forEach(chart => {
                Plotly.purge(chart);
            });
            currentCharts = [];
        }

        // Year selector
        document.querySelectorAll('.year-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.year-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                selectedYears = parseInt(this.dataset.years);
            });
        });

        // State change
        document.getElementById('state').addEventListener('change', async function() {
            const state = this.value;
            currentState = state;
            const districtSelect = document.getElementById('district');
            const forecastBtn = document.getElementById('forecastBtn');
            
            if (!state) {
                districtSelect.disabled = true;
                districtSelect.innerHTML = '<option value="">-- Choose District --</option>';
                forecastBtn.disabled = true;
                return;
            }

            districtSelect.disabled = true;
            districtSelect.innerHTML = '<option value="">Loading districts...</option>';

            try {
                const response = await fetch(`/get_districts/${encodeURIComponent(state)}`);
                const districts = await response.json();
                
                districtSelect.innerHTML = '<option value="">-- Choose District --</option>';
                districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district;
                    option.textContent = district;
                    districtSelect.appendChild(option);
                });
                
                districtSelect.disabled = false;
            } catch (error) {
                districtSelect.innerHTML = '<option value="">Error loading districts</option>';
                console.error('Error loading:', error);
            }
        });

        // District change
        document.getElementById('district').addEventListener('change', function() {
            currentDistrict = this.value;
            document.getElementById('forecastBtn').disabled = !this.value;
        });

        // Forecast button
        document.getElementById('forecastBtn').addEventListener('click', async function() {
            const state = currentState;
            const district = currentDistrict;
            if (!state || !district) return;

            clearPreviousCharts();
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('alertsContainer').style.display = 'none';
            document.getElementById('loading').style.display = 'block';

            try {
                const response = await fetch('/forecast', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ state, district, num_years: selectedYears })
                });

                const data = await response.json();

                if (response.ok) {
                    if (data.alerts && data.alerts.length > 0) {
                        displayAlerts(data.alerts);
                    }
                    displayResults(data, state, district);
                } else {
                    showError(data.error || 'An error occurred while generating forecast');
                }
            } catch (error) {
                showError('Failed to generate forecast: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }

        function displayAlerts(alerts) {
            const alertsList = document.getElementById('alertsList');
            const alertsContainer = document.getElementById('alertsContainer');
            alertsList.innerHTML = '';
            
            alerts.forEach(alert => {
                const isCritical = alert.type === 'critical';
                const bgClass = isCritical ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/50' : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/50';
                const textCol = isCritical ? 'text-red-800 dark:text-red-300' : 'text-amber-800 dark:text-amber-300';
                const icon = isCritical ? '🚨' : '⚠️';
                const titleCol = isCritical ? 'text-red-900 dark:text-red-200' : 'text-amber-900 dark:text-amber-200';
                
                alertsList.innerHTML += `
                    <div class="${bgClass} border rounded-xl p-5 flex items-start gap-4 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-2xl">${icon}</div>
                        <div>
                            <div class="font-bold text-lg mb-1 ${titleCol}">${alert.category}</div>
                            <div class="${textCol}">${alert.message}</div>
                        </div>
                    </div>
                `;
            });
            alertsContainer.classList.remove('hidden');
        }

        function displayResults(data, state, district) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.classList.remove('hidden');
            resultsDiv.style.display = 'block';
            document.getElementById('location-info').textContent = `${district}, ${state}`;

            const latestForecast = data.forecast[data.forecast.length - 1];
            
            // Latest Metrics UI
            const metricsHtml = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white dark:bg-darkcard p-6 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-all text-center">
                        <div class="text-sm font-semibold text-slate-500 text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wide">Water Level (${latestForecast.year})</div>
                        <div class="text-3xl font-extrabold text-blue-600 dark:text-blue-400 mb-1">${latestForecast.wl} <span class="text-sm font-normal text-slate-400">m</span></div>
                        <div class="text-xs text-slate-400">Below Ground</div>
                    </div>
                    <div class="bg-white dark:bg-darkcard p-6 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-all text-center">
                        <div class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wide">pH Level (${latestForecast.year})</div>
                        <div class="text-3xl font-extrabold text-teal-600 dark:text-teal-400 mb-1">${latestForecast.ph}</div>
                        <div class="text-xs text-slate-400">pH Units</div>
                    </div>
                    <div class="bg-white dark:bg-darkcard p-6 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-all text-center">
                        <div class="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-2 uppercase tracking-wide">Nitrate (${latestForecast.year})</div>
                        <div class="text-3xl font-extrabold text-red-500 dark:text-red-400 mb-1">${latestForecast.no3} <span class="text-sm font-normal text-slate-400">mg/L</span></div>
                        <div class="text-xs text-slate-400">Concentration</div>
                    </div>
                </div>
            `;
            document.getElementById('latest-metrics').innerHTML = metricsHtml;

            // Generate Charts
            createChart('wl-chart', data, 'wl', 'Depth (m)', '#3b82f6');
            createChart('ph-chart', data, 'ph', 'pH Value', '#14b8a6');
            createChart('no3-chart', data, 'no3', 'mg/L', '#ef4444');
        }

        function createChart(elementId, data, key, unit, color) {
            const historicalYears = data.historical.years;
            const historicalValues = data.historical[key];
            const forecastYears = data.forecast.map(f => f.year);
            const forecastValues = data.forecast.map(f => f[key]);
            const allYears = [...historicalYears, ...forecastYears];
            
            const theme = getChartThemeSettings();

            const trace1 = {
                x: historicalYears,
                y: historicalValues,
                name: 'Historical',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: theme.historicalLine, width: 3, shape: 'spline'},
                marker: {size: 6, color: theme.historicalLine}
            };

            const trace2 = {
                x: forecastYears,
                y: forecastValues,
                name: 'AI Forecast',
                type: 'scatter',
                mode: 'lines+markers',
                line: {color: color, width: 3, dash: 'dash', shape: 'spline'},
                marker: {size: 8, symbol: 'diamond', color: color}
            };

            const layout = {
                font: { family: '"Plus Jakarta Sans", sans-serif', color: theme.textColor },
                xaxis: {
                    title: {text: 'Year', font: {size: 13}},
                    gridcolor: theme.gridColor,
                    tickmode: 'array',
                    tickvals: allYears,
                    showgrid: true,
                    zeroline: false
                },
                yaxis: {
                    title: {text: unit, font: {size: 13}},
                    gridcolor: theme.gridColor,
                    showgrid: true,
                    zeroline: false
                },
                plot_bgcolor: theme.plotBg,
                paper_bgcolor: theme.paperBg,
                showlegend: true,
                legend: {
                    orientation: 'h',
                    yanchor: 'bottom',
                    y: 1.02,
                    xanchor: 'right',
                    x: 1,
                    bgcolor: theme.legendBg,
                    bordercolor: theme.legendBorder,
                    borderwidth: 1
                },
                margin: {l: 50, r: 20, t: 30, b: 50},
                hovermode: 'x unified',
                autosize: true
            };

            const config = {
                responsive: true,
                displayModeBar: false
            };

            const chartDiv = document.getElementById(elementId);
            chartDiv.innerHTML = '';
            
            Plotly.newPlot(chartDiv, [trace1, trace2], layout, config);
            currentCharts.push(chartDiv);
        }
    </script>
</body>
</html>"""

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
print("Updated successfully")
