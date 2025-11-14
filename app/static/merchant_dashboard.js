// /app/static/merchant_dashboard.js

// (全局) 状态
let currentRestaurantId = localStorage.getItem('restaurant_id');

// DOM 元素
const merchantNameDisplayEl = document.getElementById('merchant-name-display');
const logoutBtn = document.getElementById('logout-btn');
const discountForm = document.getElementById('discount-form');
const saveStatusEl = document.getElementById('save-status');
const inputFields = document.querySelectorAll('.form-input[data-level]');
const kmeansBtn = document.getElementById('run-kmeans-btn'); // <-- 【新增此行】
const pendingOrdersListEl = document.getElementById('pending-orders-list');
// --- 1. 页面加载时执行 ---
document.addEventListener('DOMContentLoaded', () => {
    // (简易安全检查) 检查是否登录
    if (!currentRestaurantId) {
        alert('请先以商家身份登录！');
        window.location.href = '/'; // 跳回登录页
        return;
    }

    // 设置欢迎语
    merchantNameDisplayEl.textContent = localStorage.getItem('restaurant_name') || '商家';
    
    // 加载当前折扣规则
    loadDiscountRules();

    // 绑定退出登录
    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });
    
    // 绑定表单提交事件
    discountForm.addEventListener('submit', handleSaveRules);
    
    // 【新增】绑定 K-Means 按钮事件
    kmeansBtn.addEventListener('click', handleRunKmeans);
    loadPendingOrders(); // 1. 立即加载一次
    setInterval(loadPendingOrders, 10000); // 2. 之后每 10 秒刷新一次
});

// --- 2. 加载当前折扣规则 ---
async function loadDiscountRules() {
    saveStatusEl.textContent = '加载当前规则...';
    try {
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/rules`);
        if (!response.ok) {
            throw new Error('无法获取规则');
        }
        
        const rules = await response.json(); // [ {PriceLevel: 1, Discount: 0.8}, ... ]
        
        // 将数据填充到输入框
        inputFields.forEach(input => {
            const level = parseInt(input.dataset.level);
            const rule = rules.find(r => r.PriceLevel === level);
            if (rule) {
                input.value = rule.Discount.toFixed(2); // 保留两位小数
            } else {
                input.value = 1.00; // 默认值
            }
        });
        saveStatusEl.textContent = '规则加载完毕。';
        
    } catch (error) {
        console.error(error);
        saveStatusEl.style.color = 'red';
        saveStatusEl.textContent = `加载失败: ${error.message}`;
    }
}

// --- 3. 保存新规则 (调用 POST API) ---
async function handleSaveRules(e) {
    e.preventDefault(); // 阻止表单默认提交
    saveStatusEl.textContent = '保存中...';
    saveStatusEl.style.color = '#333';

    // 1. 从表单收集数据, 构造成 API 需要的格式
    let rulesPayload = [];
    try {
        inputFields.forEach(input => {
            const level = parseInt(input.dataset.level);
            const discount = parseFloat(input.value);
            
            if (isNaN(discount) || discount <= 0) {
                // 抛出错误, 终止执行
                throw new Error(`Level ${level} 的折扣值无效`);
            }
            
            rulesPayload.push({
                "PriceLevel": level,
                "Discount": discount
            });
        });
    } catch (error) {
        saveStatusEl.style.color = 'red';
        saveStatusEl.textContent = error.message;
        return;
    }

    // 2. 发送 POST 请求
    try {
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rulesPayload) // 发送: [ {PriceLevel: 1, Discount: 0.9}, ... ]
        });
        
        const result = await response.json();

        if (response.ok) {
            saveStatusEl.style.color = 'green';
            saveStatusEl.textContent = result.message || '保存成功!';
        } else {
            throw new Error(result.error || '未知错误');
        }
    } catch (error) {
        console.error(error);
        saveStatusEl.style.color = 'red';
        saveStatusEl.textContent = `保存失败: ${error.message}`;
    }
}

async function handleRunKmeans() {
    // 1. 禁用按钮, 提供反馈
    kmeansBtn.disabled = true;
    kmeansBtn.textContent = '运行中...';
    saveStatusEl.textContent = '正在后台运行 K-Means 聚类...';
    saveStatusEl.style.color = '#333';

    try {
        const response = await fetch('/api/admin/run_kmeans', {
            method: 'POST'
        });
        
        const result = await response.json();

        if (response.ok && result.success) {
            saveStatusEl.style.color = 'green';
            saveStatusEl.textContent = result.message; // "K-Means 运行完毕！..."
        } else {
            throw new Error(result.error || 'K-Means 运行失败');
        }

    } catch (error) {
        console.error(error);
        saveStatusEl.style.color = 'red';
        saveStatusEl.textContent = `运行出错: ${error.message}`;
    } finally {
        // 5. 无论成功失败, 恢复按钮
        kmeansBtn.disabled = false;
        kmeansBtn.textContent = '🖌️ 运行K-Means';
    }
}


// /app/static/merchant_dashboard.js

// ... (在 handleRunKmeans 函数之后) ...

// --- 5. 【新增】加载待处理订单 ---
async function loadPendingOrders() {
    if (!saveStatusEl.textContent.includes('K-Means')) {
        saveStatusEl.textContent = '正在刷新订单...';
    }

    try {
        // (注意) 这里的 API 调用现在应该成功了
        const response = await fetch(`/api/restaurant/${currentRestaurantId}/orders?status=Pending`);
        if (!response.ok) {
            // 如果还是 404, 可能是上面的 API 代码没保存或服务器没重启
            throw new Error(`无法获取订单 (HTTP ${response.status})`);
        }
        
        const orders = await response.json();
        pendingOrdersListEl.innerHTML = ''; 
        
        if (orders.length === 0) {
            pendingOrdersListEl.innerHTML = '<p>没有待处理的订单。</p>';
        }

        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-card';
            let itemsHtml = '<ul>';
            order.items.forEach(item => {
                itemsHtml += `<li>${item.dish_name} (x${item.quantity}) @ ￥${item.final_price_per_item.toFixed(2)}</li>`;
            });
            itemsHtml += '</ul>';

            card.innerHTML = `
                <div class="order-card-header">
                    <strong>订单 #${order.order_id} (来自: ${order.user_name})</strong>
                    <span>￥${order.total_price.toFixed(2)}</span>
                </div>
                <div class="order-card-body">
                    ${itemsHtml}
                </div>
                <div class="order-card-actions">
                    <button class="btn-confirm" data-order-id="${order.order_id}">
                        确认接单 (-> V)
                    </button>
                </div>
            `;
            
            card.querySelector('.btn-confirm').addEventListener('click', (e) => {
                const orderId = e.target.dataset.orderId;
                handleUpdateOrderStatus(orderId, 'Confirmed');
            });
            pendingOrdersListEl.appendChild(card);
        });

        if (!saveStatusEl.textContent.includes('K-Means')) {
             saveStatusEl.textContent = '订单已刷新。';
        }

    } catch (error) {
        console.error(error);
        pendingOrdersListEl.innerHTML = `<p style="color:red;">加载订单失败: ${error.message}</p>`;
    }
}

// --- 6. 【新增】处理订单状态更新 ---
async function handleUpdateOrderStatus(orderId, newStatus) {
    saveStatusEl.textContent = `正在更新订单 #${orderId}...`;
    saveStatusEl.style.color = '#333';

    try {
        const response = await fetch(`/api/order/${orderId}/update_status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error);
        
        saveStatusEl.style.color = 'green';
        saveStatusEl.textContent = `订单 #${orderId} 已更新为 ${newStatus}!`;
        loadPendingOrders(); // 立即刷新列表

    } catch (error) {
        console.error(error);
        saveStatusEl.style.color = 'red';
        saveStatusEl.textContent = `更新失败: ${error.message}`;
    }
}