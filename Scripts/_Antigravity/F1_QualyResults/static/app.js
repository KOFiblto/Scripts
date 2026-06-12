// F1 Qualifying Analytics Logic

let driversData = [];
let selectedDrivers = new Set();
let qualyChart = null;

// Preset palette for beautiful neon lines
const COLOR_PALETTE = [
    '#e10600', // Red
    '#00f2fe', // Cyan
    '#39ff14', // Neon Green
    '#ff007f', // Pink
    '#ffaa00', // Orange
    '#b026ff', // Neon Purple
    '#ffff00', // Yellow
    '#00ffcc', // Teal
    '#ffffff', // White
    '#7f8c8d'  // Silver
];

// Team Color Mapping (to match F1 team colors if possible)
const TEAM_COLORS = {
    'red_bull': '#3671C6',
    'ferrari': '#F91536',
    'mercedes': '#27F4D2',
    'mclaren': '#FF8000',
    'aston_martin': '#229971',
    'alpine': '#0093cc',
    'williams': '#64C4FF',
    'haas': '#B6BABD',
    'sauber': '#52e252',
    'kick_sauber': '#52e252',
    'rb': '#6692FF',
    'alphatauri': '#5E8FAA',
    'alfa': '#C92D4B',
    'renault': '#FFF500',
    'racing_point': '#F596C8'
};

document.addEventListener('DOMContentLoaded', () => {
    initMultiselect();
    loadDrivers();
    
    document.getElementById('apply-filters-btn').addEventListener('click', updateAnalytics);
    document.getElementById('export-chart-btn').addEventListener('click', exportChart);
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const select = document.getElementById('driver-multiselect');
        if (!select.contains(e.target)) {
            document.getElementById('dropdown-menu').classList.remove('show');
            document.getElementById('select-box-btn').classList.remove('active');
        }
    });
    
    // Height & Width range slider listeners
    const heightSlider = document.getElementById('chart-height-slider');
    const widthSlider = document.getElementById('chart-width-slider');
    
    heightSlider.addEventListener('input', () => {
        const val = heightSlider.value;
        document.getElementById('height-val').textContent = val + 'px';
        document.getElementById('chart-container-inner').style.height = val + 'px';
        localStorage.setItem('f1_chart_height', val);
        if (qualyChart) {
            qualyChart.resize();
        }
    });
    
    widthSlider.addEventListener('input', () => {
        const val = widthSlider.value;
        document.getElementById('width-val').textContent = val === '100' ? 'Fit (100%)' : val + '%';
        applyChartWidth(val);
        localStorage.setItem('f1_chart_width', val);
        if (qualyChart) {
            qualyChart.resize();
        }
    });
    
    window.addEventListener('resize', () => {
        const val = widthSlider.value;
        applyChartWidth(val);
    });
});

function applyChartWidth(val) {
    const inner = document.getElementById('chart-container-inner');
    if (!inner) return;
    if (val === '100') {
        inner.style.width = '100%';
    } else {
        const parentWidth = inner.parentElement.clientWidth || 800;
        inner.style.width = Math.floor(parentWidth * (parseInt(val) / 100)) + 'px';
    }
}

function initMultiselect() {
    const selectBox = document.getElementById('select-box-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');
    const searchInput = document.getElementById('driver-search-input');
    
    selectBox.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
        selectBox.classList.toggle('active');
        if (dropdownMenu.classList.contains('show')) {
            searchInput.focus();
        }
    });
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filterDriverOptions(query);
    });
}

async function loadDrivers() {
    try {
        const response = await fetch('/api/drivers');
        driversData = await response.json();
        
        // Restore selected drivers from localStorage
        const savedDrivers = localStorage.getItem('f1_selected_drivers');
        if (savedDrivers) {
            selectedDrivers = new Set(JSON.parse(savedDrivers));
        } else {
            // Defaults
            const initialSelections = ['verstappen', 'hamilton'];
            initialSelections.forEach(id => {
                if (driversData.some(d => d.driver_id === id)) {
                    selectedDrivers.add(id);
                }
            });
        }
        
        renderDriverOptions(driversData);
        
        // Restore selected seasons from localStorage
        const savedSeasons = localStorage.getItem('f1_selected_seasons');
        if (savedSeasons) {
            const seasonsList = JSON.parse(savedSeasons);
            document.querySelectorAll('input[name="season"]').forEach(cb => {
                cb.checked = seasonsList.includes(cb.value);
            });
        }
        
        // Restore disable-dots setting
        const savedDisableDots = localStorage.getItem('f1_disable_dots');
        if (savedDisableDots !== null) {
            document.getElementById('disable-dots-checkbox').checked = (savedDisableDots === 'true');
        }
        
        // Restore size settings from localStorage
        const savedHeight = localStorage.getItem('f1_chart_height');
        if (savedHeight) {
            document.getElementById('chart-height-slider').value = savedHeight;
            document.getElementById('height-val').textContent = savedHeight + 'px';
            document.getElementById('chart-container-inner').style.height = savedHeight + 'px';
        }
        
        const savedWidth = localStorage.getItem('f1_chart_width');
        if (savedWidth) {
            document.getElementById('chart-width-slider').value = savedWidth;
            document.getElementById('width-val').textContent = savedWidth === '100' ? 'Fit (100%)' : savedWidth + '%';
            setTimeout(() => {
                applyChartWidth(savedWidth);
                if (qualyChart) {
                    qualyChart.resize();
                }
            }, 200);
        }
        
        updateSelectedBadge();
        updateAnalytics();
    } catch (err) {
        console.error("Failed to load drivers:", err);
    }
}

function renderDriverOptions(drivers) {
    const list = document.getElementById('driver-options-list');
    list.innerHTML = '';
    
    drivers.forEach(driver => {
        const option = document.createElement('div');
        option.className = 'driver-option';
        
        const isChecked = selectedDrivers.has(driver.driver_id) ? 'checked' : '';
        
        option.innerHTML = `
            <input type="checkbox" class="driver-checkbox" value="${driver.driver_id}" ${isChecked}>
            <div class="driver-info-meta">
                <span class="driver-meta-name">${driver.given_name} ${driver.family_name} (${driver.code || driver.family_name.substring(0,3).toUpperCase()})</span>
                <span class="driver-meta-team">${driver.team} | ${driver.nationality}</span>
            </div>
        `;
        
        option.addEventListener('click', (e) => {
            const cb = option.querySelector('input');
            if (e.target !== cb) {
                cb.checked = !cb.checked;
            }
            toggleDriverSelection(cb.value, cb.checked);
        });
        
        list.appendChild(option);
    });
}

function filterDriverOptions(query) {
    const options = document.querySelectorAll('.driver-option');
    options.forEach(option => {
        const name = option.querySelector('.driver-meta-name').textContent.toLowerCase();
        const team = option.querySelector('.driver-meta-team').textContent.toLowerCase();
        if (name.includes(query) || team.includes(query)) {
            option.style.display = 'flex';
        } else {
            option.style.display = 'none';
        }
    });
}

function toggleDriverSelection(driverId, isSelected) {
    if (isSelected) {
        selectedDrivers.add(driverId);
    } else {
        selectedDrivers.delete(driverId);
    }
    updateSelectedBadge();
}

function updateSelectedBadge() {
    const badge = document.getElementById('selected-badge');
    const placeholder = document.querySelector('.placeholder-text');
    
    if (selectedDrivers.size > 0) {
        badge.textContent = selectedDrivers.size;
        badge.style.display = 'inline-block';
        placeholder.style.display = 'none';
    } else {
        badge.style.display = 'none';
        placeholder.style.display = 'block';
    }
}

function getSelectedSeasons() {
    const checkboxes = document.querySelectorAll('input[name="season"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

async function updateAnalytics() {
    if (selectedDrivers.size === 0) {
        alert("Please select at least one driver.");
        return;
    }
    
    const driversQuery = Array.from(selectedDrivers).join(',');
    const seasonsQuery = getSelectedSeasons().join(',');
    const disableDots = document.getElementById('disable-dots-checkbox').checked;
    
    // Save to localStorage
    localStorage.setItem('f1_selected_drivers', JSON.stringify(Array.from(selectedDrivers)));
    localStorage.setItem('f1_selected_seasons', JSON.stringify(getSelectedSeasons()));
    localStorage.setItem('f1_disable_dots', disableDots);
    
    try {
        const response = await fetch(`/api/results?drivers=${driversQuery}&seasons=${seasonsQuery}`);
        const results = await response.json();
        
        processAndRenderData(results);
    } catch (err) {
        console.error("Error updating analytics:", err);
    }
}

function processAndRenderData(data) {
    // 1. Compile Unique Races as X-Axis Labels (sorted chronologically)
    const raceMap = new Map();
    data.forEach(item => {
        const key = `${item.season}_${item.round}`;
        if (!raceMap.has(key)) {
            raceMap.set(key, {
                label: `${item.season} R${item.round}: ${item.race_name.replace(' Grand Prix', '')}`,
                season: item.season,
                round: item.round
            });
        }
    });
    
    const sortedRaces = Array.from(raceMap.entries())
        .sort((a, b) => {
            if (a[1].season !== b[1].season) return a[1].season - b[1].season;
            return a[1].round - b[1].round;
        });
        
    const labels = sortedRaces.map(r => r[1].label);
    const raceKeys = sortedRaces.map(r => r[0]);

    // 2. Prepare Datasets for Chart
    const datasets = [];
    const driverList = Array.from(selectedDrivers);
    
    // Map of raceKey -> { teamName: [driverIds] } to detect teammates at each race
    const raceTeammates = {};
    data.forEach(item => {
        const key = `${item.season}_${item.round}`;
        if (!raceTeammates[key]) {
            raceTeammates[key] = {};
        }
        const team = item.constructor_name.toLowerCase().replace(/\s+/g, '_');
        if (!raceTeammates[key][team]) {
            raceTeammates[key][team] = [];
        }
        if (!raceTeammates[key][team].includes(item.driver_id)) {
            raceTeammates[key][team].push(item.driver_id);
        }
    });
    
    driverList.forEach((driverId, index) => {
        const driverResults = data.filter(r => r.driver_id === driverId);
        if (driverResults.length === 0) return;
        
        const driverInfo = driversData.find(d => d.driver_id === driverId);
        const name = driverInfo ? `${driverInfo.given_name} ${driverInfo.family_name}` : driverId;
        
        const teamColorsArray = [];
        const borderDashArray = [];
        
        // Map position values to labels index positions
        const dataPoints = raceKeys.map(key => {
            const match = driverResults.find(r => `${r.season}_${r.round}` === key);
            if (match) {
                const team = match.constructor_name.toLowerCase().replace(/\s+/g, '_');
                const color = TEAM_COLORS[team] || COLOR_PALETTE[index % COLOR_PALETTE.length];
                teamColorsArray.push(color);
                
                // Dash line if teammate is also selected and alphabetical order determines who gets dashed
                const teamDrivers = raceTeammates[key]?.[team] || [];
                if (teamDrivers.length > 1) {
                    teamDrivers.sort();
                    const driverIndexInTeam = teamDrivers.indexOf(driverId);
                    if (driverIndexInTeam > 0) {
                        borderDashArray.push([5, 5]);
                    } else {
                        borderDashArray.push([]);
                    }
                } else {
                    borderDashArray.push([]);
                }
                
                return match.position;
            } else {
                teamColorsArray.push('#7f8c8d');
                borderDashArray.push([]);
                return null;
            }
        });
        
        // Determine if teammate-dashing occurs for this driver in this set of races
        const hasTeammateDashing = borderDashArray.some(dash => dash.length > 0);
        const topLevelBorderDash = hasTeammateDashing ? [5, 5] : [];
        
        const disableDots = document.getElementById('disable-dots-checkbox').checked;
        const pointRadius = disableDots ? 0 : 4;
        
        datasets.push({
            label: name,
            data: dataPoints,
            borderColor: teamColorsArray[0] || '#7f8c8d',
            borderDash: topLevelBorderDash, // Set top-level borderDash so legend draws it dashed
            backgroundColor: (teamColorsArray[0] || '#7f8c8d') + '22',
            borderWidth: 3,
            tension: 0.2,
            spanGaps: true,
            pointBackgroundColor: teamColorsArray,
            pointBorderColor: '#ffffff',
            pointRadius: pointRadius,
            pointHoverRadius: 6,
            segment: {
                borderColor: (ctx) => {
                    const idx = ctx.p1DataIndex;
                    return teamColorsArray[idx] || '#7f8c8d';
                },
                borderDash: (ctx) => {
                    const idx = ctx.p1DataIndex;
                    return borderDashArray[idx] || [];
                }
            }
        });
    });

    // 3. Render Chart
    renderChart(labels, datasets);
    
    // 4. Calculate Stats & H2H
    calculateStats(data, driverList);
}

function renderChart(labels, datasets) {
    const ctx = document.getElementById('qualifyingChart').getContext('2d');
    
    if (qualyChart) {
        qualyChart.destroy();
    }
    
    qualyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    reverse: true, // P1 on top
                    min: 0.5,
                    max: 20,
                    ticks: {
                        stepSize: 1,
                        color: '#94a3b8',
                        font: {
                            family: 'Inter'
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            family: 'Inter',
                            size: 10
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        lineWidth: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        font: {
                            family: 'Outfit',
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(20, 24, 36, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    titleFont: {
                        family: 'Outfit',
                        weight: 'bold'
                    },
                    bodyFont: {
                        family: 'Inter'
                    }
                }
            }
        },
        plugins: [{
            id: 'seasonDividers',
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                const xAxis = chart.scales.x;
                const yAxis = chart.scales.y;
                const labels = chart.data.labels;
                
                // Draw Q3 cutoff line (between P10 and P11, i.e., value 10.5)
                const yQ3 = yAxis.getPixelForValue(10.5);
                ctx.save();
                ctx.beginPath();
                ctx.strokeStyle = 'rgba(0, 242, 254, 0.45)'; // Neon cyan Q3 line
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.moveTo(xAxis.left, yQ3);
                ctx.lineTo(xAxis.right, yQ3);
                ctx.stroke();
                
                // Q3 Text label
                ctx.fillStyle = '#00f2fe';
                ctx.font = 'bold 9px Inter';
                ctx.fillText('Q3 CUTOFF (P10)', xAxis.left + 8, yQ3 - 6);
                ctx.restore();
                
                if (!labels || labels.length <= 1) return;
                
                for (let i = 1; i < labels.length; i++) {
                    const currentSeason = labels[i].split(' ')[0];
                    const prevSeason = labels[i-1].split(' ')[0];
                    if (currentSeason !== prevSeason) {
                        const x1 = xAxis.getPixelForValue(labels[i - 1], i - 1);
                        const x2 = xAxis.getPixelForValue(labels[i], i);
                        
                        if (x1 !== undefined && x2 !== undefined && !isNaN(x1) && !isNaN(x2)) {
                            const midX = (x1 + x2) / 2;
                            
                            ctx.save();
                            ctx.beginPath();
                            ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)'; // Solid thick white divider
                            ctx.lineWidth = 4;
                            ctx.moveTo(midX, yAxis.top);
                            ctx.lineTo(midX, yAxis.bottom);
                            ctx.stroke();
                            ctx.restore();
                        }
                    }
                }
            }
        }]
    });
}

function calculateStats(data, driverList) {
    if (data.length === 0) return;
    
    // Set aggregate overview stats
    document.getElementById('stat-total-races').textContent = new Set(data.map(r => `${r.season}_${r.round}`)).size;
    
    const positions = data.map(r => r.position).filter(p => p > 0);
    const bestPos = Math.min(...positions);
    document.getElementById('stat-best-pos').textContent = bestPos === Infinity ? '-' : `P${bestPos}`;
    
    const poles = data.filter(r => r.position === 1).length;
    document.getElementById('stat-poles').textContent = poles;

    // Show H2H section if comparing multiple drivers
    const h2hSection = document.getElementById('h2h-section');
    const tbody = document.getElementById('h2h-body');
    
    if (driverList.length > 1) {
        h2hSection.style.display = 'block';
        tbody.innerHTML = '';
        
        // Calculate H2H stats per driver
        const stats = driverList.map(driverId => {
            const driverInfo = driversData.find(d => d.driver_id === driverId);
            const driverData = data.filter(r => r.driver_id === driverId);
            const count = driverData.length;
            const avg = count > 0 ? (driverData.reduce((acc, curr) => acc + curr.position, 0) / count).toFixed(1) : '-';
            const driverPoles = driverData.filter(r => r.position === 1).length;
            const q3 = driverData.filter(r => r.position <= 10).length;
            
            return {
                id: driverId,
                name: driverInfo ? `${driverInfo.given_name} ${driverInfo.family_name}` : driverId,
                team: driverInfo ? driverInfo.team : '',
                avg: avg,
                poles: driverPoles,
                q3: q3,
                rawResults: driverData
            };
        });

        // H2H Comparison algorithm: for each race where both drivers participated, who finished ahead?
        stats.forEach((driverA) => {
            let wins = 0;
            let totalMatchups = 0;
            
            stats.forEach(driverB => {
                if (driverA.id === driverB.id) return;
                
                driverA.rawResults.forEach(rA => {
                    const matchB = driverB.rawResults.find(rB => rB.season === rA.season && rB.round === rA.round);
                    if (matchB) {
                        totalMatchups++;
                        if (rA.position < matchB.position) {
                            wins++;
                        }
                    }
                });
            });
            
            const winPercentage = totalMatchups > 0 ? `(${((wins / totalMatchups) * 100).toFixed(0)}%)` : '';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${driverA.name}</strong><br><small style="color:var(--text-secondary)">${driverA.team}</small></td>
                <td>P${driverA.avg}</td>
                <td>${driverA.poles}</td>
                <td>${driverA.q3}</td>
                <td>${wins} / ${totalMatchups} wins ${winPercentage}</td>
            `;
            tbody.appendChild(tr);
        });
    } else {
        h2hSection.style.display = 'none';
    }
}

function exportChart() {
    if (!qualyChart) return;
    
    // Create link element and trigger download
    const link = document.createElement('a');
    link.download = 'f1-qualifying-history.png';
    link.href = qualyChart.toBase64Image();
    link.click();
}
