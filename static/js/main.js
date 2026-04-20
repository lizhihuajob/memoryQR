// 主 JavaScript 文件

document.addEventListener('DOMContentLoaded', function() {
    initMobileNav();
    initFlashMessages();
    initSmoothScroll();
});

// 移动端导航切换
function initMobileNav() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            
            // 切换汉堡菜单动画
            const spans = navToggle.querySelectorAll('span');
            if (navMenu.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
        
        // 点击链接关闭菜单
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                const spans = navToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });
    }
}

// Flash 消息自动消失
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // 5 秒后自动消失
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateX(20px)';
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 300);
        }, 5000);
    });
}

// 平滑滚动
function initSmoothScroll() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 工具函数：防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 工具函数：节流
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 表单验证工具
const FormValidator = {
    required(value, message = '此字段为必填项') {
        if (!value || value.trim() === '') {
            return message;
        }
        return null;
    },
    
    minLength(value, min, message = null) {
        if (value.length < min) {
            return message || `至少需要 ${min} 个字符`;
        }
        return null;
    },
    
    maxLength(value, max, message = null) {
        if (value.length > max) {
            return message || `最多 ${max} 个字符`;
        }
        return null;
    },
    
    email(value, message = '请输入有效的邮箱地址') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (value && !emailRegex.test(value)) {
            return message;
        }
        return null;
    },
    
    match(value, compareValue, message = '两次输入不一致') {
        if (value !== compareValue) {
            return message;
        }
        return null;
    }
};

// 文件上传预览
function setupFilePreview(inputElement, previewElement) {
    inputElement.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(event) {
                if (previewElement.tagName === 'IMG') {
                    previewElement.src = event.target.result;
                } else {
                    previewElement.style.backgroundImage = `url(${event.target.result})`;
                    previewElement.style.backgroundSize = 'cover';
                    previewElement.style.backgroundPosition = 'center';
                }
            };
            reader.readAsDataURL(file);
        }
    });
}

// 复制到剪贴板
async function copyToClipboard(text, successMessage = '已复制到剪贴板') {
    try {
        await navigator.clipboard.writeText(text);
        showToast(successMessage, 'success');
        return true;
    } catch (err) {
        console.error('复制失败:', err);
        showToast('复制失败，请手动复制', 'error');
        return false;
    }
}

// 显示提示消息
function showToast(message, type = 'info', duration = 3000) {
    // 检查是否已有 toast 容器
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }
    
    // 创建 toast
    const toast = document.createElement('div');
    toast.style.cssText = `
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: toastIn 0.3s ease;
        ${type === 'success' ? 'background: #28a745;' : ''}
        ${type === 'error' ? 'background: #dc3545;' : ''}
        ${type === 'warning' ? 'background: #ffc107; color: #333;' : ''}
        ${type === 'info' ? 'background: #17a2b8;' : ''}
    `;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // 添加动画样式
    if (!document.querySelector('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes toastIn {
                from { opacity: 0; transform: translateX(100px); }
                to { opacity: 1; transform: translateX(0); }
            }
            @keyframes toastOut {
                from { opacity: 1; transform: translateX(0); }
                to { opacity: 0; transform: translateX(100px); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // 自动消失
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, duration);
}

// 确认对话框
function confirmDialog(message, onConfirm, onCancel) {
    const result = window.confirm(message);
    if (result && onConfirm) {
        onConfirm();
    } else if (!result && onCancel) {
        onCancel();
    }
    return result;
}

// 导出公共函数
window.MemoryQR = {
    copyToClipboard,
    showToast,
    confirmDialog,
    debounce,
    throttle,
    FormValidator,
    setupFilePreview
};
