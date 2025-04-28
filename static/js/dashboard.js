/**
 * Dashboard charts and analytics for Virtual Internship Simulator
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard charts
    initializeAdminCharts();
    
    // Initialize user dashboard charts
    initializeUserProgressChart();
    
    // Handle tasks filter on admin dashboard
    initializeTasksFilter();
});

/**
 * Initialize charts for admin dashboard
 */
function initializeAdminCharts() {
    // Industry Distribution Chart
    const industryChartEl = document.getElementById('industryDistributionChart');
    if (industryChartEl) {
        // Get data from data attributes
        const industryNames = JSON.parse(industryChartEl.dataset.names || '[]');
        const industryCounts = JSON.parse(industryChartEl.dataset.counts || '[]');
        
        const industryChart = new Chart(industryChartEl, {
            type: 'pie',
            data: {
                labels: industryNames,
                datasets: [{
                    data: industryCounts,
                    backgroundColor: [
                        '#4e73df',
                        '#1cc88a',
                        '#36b9cc',
                        '#f6c23e',
                        '#e74a3b'
                    ],
                    hoverBackgroundColor: [
                        '#2e59d9',
                        '#17a673',
                        '#2c9faf',
                        '#dda20a',
                        '#be2617'
                    ],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                tooltips: {
                    backgroundColor: "rgb(255,255,255)",
                    bodyFontColor: "#858796",
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    xPadding: 15,
                    yPadding: 15,
                    displayColors: false,
                    caretPadding: 10,
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                cutoutPercentage: 70,
            },
        });
    }
    
    // Task Status Chart
    const taskChartEl = document.getElementById('taskStatusChart');
    if (taskChartEl) {
        // Get data from data attributes
        const taskStatuses = JSON.parse(taskChartEl.dataset.statuses || '[]');
        const taskCounts = JSON.parse(taskChartEl.dataset.counts || '[]');
        
        const taskChart = new Chart(taskChartEl, {
            type: 'bar',
            data: {
                labels: taskStatuses.map(status => status.charAt(0).toUpperCase() + status.slice(1)),
                datasets: [{
                    label: 'Tasks',
                    data: taskCounts,
                    backgroundColor: '#4e73df',
                    borderColor: '#4e73df',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            stepSize: 1
                        }
                    }]
                }
            }
        });
    }
    
    // User Growth Chart
    const userGrowthChartEl = document.getElementById('userGrowthChart');
    if (userGrowthChartEl) {
        // Get data from data attributes
        const months = JSON.parse(userGrowthChartEl.dataset.months || '[]');
        const userCounts = JSON.parse(userGrowthChartEl.dataset.counts || '[]');
        
        const userGrowthChart = new Chart(userGrowthChartEl, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Users',
                    data: userCounts,
                    lineTension: 0.3,
                    backgroundColor: "rgba(78, 115, 223, 0.05)",
                    borderColor: "rgba(78, 115, 223, 1)",
                    pointRadius: 3,
                    pointBackgroundColor: "rgba(78, 115, 223, 1)",
                    pointBorderColor: "rgba(78, 115, 223, 1)",
                    pointHoverRadius: 3,
                    pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
                    pointHoverBorderColor: "rgba(78, 115, 223, 1)",
                    pointHitRadius: 10,
                    pointBorderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    xAxes: [{
                        gridLines: {
                            display: false,
                            drawBorder: false
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            stepSize: 5
                        }
                    }]
                },
                legend: {
                    display: false
                }
            }
        });
    }
}

/**
 * Initialize progress chart for user dashboard
 */
function initializeUserProgressChart() {
    const progressChartEl = document.getElementById('userProgressChart');
    if (progressChartEl) {
        // Get data from data attributes
        const weeks = JSON.parse(progressChartEl.dataset.weeks || '[]');
        const progress = JSON.parse(progressChartEl.dataset.progress || '[]');
        
        const progressChart = new Chart(progressChartEl, {
            type: 'line',
            data: {
                labels: weeks,
                datasets: [{
                    label: 'Task Completion',
                    data: progress,
                    backgroundColor: "rgba(28, 200, 138, 0.1)",
                    borderColor: "rgba(28, 200, 138, 1)",
                    pointBackgroundColor: "rgba(28, 200, 138, 1)",
                    pointBorderColor: "rgba(28, 200, 138, 1)",
                    pointHoverRadius: 3,
                    pointHoverBackgroundColor: "rgba(28, 200, 138, 1)",
                    pointHoverBorderColor: "rgba(28, 200, 138, 1)",
                    pointHitRadius: 10,
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    xAxes: [{
                        gridLines: {
                            color: "rgb(234, 236, 244)",
                            zeroLineColor: "rgb(234, 236, 244)",
                            drawBorder: false,
                            drawTicks: false,
                            borderDash: [2],
                            zeroLineBorderDash: [2],
                            drawOnChartArea: false
                        },
                        ticks: {
                            padding: 20
                        }
                    }],
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            max: 100,
                            stepSize: 20,
                            padding: 20
                        }
                    }]
                }
            }
        });
    }
}

/**
 * Initialize tasks filter functionality
 */
function initializeTasksFilter() {
    const taskFilterSelect = document.getElementById('task-filter');
    if (taskFilterSelect) {
        taskFilterSelect.addEventListener('change', function() {
            const status = this.value;
            const tasks = document.querySelectorAll('.task-item');
            
            tasks.forEach(task => {
                const taskStatus = task.dataset.status;
                if (status === 'all' || taskStatus === status) {
                    task.style.display = 'block';
                } else {
                    task.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Update real-time stats for admin dashboard
 */
function updateRealTimeStats() {
    const statsContainer = document.getElementById('real-time-stats');
    if (!statsContainer) return;
    
    // In a real implementation, this would call an API endpoint
    // For demo purposes, we'll just simulate updates with random data
    setInterval(() => {
        const activeUsers = document.getElementById('active-users-count');
        if (activeUsers) {
            const currentCount = parseInt(activeUsers.textContent);
            // Random fluctuation between -2 and +2
            const newCount = Math.max(0, currentCount + Math.floor(Math.random() * 5) - 2);
            activeUsers.textContent = newCount;
        }
        
        const taskSubmissions = document.getElementById('task-submissions-count');
        if (taskSubmissions) {
            const currentCount = parseInt(taskSubmissions.textContent);
            // Add between 0 and 3 new submissions
            const newCount = currentCount + Math.floor(Math.random() * 4);
            taskSubmissions.textContent = newCount;
        }
    }, 5000); // Update every 5 seconds
}

// Start real-time stats updates if on admin dashboard
if (document.getElementById('real-time-stats')) {
    updateRealTimeStats();
}
