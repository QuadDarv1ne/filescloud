document.addEventListener('DOMContentLoaded', function() {
    // Инициализация компонентов
    initDeleteButtons();
    initUploadModal();
    initThemeSwitcher();
    initTooltips();
});

// Обработчики удаления файлов
function initDeleteButtons() {
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            if (!confirm('Вы уверены, что хотите удалить этот файл?')) {
                e.preventDefault();
            }
        });
    });
}

// Управление модальным окном загрузки
function initUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (!modal) return;

    const form = modal.querySelector('form');
    const fileInput = modal.querySelector('input[type="file"]');
    
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0]?.name || 'Файл не выбран';
        modal.querySelector('.file-name').textContent = fileName;
    });

    form.addEventListener('submit', function(e) {
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Загрузка...';
    });
}

// Переключение темы
function initThemeSwitcher() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// Инициализация всплывающих подсказок
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(t => new bootstrap.Tooltip(t));
}

// Drag & Drop для загрузки
function initDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('fileInput').files = files;
        }
    });
}

// Динамическое обновление файлового списка
async function refreshFileList() {
    try {
        const response = await fetch('/api/files');
        const files = await response.json();
        renderFileList(files);
    } catch (error) {
        console.error('Ошибка обновления списка:', error);
    }
}

// Валидация форм
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            this.classList.add('was-validated');
        }
    }, false);
});

// Улучшенная обработка модальных окон
document.addEventListener('DOMContentLoaded', () => {
    // Инициализация тултипов
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    
    // Обработка копирования ссылки
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const target = document.querySelector(this.dataset.target)
            navigator.clipboard.writeText(target.value)
            
            // Показ уведомления
            const toast = new bootstrap.Toast(document.getElementById('copyToast'))
            toast.show()
        })
    })
})