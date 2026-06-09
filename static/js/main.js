// tryb ciemny
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    
    const btn = document.querySelector('.theme-toggle');
    btn.textContent = next === 'dark' ? 'Tryb jasny' : 'Tryb ciemny';
}

document.addEventListener('DOMContentLoaded', function() {
    const saved = localStorage.getItem('theme');
    const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = saved || system;
    
    document.documentElement.setAttribute('data-theme', theme);
    
    const btn = document.querySelector('.theme-toggle');
    btn.textContent = theme === 'dark' ? 'Tryb jasny' : 'Tryb ciemny';
});

function toggleMenu(header) {
    header.classList.toggle('open');
    const items = header.nextElementSibling;
    items.classList.toggle('open');
}

function toggleSubMenu(header) {
    header.classList.toggle('open');
    const items = header.nextElementSibling;
    items.classList.toggle('open');
}

function toggleKolumny() {
    const panel = document.getElementById('panel-kolumn');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('change', function(e) {
    if (e.target.classList.contains('col-toggle')) {
        const col = parseInt(e.target.getAttribute('data-col'));
        const table = document.getElementById('tabela-pojazdow');
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.children;
            if (cells[col]) {
                cells[col].style.display = e.target.checked ? '' : 'none';
            }
        });
    }
});

