// /app/static/app.js

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. 选项卡切换逻辑 (不变) ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const formPanels = document.querySelectorAll('.form-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            const targetId = button.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);
            formPanels.forEach(panel => panel.classList.remove('active'));
            targetPanel.classList.add('active');
        });
    });

    // --- 2. 登录 API 逻辑 (不变) ---
    const userLoginForm = document.getElementById('user-login-form');
    userLoginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        const username = e.target.username.value;
        const password = e.target.password.value;
        try {
            const response = await fetch('/api/user/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('username', data.username);
                window.location.href = '/dashboard'; 
            } else {
                alert(`登录失败: ${data.error}`);
            }
        } catch (error) {
            alert(`登录请求出错: ${error}`);
        }
    });

    const merchantLoginForm = document.getElementById('merchant-login-form');
    merchantLoginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = e.target.username.value;
        const password = e.target.password.value;
        try {
            const response = await fetch('/api/restaurant/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('restaurant_id', data.restaurant_id);
                localStorage.setItem('restaurant_name', data.name);
                window.location.href = '/merchant_dashboard'; 
            } else {
                alert(`登录失败: ${data.error}`);
            }
        } catch (error) {
            alert(`登录请求出错: ${error}`);
        }
    });

    // --- 3. 【新增】注册 API 逻辑 ---

    // (A) 用户注册
    const userRegisterForm = document.getElementById('user-register-form');
    userRegisterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = e.target.username.value;
        const password = e.target.password.value;
        const area = e.target.area.value;
        
        try {
            const response = await fetch('/api/user/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, area })
            });
            const data = await response.json();
            if (response.ok) {
                alert('用户注册成功！请前往“用户登录”选项卡登录。');
                // (可选) 自动切换回登录
                // document.querySelector('.tab-btn[data-target="user-login"]').click();
            } else {
                alert(`注册失败: ${data.error}`);
            }
        } catch (error) {
            alert(`注册请求出错: ${error}`);
        }
    });

    // (B) 商家注册
    const merchantRegisterForm = document.getElementById('merchant-register-form');
    merchantRegisterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = e.target.username.value;
        const password = e.target.password.value;
        const name = e.target.name.value;
        const location = e.target.location.value;
        
        try {
            const response = await fetch('/api/restaurant/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, name, location })
            });
            const data = await response.json();
            if (response.ok) {
                alert('商家注册成功！请前往“商家登录”选项卡登录。');
            } else {
                alert(`注册失败: ${data.error}`);
            }
        } catch (error) {
            alert(`注册请求出错: ${error}`);
        }
    });

});