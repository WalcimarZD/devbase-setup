// DevBase Dashboard Charts

let activityChart = null;
let typeChart = null;

// Colors matching our CSS variables
const colors = {
    primary: '#6366f1',
    secondary: '#0ea5e9',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    purple: '#8b5cf6',
    textSecondary: '#94a3b8',
    border: '#334155'
};

const typeColors = {
    'work': colors.primary,
    'meeting': colors.warning,
    'bugfix': colors.danger,
    'feature': colors.success,
    'learning': colors.secondary,
    'review': colors.purple,
    'unknown': colors.textSecondary
};

// Chart.js global configuration
Chart.defaults.color = colors.textSecondary;
Chart.defaults.borderColor = colors.border;

/**
 * Load statistics from API and update dashboard
 */
async function loadStats() {
    const days = document.getElementById('period').value;

    try {
        const response = await fetch(`/api/stats?days=${days}`);
        const data = await response.json();

        updateKPIs(data, days);
        updateActivityChart(data.by_date);
        updateTypeChart(data.by_type);
        updateRecentActivity(data.recent);

    } catch (error) {
        console.error('Error loading stats:', error);
        showError();
    }
}

/**
 * Update KPI cards with statistics
 */
function updateKPIs(data, days) {
    // Total activities
    document.getElementById('total-activities').textContent = data.total;

    // Average per day
    const avg = data.total > 0 ? (data.total / parseInt(days)).toFixed(1) : 0;
    document.getElementById('avg-per-day').textContent = avg;

    // Most active type
    const types = Object.entries(data.by_type);
    if (types.length > 0) {
        const topType = types.sort((a, b) => b[1] - a[1])[0][0];
        document.getElementById('most-active-type').textContent = topType;
    } else {
        document.getElementById('most-active-type').textContent = '-';
    }

    // Active days (streak)
    const activeDays = Object.keys(data.by_date.labels || {}).length;
    document.getElementById('streak').textContent = activeDays;
}

/**
 * Update or create the activity line chart
 */
function updateActivityChart(byDate) {
    const ctx = document.getElementById('activityChart').getContext('2d');

    const chartData = {
        labels: byDate.labels || [],
        datasets: [{
            label: 'Atividades',
            data: byDate.values || [],
            borderColor: colors.primary,
            backgroundColor: colors.primary + '20',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: colors.primary,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: '#1e293b',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: colors.border,
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    maxRotation: 45,
                    minRotation: 45
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: colors.border
                },
                ticks: {
                    stepSize: 1
                }
            }
        }
    };

    if (activityChart) {
        activityChart.data = chartData;
        activityChart.update();
    } else {
        activityChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: options
        });
    }
}

/**
 * Update or create the type distribution doughnut chart
 */
function updateTypeChart(byType) {
    const ctx = document.getElementById('typeChart').getContext('2d');

    const labels = Object.keys(byType);
    const values = Object.values(byType);
    const backgroundColors = labels.map(type => typeColors[type] || typeColors.unknown);

    const chartData = {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: backgroundColors,
            borderColor: '#0f172a',
            borderWidth: 3,
            hoverBorderWidth: 0
        }]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 20,
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            },
            tooltip: {
                backgroundColor: '#1e293b',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: colors.border,
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12
            }
        },
        cutout: '60%'
    };

    if (typeChart) {
        typeChart.data = chartData;
        typeChart.update();
    } else {
        typeChart = new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: options
        });
    }
}

/**
 * Update the recent activity list
 */
function updateRecentActivity(recent) {
    const container = document.getElementById('activity-list');

    if (!recent || recent.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>Nenhuma atividade registrada ainda.</p>
                <p>Use <code>devbase track "sua mensagem"</code> para começar.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recent.map(event => {
        const type = event.type || 'work';
        const message = event.message || '';
        const timestamp = formatTimestamp(event.timestamp);

        return `
            <div class="activity-item">
                <span class="activity-type ${type}">${type}</span>
                <span class="activity-message">${escapeHtml(message)}</span>
                <span class="activity-time">${timestamp}</span>
            </div>
        `;
    }).join('');
}

/**
 * Format timestamp for display
 */
function formatTimestamp(ts) {
    if (!ts) return '';

    const date = new Date(ts);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'agora';
    if (diffMins < 60) return `${diffMins}m atrás`;
    if (diffHours < 24) return `${diffHours}h atrás`;
    if (diffDays < 7) return `${diffDays}d atrás`;

    return date.toLocaleDateString('pt-BR');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show error state
 */
function showError() {
    document.getElementById('activity-list').innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <p>Erro ao carregar dados.</p>
        </div>
    `;
}

// Initial load
document.addEventListener('DOMContentLoaded', loadStats);
