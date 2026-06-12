document.addEventListener("DOMContentLoaded", function() {
    const loadingEl = document.getElementById("dashboard-loading");
    const emptyEl = document.getElementById("dashboard-empty");
    const contentEl = document.getElementById("dashboard-content");

    if (!contentEl) {
        // We are on a page that doesn't have the dashboard content elements (like Profiles or Sync)
        return;
    }

    // Fetch dashboard stats from backend API
    fetch("/api/dashboard_data")
        .then(response => response.json())
        .then(data => {
            if (loadingEl) loadingEl.classList.add("hidden");

            if (!data.success || !data.has_data) {
                if (emptyEl) emptyEl.classList.remove("hidden");
                return;
            }

            if (contentEl) contentEl.classList.remove("hidden");

            // Update stats
            document.getElementById("stat-total-hours").innerText = data.stats.total_hours;
            document.getElementById("stat-excused-hours").innerText = data.stats.excused_hours + "h";
            document.getElementById("stat-unexcused-hours").innerText = data.stats.unexcused_hours + "h";
            document.getElementById("stat-open-hours").innerText = data.stats.open_hours + "h";
            document.getElementById("stat-late-arrivals").innerText = data.stats.late_arrivals;
            document.getElementById("stat-full-hours").innerText = data.stats.full_hours_missed;

            // Render components
            renderHeatmap(data.heatmap);
            renderSubjectsChart(data.subjects);
            renderSubjectTable(data.subjects);
            renderDensityMatrix(data.density_matrix);
            renderWeekdaysChart(data.weekdays);
            renderAbsenceTable(data.absences);
        })
        .catch(err => {
            console.error("Error fetching dashboard data:", err);
            if (loadingEl) {
                loadingEl.innerHTML = `
                    <div class="text-github-red font-mono text-xs">
                        <i class="fa-solid fa-circle-exclamation text-lg mb-2"></i>
                        <div>Failed to load dashboard data. Please check local logs or recreate your profile.</div>
                    </div>
                `;
            }
        });
});

function renderHeatmap(heatmapData) {
    const gridContainer = document.getElementById("heatmap-grid");
    const monthContainer = document.getElementById("heatmap-month-labels");
    if (!gridContainer || !monthContainer) return;

    gridContainer.innerHTML = "";
    monthContainer.innerHTML = "";

    // 1. Calculate date range (past 365 days aligned to Monday)
    const today = new Date();
    
    // Start date is 365 days ago
    const startDate = new Date();
    startDate.setDate(today.getDate() - 365);
    
    // Align to the Monday of that week
    const startDay = startDate.getDay(); // 0 is Sunday, 1 is Monday, ...
    const diffToMonday = startDay === 0 ? -6 : 1 - startDay;
    const heatmapStart = new Date(startDate);
    heatmapStart.setDate(startDate.getDate() + diffToMonday);

    // End date is aligned to the Sunday of the current week (to fill the grid)
    const endDay = today.getDay();
    const diffToSunday = endDay === 0 ? 0 : 7 - endDay;
    const heatmapEnd = new Date(today);
    heatmapEnd.setDate(today.getDate() + diffToSunday);

    // 2. Loop dates and build grid columns
    let currentDate = new Date(heatmapStart);
    let columnsHtml = "";
    let currentColumnHtml = '<div class="flex flex-col gap-[3.5px]">';
    let dayInWeekIndex = 0;
    
    const monthLabels = [];
    let lastMonthName = "";
    let weekIndex = 0;

    while (currentDate <= heatmapEnd) {
        const dateStr = currentDate.toISOString().split("T")[0];
        const hours = heatmapData[dateStr] || 0;
        
        // Define intensity level matching GitHub style
        let colorClass = "bg-[#161b22] border border-[#21262d]"; // Level 0 (no absence)
        let levelText = "No absences";
        
        if (hours > 0) {
            levelText = `${hours} hours missed`;
            if (hours <= 1.5) {
                colorClass = "bg-[#0e4429]"; // Level 1 (Light green)
            } else if (hours <= 3.0) {
                colorClass = "bg-[#006d32]"; // Level 2 (Medium green)
            } else if (hours <= 5.0) {
                colorClass = "bg-[#26a641]"; // Level 3 (Bright green)
            } else {
                colorClass = "bg-[#39d353]"; // Level 4 (Vibrant green)
            }
        }
        
        const dayName = currentDate.toLocaleDateString("en-US", { weekday: "short" });
        const monthName = currentDate.toLocaleDateString("en-US", { month: "short" });
        const formattedDate = currentDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        const tooltip = `${levelText} on ${dayName}, ${formattedDate}`;

        currentColumnHtml += `
            <div class="w-[10.5px] h-[10.5px] rounded-[1.5px] ${colorClass} transition duration-100 hover:scale-125 cursor-pointer relative group" data-date="${dateStr}">
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-[#21262d] border border-[#30363d] text-[#f0f6fc] text-[10px] py-1.5 px-2.5 rounded-md whitespace-nowrap z-50 font-mono shadow-xl pointer-events-none">
                    ${tooltip}
                </div>
            </div>
        `;

        // Check if week ends
        dayInWeekIndex++;
        if (dayInWeekIndex === 7) {
            currentColumnHtml += "</div>";
            columnsHtml += currentColumnHtml;
            currentColumnHtml = '<div class="flex flex-col gap-[3.5px]">';
            dayInWeekIndex = 0;
            
            // Record month label alignment if the month changed at the beginning of the week
            if (monthName !== lastMonthName) {
                monthLabels.push({ weekIndex: weekIndex, label: monthName });
                lastMonthName = monthName;
            }
            weekIndex++;
        }

        // Increment day
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Add columns to grid
    gridContainer.innerHTML = columnsHtml;

    // 3. Render Month labels aligned to columns
    const totalWeeks = weekIndex;
    let labelHtml = "";
    let currentLabelWeek = 0;
    
    // Sort and place labels relative to the week index
    monthLabels.forEach((ml, idx) => {
        // Skip label if it is too close to the previous one
        if (idx > 0 && ml.weekIndex - monthLabels[idx-1].weekIndex < 3) {
            return;
        }
        
        const marginWeeks = ml.weekIndex - currentLabelWeek;
        // width of one column = 10.5px + 3px gap = 13.5px
        const widthMins = marginWeeks * 13.8;
        
        labelHtml += `<div style="margin-left: ${widthMins}px; width: 35px;" class="text-[9px] text-[#8b949e] font-mono leading-none truncate">${ml.label}</div>`;
        currentLabelWeek = ml.weekIndex + 2; // offset to account for label text width
    });
    
    monthContainer.innerHTML = labelHtml;
}

function renderSubjectsChart(subjectsData) {
    const ctx = document.getElementById("chart-subjects");
    if (!ctx) return;

    if (!subjectsData || subjectsData.length === 0) {
        document.getElementById("chart-subjects-empty").classList.remove("hidden");
        ctx.classList.add("hidden");
        return;
    }

    // Prepare chart data (limit to top 8 subjects for clean design, group others)
    let displayData = [...subjectsData];
    if (displayData.length > 8) {
        const top = displayData.slice(0, 7);
        const others = displayData.slice(7);
        const othersHours = others.reduce((sum, item) => sum + item.hours, 0);
        const othersMins = others.reduce((sum, item) => sum + (item.minutes || 0), 0);
        top.push({
            subject: "Others",
            hours: parseFloat(othersHours.toFixed(1)),
            minutes: othersMins,
            periods: parseFloat(othersHours.toFixed(1))
        });
        displayData = top;
    }

    const labels = displayData.map(item => item.subject);
    const dataValues = displayData.map(item => item.hours);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: dataValues,
                backgroundColor: '#2ea44f',
                borderColor: '#30363d',
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: '#2c974b',
            }]
        },
        options: {
            indexAxis: 'y', // Makes it horizontal
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#161b22',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    titleFont: { family: 'JetBrains Mono', size: 11 },
                    bodyFont: { family: 'JetBrains Mono', size: 11 },
                    callbacks: {
                        label: function(context) {
                            const item = displayData[context.dataIndex];
                            const totalMins = item.minutes || Math.round(item.hours * 50);
                            const h = Math.floor(totalMins / 60);
                            const m = Math.round(totalMins % 60);
                            const timeStr = h > 0 ? `${h}h ${m}m` : `${m}m`;
                            return ` ${item.hours} periods missed (${timeStr} clock time)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#21262d',
                        drawTicks: false
                    },
                    ticks: {
                        color: '#8b949e',
                        font: { family: 'JetBrains Mono', size: 10 }
                    },
                    border: {
                        dash: [4, 4],
                        color: '#30363d'
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#f0f6fc',
                        font: { family: 'JetBrains Mono', size: 11, weight: 'bold' }
                    }
                }
            }
        }
    });
}

function renderWeekdaysChart(weekdaysData) {
    const ctx = document.getElementById("chart-weekdays");
    if (!ctx) return;

    const labels = weekdaysData.map(item => item.day.substring(0, 3)); // Mon, Tue, etc.
    const dataValues = weekdaysData.map(item => item.hours);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: dataValues,
                backgroundColor: 'rgba(56, 139, 253, 0.45)', // GitHub link blue with alpha
                borderColor: '#388bfd',
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: 'rgba(56, 139, 253, 0.7)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#161b22',
                    borderColor: '#30363d',
                    borderWidth: 1,
                    titleFont: { family: 'JetBrains Mono', size: 11 },
                    bodyFont: { family: 'JetBrains Mono', size: 11 },
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y} school periods missed`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: '#21262d',
                        drawTicks: false
                    },
                    ticks: {
                        color: '#8b949e',
                        font: { family: 'JetBrains Mono', size: 10 }
                    },
                    border: {
                        dash: [4, 4],
                        color: '#30363d'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#f0f6fc',
                        font: { family: 'JetBrains Mono', size: 11 }
                    }
                }
            }
        }
    });
}

function renderAbsenceTable(absencesList) {
    const tbody = document.getElementById("absence-table-body");
    const emptyState = document.getElementById("absence-table-empty");
    const counter = document.getElementById("absence-count");
    if (!tbody) return;

    tbody.innerHTML = "";
    
    if (counter) {
        counter.innerText = `${absencesList.length} absence${absencesList.length === 1 ? '' : 's'}`;
    }

    if (!absencesList || absencesList.length === 0) {
        if (emptyState) emptyState.classList.remove("hidden");
        return;
    }

    if (emptyState) emptyState.classList.add("hidden");

    absencesList.forEach(ab => {
        // Create Status Badge HTML
        let statusBadge = "";
        if (ab.status === "excused") {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#1b2b20] text-[#34d399] border border-emerald-950 font-mono">Excused</span>`;
        } else if (ab.status === "unexcused") {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#341d1d] text-[#f87171] border border-red-950 font-mono">Unexcused</span>`;
        } else {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#2d251d] text-[#fbbf24] border border-yellow-950/40 font-mono">Open</span>`;
        }

        // Duration string
        let durationStr = `${ab.duration_periods} period`;
        if (ab.duration_periods !== 1) durationStr += "s";
        durationStr += ` (${ab.duration_minutes}m)`;

        // Format Date nicely
        let formattedDate = ab.date;
        try {
            const dt = new Date(ab.date);
            formattedDate = dt.toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'});
        } catch(e) {}

        const row = document.createElement("tr");
        row.className = "hover:bg-[#21262d]/20 transition duration-100";
        row.innerHTML = `
            <td class="px-4 py-3 text-github-header font-semibold whitespace-nowrap">${formattedDate}</td>
            <td class="px-4 py-3 text-github-muted whitespace-nowrap">${ab.time_range}</td>
            <td class="px-4 py-3 text-github-muted whitespace-nowrap">${durationStr}</td>
            <td class="px-4 py-3 text-github-header font-semibold whitespace-nowrap">${ab.subject}</td>
            <td class="px-4 py-3 text-github-muted whitespace-nowrap">${ab.teachers}</td>
            <td class="px-4 py-3 whitespace-nowrap">${statusBadge}</td>
            <td class="px-4 py-3 text-github-muted max-w-[200px] truncate" title="${ab.reason}">${ab.reason}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderSubjectTable(subjectsData) {
    const tbody = document.getElementById("subject-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if (!subjectsData || subjectsData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="px-2 py-4 text-center text-github-muted font-mono">No subject data.</td></tr>`;
        return;
    }
    
    subjectsData.forEach(item => {
        const h = Math.floor(item.minutes / 60);
        const m = Math.round(item.minutes % 60);
        const timeStr = h > 0 ? `${h}h ${m}m` : `${m}m`;
        
        const row = document.createElement("tr");
        row.className = "hover:bg-[#21262d]/20 transition duration-100";
        row.innerHTML = `
            <td class="px-2 py-2 text-github-header font-semibold whitespace-nowrap">${item.subject}</td>
            <td class="px-2 py-2 text-right text-github-muted whitespace-nowrap">${timeStr}</td>
            <td class="px-2 py-2 text-right text-github-header font-semibold whitespace-nowrap">${item.periods}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderDensityMatrix(matrix) {
    const container = document.getElementById("density-grid-rows");
    if (!container) return;
    container.innerHTML = "";
    
    if (!matrix) return;
    
    const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const dayShortNames = ["Mon", "Tue", "Wed", "Thu", "Fri"];
    const periodStartTimes = ["07:45", "08:35", "09:40", "10:30", "11:30", "12:20", "13:15", "14:05", "15:15", "16:05"];
    const periodEndTimes = ["08:35", "09:25", "10:30", "11:20", "12:20", "13:10", "14:05", "14:55", "16:05", "16:55"];
    
    for (let r = 0; r < 5; r++) {
        const rowVal = matrix[r];
        const rowEl = document.createElement("div");
        rowEl.className = "flex items-center";
        
        let cellsHtml = "";
        for (let c = 0; c < 10; c++) {
            const val = rowVal[c];
            
            let colorClass = "bg-[#161b22] border border-[#21262d]";
            if (val > 0) {
                if (val <= 1.0) {
                    colorClass = "bg-[#0e4429] border border-emerald-950/20";
                } else if (val <= 3.0) {
                    colorClass = "bg-[#006d32] border border-emerald-900/20";
                } else if (val <= 5.0) {
                    colorClass = "bg-[#26a641] border border-emerald-800/20";
                } else {
                    colorClass = "bg-[#39d353] border border-emerald-700/20";
                }
            }
            
            const tooltip = `${dayNames[r]} Period ${c + 1} (${periodStartTimes[c]} - ${periodEndTimes[c]}): ${val.toFixed(1)} periods missed`;
            
            cellsHtml += `
                <div class="h-8 rounded-[3px] ${colorClass} transition duration-100 hover:scale-105 cursor-pointer relative group flex items-center justify-center">
                    <span class="text-[9px] font-bold font-mono text-github-muted/80 group-hover:text-github-header select-none">${val > 0 ? val.toFixed(1) : ''}</span>
                    <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-[#21262d] border border-[#30363d] text-[#f0f6fc] text-[10px] py-1.5 px-2.5 rounded-md whitespace-nowrap z-50 font-mono shadow-xl pointer-events-none">
                        ${tooltip}
                    </div>
                </div>
            `;
        }
        
        rowEl.innerHTML = `
            <div class="w-16 text-xs text-github-muted font-bold font-mono select-none">${dayShortNames[r]}</div>
            <div class="grid grid-cols-10 gap-2 flex-grow">
                ${cellsHtml}
            </div>
        `;
        container.appendChild(rowEl);
    }
}
