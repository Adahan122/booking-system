// Анимации при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Плавное появление элементов
    const animatedElements = document.querySelectorAll('.fade-in-up');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });
    
    // Улучшение UX для форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Обработка...';
                submitBtn.disabled = true;
            }
        });
    });
    
    function updateTime() {
        const timeElements = document.querySelectorAll('.current-time');
        const now = new Date();
        timeElements.forEach(el => {
            el.textContent = now.toLocaleTimeString('ru-RU');
        });
    }
    
    setInterval(updateTime, 1000);
    updateTime();
});




