// /app/static/dashboard.js

// (全局) 存储状态
let currentCart = []; // 购物车
let currentRestaurantId = null; // 当前正在点餐的餐厅ID
let currentUserId = localStorage.getItem('user_id'); // 从 localStorage 获取登录用户ID

// DOM 元素
const restaurantListEl = document.getElementById('restaurant-list');
const modalEl = document.getElementById('dishes-modal');
const modalCloseBtn = document.querySelector('.modal-close-btn');
const modalRestaurantNameEl = document.getElementById('modal-restaurant-name');
const modalDishesListEl = document.getElementById('modal-dishes-list');
const cartItemsEl = document.getElementById('cart-items');
const cartTotalEl = document.getElementById('cart-total'); // 【修改】这个现在是“最终总价”
const placeOrderBtn = document.getElementById('place-order-btn');
const logoutBtn = document.getElementById('logout-btn');
const usernameDisplayEl = document.getElementById('username-display');
const finalPriceMsgEl = document.getElementById('final-price-msg'); 
const kmeansBtn = document.getElementById('run-kmeans-btn'); // <-- 【新增此行】

// --- 1. 页面加载时执行 ---
document.addEventListener('DOMContentLoaded', () => {
    if (!currentUserId) {
        alert('请先登录！');
        window.location.href = '/'; 
        return;
    }
    usernameDisplayEl.textContent = localStorage.getItem('username') || '用户';
    loadRestaurants(); // 【修改】加载带图片的餐厅
    modalCloseBtn.addEventListener('click', () => modalEl.style.display = 'none');
    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = '/';
    });

    placeOrderBtn.addEventListener('click', handlePlaceOrder);
    kmeansBtn.addEventListener('click', handleRunKmeans);

});

// --- 2. 【修改】加载所有餐厅 (以显示图片) ---
async function loadRestaurants() {
    try {
        const response = await fetch('/api/restaurants');
        if (!response.ok) throw new Error('无法获取餐厅列表');
        
        const restaurants = await response.json();
        restaurantListEl.innerHTML = ''; 
        
        restaurants.forEach(r => {
            const card = document.createElement('div');
            card.className = 'card restaurant-card';
            
            // 【新增】餐厅图片
            card.innerHTML = `
                <img src="${r.image_url || 'https://placehold.co/400x200/eee/ccc?text=暂无图片'}" alt="${r.name}" class="restaurant-image">
                <div class="restaurant-info">
                    <h3>${r.name}</h3>
                    <p>${r.location || '暂无描述'}</p>
                </div>
            `;
            card.addEventListener('click', () => showDishesModal(r.id, r.name));
            restaurantListEl.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        restaurantListEl.innerHTML = '<p>加载餐厅失败</p>';
    }
}

// --- 3. 【核心重构】显示菜品弹窗 (调用智能 API) ---
async function showDishesModal(restaurantId, restaurantName) {
    if (currentRestaurantId !== null && currentRestaurantId !== restaurantId) {
        if (currentCart.length > 0 && !confirm('您正在从一家新餐厅点餐，这会清空您当前的购物车。确定吗？')) {
            return;
        }
        currentCart = [];
        updateCart(); // 清空购物车
    }
    
    currentRestaurantId = restaurantId; 
    
    modalRestaurantNameEl.textContent = restaurantName;
    modalDishesListEl.innerHTML = '<p>加载中...</p>';
    modalEl.style.display = 'flex'; 

    logBehavior('view_restaurant', restaurantId);

    try {
        // 【修改】调用“智能 API”，必须附带 user_id
        const response = await fetch(`/api/restaurant/${restaurantId}/dishes?user_id=${currentUserId}`);
        
        if (!response.ok) throw new Error('无法获取菜品');
        
        const dishes = await response.json(); // (现在返回的是带最终价格的列表)
        modalDishesListEl.innerHTML = ''; 
        
        dishes.forEach(d => {
            const item = document.createElement('div');
            item.className = 'dish-item';
            
            // 【新增】检查是否有折扣 (原价 != 最终价)
            const hasDiscount = d.base_price !== d.final_price;
            
            // 【修改】构建“划线价” HTML 结构
            item.innerHTML = `
                <img src="${d.image_url || 'https://placehold.co/100x100/eee/ccc?text=?'}" alt="${d.name}" class="dish-image">
                <div class="dish-info">
                    <span class="dish-name">${d.name}</span>
                    <div class="dish-price-wrapper">
                        <span class="dish-final-price">￥${d.final_price.toFixed(2)}</span>
                        
                        ${hasDiscount ? `
                            <span class="dish-base-price">￥${d.base_price.toFixed(2)}</span>
                            <span class="dish-discount-label">${d.discount_label}</span>
                        ` : ''}
                    </div>
                </div>
                <button class="btn-add-to-cart" 
                    data-id="${d.id}" 
                    data-name="${d.name}" 
                    data-final-price="${d.final_price}" 
                    data-base-price="${d.base_price}"
                >添加</button>
            `;
            
            // 绑定“添加”按钮事件
            item.querySelector('.btn-add-to-cart').addEventListener('click', (e) => {
                const dishData = e.target.dataset;
                addToCart(
                    dishData.id, 
                    dishData.name, 
                    parseFloat(dishData.finalPrice), // 【修改】传入 finalPrice
                    parseFloat(dishData.basePrice)
                );
            });
            modalDishesListEl.appendChild(item);
        });

    } catch (error) {
        console.error(error);
        modalDishesListEl.innerHTML = '<p>加载菜品失败</p>';
    }
}

// --- 4. 【修改】添加到购物车 (存入 final_price) ---
function addToCart(dishId, dishName, finalPrice, basePrice) {
    currentCart.push({
        dish_id: dishId,
        name: dishName,
        final_price: finalPrice, // 【修改】存最终价
        base_price: basePrice  // (可选) 存原价用于显示
    });
    updateCart();
}

// --- 5. 【修改】更新购物车 UI (累加 final_price) ---
function updateCart() {
    cartItemsEl.innerHTML = '';
    finalPriceMsgEl.textContent = ''; 
    
    if (currentCart.length === 0) {
        cartItemsEl.innerHTML = '<li>购物车是空的</li>';
        cartTotalEl.textContent = '￥0.00'; // 【修改】总价标签
        placeOrderBtn.disabled = true;
        return;
    }

    let total = 0;
    currentCart.forEach(item => {
        const li = document.createElement('li');
        // (显示最终价)
        li.innerHTML = `
            <span>${item.name}</span>
            <strong>￥${item.final_price.toFixed(2)}</strong>
        `;
        cartItemsEl.appendChild(li);
        total += item.final_price; // 【修改】累加最终价
    });

    cartTotalEl.textContent = `￥${total.toFixed(2)}`; // 【修改】总价标签
    placeOrderBtn.disabled = false;
}

// --- 6. 【修改】处理下单 (逻辑简化) ---
// (这个函数现在变得更简单了, 因为价格计算已在前端完成)
async function handlePlaceOrder() {
    if (currentCart.length === 0) return;

    placeOrderBtn.disabled = true;
    placeOrderBtn.textContent = '处理中...';
    finalPriceMsgEl.textContent = '';

    // 【修改】我们现在只发送 ID 列表
    // 后端 API (`order_api.py`) 仍然会重新计算一次价格,
    // 这是为了“安全校验”, 防止恶意用户在前端篡改价格。
    // (我们的后端 `create_order` API 已经是这样设计的, 所以它不需要改动!)
    const orderData = {
        user_id: parseInt(currentUserId),
        restaurant_id: currentRestaurantId,
        dish_ids: currentCart.map(item => parseInt(item.dish_id)) 
    };

    try {
        const response = await fetch('/api/order/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();

        if (response.ok) {
            // (显示后端返回的最终校验结果)
            finalPriceMsgEl.style.color = '#28a745';
            finalPriceMsgEl.innerHTML = `
                下单成功! 
                (您是 Level ${result.price_level_used} 用户, 享受 ${result.discount_applied.toFixed(2)} 折扣) <br>
                <strong>后端校验总价: ￥${result.total_price.toFixed(2)}</strong>
            `;
            
            currentCart = [];
            updateCart();
        } else {
            finalPriceMsgEl.style.color = 'red';
            finalPriceMsgEl.textContent = `下单失败: ${result.error}`;
        }

    } catch (error) {
        finalPriceMsgEl.style.color = 'red';
        finalPriceMsgEl.textContent = `请求出错: ${error}`;
    } finally {
        placeOrderBtn.disabled = false;
        placeOrderBtn.textContent = '立即下单';
    }
}

// --- 7. 记录行为 (不变) ---
async function logBehavior(actionType, restaurantId) {
    try {
        await fetch('/api/log/behavior', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: parseInt(currentUserId),
                restaurant_id: restaurantId,
                action_type: actionType
            })
        });
    } catch (error) {
        console.error('Log behavior failed:', error);
    }
}
async function handleRunKmeans() {
    // 1. 禁用按钮, 提供反馈
    kmeansBtn.disabled = true;
    kmeansBtn.textContent = '运行中...';
    
    // (用户端我们用 alert，或者您可以创建一个状态栏)
    alert('正在后台运行 K-Means 聚类... 这可能需要几秒钟。');

    try {
        const response = await fetch('/api/admin/run_kmeans', {
            method: 'POST'
        });
        
        const result = await response.json();

        if (response.ok && result.success) {
            alert(result.message); // "K-Means 运行完毕！..."
        } else {
            throw new Error(result.error || 'K-Means 运行失败');
        }

    } catch (error) {
        console.error(error);
        alert(`运行出错: ${error.message}`);
    } finally {
        // 5. 无论成功失败, 恢复按钮
        kmeansBtn.disabled = false;
        kmeansBtn.textContent = '🖌️ 运行K-Means';
    }
}