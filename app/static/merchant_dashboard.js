// /app/static/merchant_dashboard.js

let currentRestaurantId = localStorage.getItem('restaurant_id');

// DOM 元素
const merchantNameDisplayEl = document.getElementById('merchant-name-display');
const logoutBtn = document.getElementById('logout-btn');
const discountForm = document.getElementById('discount-form');
const saveStatusEl = document.getElementById('save-status');
const inputFields = document.querySelectorAll('.form-input[data-level]');
const kmeansBtn = document.getElementById('run-kmeans-btn');
// 两个订单列表容器
const pendingOrdersListEl = document.getElementById('pending-orders-list');
const processingOrdersListEl = document.getElementById('processing-orders-list');

// --- 1. 页面加载 ---
document.addEventListener('DOMContentLoaded', () => {
    if (!currentRestaurantId) {
        alert('请先登录！');
        window.location.href = '/'; 
        return;
    }
    merchantNameDisplayEl.textContent = localStorage.getItem('restaurant_name') || '商家';
    
    loadDiscountRules();
    initCharts(); // 【修改】现在加载真实图表

    // 绑定事件
    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });
    discountForm.addEventListener('submit', handleSaveRules);
    kmeansBtn.addEventListener('click', handleRunKmeans);

    // 轮询订单 (同时加载待处理和制作中)
    loadOrders();
    setInterval(loadOrders, 5000); // 5秒刷一次
});

// --- 2. 加载规则 (保持不变) ---
async function loadDiscountRules() {
    try {
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/rules`);
        if (!response.ok) throw new Error('无法获取规则');
        const rules = await response.json();
        inputFields.forEach(input => {
            const level = parseInt(input.dataset.level);
            const rule = rules.find(r => r.PriceLevel === level);
            input.value = rule ? rule.Discount.toFixed(2) : 1.00;
        });
    } catch (error) { console.error(error); }
}

// --- 3. 保存规则 (保持不变) ---
async function handleSaveRules(e) {
    e.preventDefault();
    saveStatusEl.textContent = '保存中...';
    // ... (此处逻辑与之前相同，为节省篇幅省略，若需要完整代码请说) ...
    // 简写版逻辑：
    try {
        let rulesPayload = [];
        inputFields.forEach(input => {
            rulesPayload.push({ "PriceLevel": parseInt(input.dataset.level), "Discount": parseFloat(input.value) });
        });
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rulesPayload)
        });
        if (response.ok) { saveStatusEl.textContent = '保存成功!'; saveStatusEl.style.color='green'; }
    } catch (err) { saveStatusEl.textContent = '保存失败'; }
}

// --- 4. K-Means (保持不变) ---
async function handleRunKmeans() {
    // ... (同之前) ...
    alert('正在后台计算...');
    await fetch('/api/admin/run_kmeans', { method: 'POST' });
    alert('计算完成，图表稍后将更新');
    initCharts(); // 重新加载图表
}

// --- 5. 【核心修改】加载订单 ( Pending & Confirmed ) ---
async function loadOrders() {
    // 并行获取两种状态的订单
    await Promise.all([
        fetchAndRenderOrders('Pending', pendingOrdersListEl),
        fetchAndRenderOrders('Confirmed', processingOrdersListEl)
    ]);
}

async function fetchAndRenderOrders(status, containerEl) {
    try {
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/orders?status=${status}`);
        if (!response.ok) return;
        const orders = await response.json();
        
        containerEl.innerHTML = '';
        if (orders.length === 0) {
            containerEl.innerHTML = '<p style="color:#666; font-size:14px;">暂无订单</p>';
            return;
        }

        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-card'; // 使用之前的样式
            card.style.background = '#fff'; // 覆盖背景色
            
            let itemsHtml = '<ul style="padding-left:20px; margin:5px 0;">';
            order.items.forEach(item => {
                itemsHtml += `<li>${item.dish_name} x${item.quantity}</li>`;
            });
            itemsHtml += '</ul>';

            // 根据状态决定按钮文字
            let actionBtnHtml = '';
            if (status === 'Pending') {
                actionBtnHtml = `<button class="btn-confirm" onclick="updateStatus(${order.order_id}, 'Confirmed')">接单</button>`;
            } else if (status === 'Confirmed') {
                actionBtnHtml = `<button class="btn-confirm" style="background:#17a2b8;" onclick="updateStatus(${order.order_id}, 'Completed')">完单 (出餐)</button>`;
            }

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; font-weight:bold; margin-bottom:5px;">
                    <span>#${order.order_id} ${order.user_name}</span>
                    <span style="color:red;">￥${order.total_price.toFixed(2)}</span>
                </div>
                ${itemsHtml}
                <div style="text-align:right; margin-top:10px;">
                    ${actionBtnHtml}
                </div>
            `;
            containerEl.appendChild(card);
        });
    } catch (error) {
        console.error(error);
    }
}

// --- 6. 更新订单状态 ---
async function updateStatus(orderId, newStatus) {
    if(!confirm(`确定要更新订单 #${orderId} 为 "${newStatus}" 吗?`)) return;
    
    try {
        await fetch(`/api/order/${orderId}/update_status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        loadOrders(); // 立即刷新
    } catch (e) { alert(e); }
}

// --- 7. 【核心修改】真实数据图表 ---
async function initCharts() {
    const chartDishesDom = document.getElementById('chart-top-dishes');
    const chartLevelsDom = document.getElementById('chart-user-levels');
    
    const myChartDishes = echarts.init(chartDishesDom);
    const myChartLevels = echarts.init(chartLevelsDom);

    // 1. 显示 Loading 动画
    myChartDishes.showLoading();
    myChartLevels.showLoading();

    try {
        // 2. 请求后端真实数据
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/stats`);
        const data = await response.json(); // { dishes_names: [], dishes_values: [], levels_data: [] }

        myChartDishes.hideLoading();
        myChartLevels.hideLoading();

        // 3. 配置图表 (使用 data 里的数据)
        const optionDishes = {
            title: { text: '🔥 销量 Top 5 (真实)', left: 'center', textStyle: { fontSize: 14 } },
            tooltip: { trigger: 'axis' },
            grid: { bottom: '10%', top: '20%', left: '10%', right: '5%' },
            xAxis: { type: 'category', data: data.dishes_names, axisLabel: { rotate: 20, interval: 0 } },
            yAxis: { type: 'value' },
            series: [{
                data: data.dishes_values,
                type: 'bar',
                itemStyle: { color: '#007bff' }
            }]
        };

        const optionLevels = {
            title: { text: '👥 用户等级分布', left: 'center', textStyle: { fontSize: 14 } },
            tooltip: { trigger: 'item' },
            legend: { bottom: 0, padding: 0, itemWidth: 10, itemHeight: 10, textStyle: {fontSize: 10} },
            series: [{
                name: '用户等级',
                type: 'pie',
                radius: ['30%', '60%'],
                center: ['50%', '45%'], // 稍微上移
                data: data.levels_data, // 使用后端返回的 level 数据
                itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 }
            }]
        };

        myChartDishes.setOption(optionDishes);
        myChartLevels.setOption(optionLevels);

    } catch (error) {
        console.error("图表加载失败:", error);
        myChartDishes.hideLoading();
    }
    
    window.addEventListener('resize', () => {
        myChartDishes.resize();
        myChartLevels.resize();
    });
}