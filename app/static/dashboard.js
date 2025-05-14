// 水质数据图表配置
const generateMockData = () => {
  const dates = Array.from({length:7}, (_,i) => {
    const d = new Date(Date.now() - (6-i)*86400000);
    return d.toISOString().split('T')[0];
  });
  return {
    dates,
    ph: dates.map(() => Math.random()*2 + 8.5),
    oxygen: dates.map(() => Math.random()*5 + 10),
    turbidity: dates.map(() => Math.random()*5 + 8)
  };
};

const initWaterQualityChart = (startDate, endDate) => {
    const data = generateMockData();
    
    new Chart(document.getElementById('waterQualityChart'), {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'pH值',
                data: data.ph,
                borderColor: '#4dc9f6',
                tension: 0.1
            },{
                label: '溶解氧',
                data: data.oxygen,
                borderColor: '#f67019',
                tension: 0.1
            },{
                label: '浊度',
                data: data.turbidity,
                borderColor: '#537bc4',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index' },
            scales: { y: { title: { display: true, text: '数值' } } }
        }
    });
};

// 初始化控制功能
const initChartControls = () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('startDate').value = new Date(Date.now() - 604800000).toISOString().split('T')[0];
    document.getElementById('endDate').value = today;

    document.getElementById('refreshChart').addEventListener('click', () => {
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        initWaterQualityChart(start, end);
    });

    document.getElementById('exportData').addEventListener('click', () => {
        const chart = Chart.getChart('waterQualityChart');
        if (chart) {
            const csvContent = '数据,日期,' + chart.data.labels.join(',') + '\n' +
                chart.data.datasets.map(d => `${d.label},${d.data.join(',')}`).join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `水质数据_${new Date().toISOString().slice(0,10)}.csv`;
            a.click();
        }
    });
};

// 初始化鱼类分布饼图
const initFishDistributionChart = () => {
    new Chart(document.getElementById('fishDistributionChart'), {
        type: 'pie',
        data: {
            labels: ['Bream', 'Roach', 'WhiteFish', 'Parkki', 'Perch', 'Smelt'],
            datasets: [{
                data: [35, 20, 6, 11, 73, 14],
                backgroundColor: ['#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236', '#8549ba']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
};

// 初始化视频控制功能
const initVideoControls = () => {
    const videoInput = document.getElementById('videoUpload');
    const videoPlayer = document.getElementById('localVideo');
    const playButton = document.getElementById('playVideo');

    videoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('video/')) {
            const url = URL.createObjectURL(file);
            videoPlayer.src = url;
            videoPlayer.style.display = 'block';
            document.querySelector('.video-placeholder').style.display = 'none';
        }
    });

    playButton.addEventListener('click', () => {
        if (videoPlayer.src) {
            videoPlayer.play();
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
        }
    });

    videoPlayer.addEventListener('play', () => {
        playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
    });

    videoPlayer.addEventListener('pause', () => {
        playButton.innerHTML = '<i class="bi bi-play-fill"></i>';
    });

    videoPlayer.loop = true;
};

// 初始化所有功能
initChartControls();
initVideoControls();
initWaterQualityChart(document.getElementById('startDate').value, document.getElementById('endDate').value);
initFishDistributionChart();