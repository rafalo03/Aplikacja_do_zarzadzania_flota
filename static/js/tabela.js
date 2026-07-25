/*
 * Wspolna mechanika tabel: filtry per kolumna, sortowanie, zmiana szerokosci,
 * panel kolumn (widocznosc + kolejnosc), zapisywane uklady per uzytkownik,
 * chipy filtrow, paginacja i eksport CSV.
 *
 * Uzycie: zwykla tabela .table z jednym wierszem naglowka, ostatnia kolumna
 * "Akcje" i ewentualna kolumna z checkboxem sa pomijane w filtrach/panelu.
 *
 *   <table class="table" id="tabela-marki">...</table>
 *   <script>initTabela({ tableId: 'tabela-marki', tabela: 'marki' });</script>
 */
(function() {
'use strict';

function getCookie(name) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]+)'));
    return m ? decodeURIComponent(m[1]) : '';
}

async function apiPost(url, data) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(data)
        });
        if (!res.ok) return null;
        return await res.json();
    } catch (e) {
        return null;
    }
}

window.toggleAll = function(cb) {
    const t = cb.closest('table');
    if (!t) return;
    t.querySelectorAll('tbody input[type="checkbox"]').forEach(c => { c.checked = cb.checked; });
};

const IKONA_LEJEK = '<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" aria-hidden="true"><path d="M4 4h16l-6.5 8v6l-3 1.5V12L4 4z"/></svg>';

window.initTabela = function(opts) {
    const table = document.getElementById(opts.tableId);
    if (!table || table.dataset.tabelaInit) return;
    table.dataset.tabelaInit = '1';

    const TABELA = opts.tabela;
    let perPage = 10;
    let currentPage = 1;
    const filterModes = {};
    let ukladyStore = { layouts: {}, active: null };
    let activeSortCol = null;
    let activeSortEl = null;
    let activeFilterCol = null;
    let activeFilterEl = null;
    let dragSrc = null;

    /* ---------- rozpoznanie kolumn ---------- */

    const headerRow = table.querySelector('thead tr');
    const ths = Array.from(headerRow.children);
    const colCount = ths.length;
    const origWidths = {};
    const kolumny = ths.map(function(th, i) {
        th.setAttribute('data-col', i);
        origWidths[String(i)] = th.style.width || '';
        const maCheckbox = !!th.querySelector('input[type="checkbox"]');
        const label = th.textContent.trim();
        return { col: String(i), label: label, konfigurowalna: !maCheckbox && label !== 'Akcje' };
    });
    const akcjeKol = (function() {
        for (let i = kolumny.length - 1; i >= 0; i--) {
            if (kolumny[i].label === 'Akcje') return kolumny[i].col;
        }
        return null;
    })();

    table.querySelectorAll('tbody tr').forEach(function(row) {
        if (row.children.length < colCount) return;
        Array.from(row.children).forEach(function(td, i) { td.setAttribute('data-col', i); });
    });

    /* ---------- naglowki: sortowanie po kliknieciu ---------- */

    kolumny.forEach(function(k, i) {
        if (!k.konfigurowalna) return;
        const th = ths[i];
        const span = document.createElement('span');
        span.className = 'th-name';
        span.textContent = k.label;
        th.textContent = '';
        th.appendChild(span);
        span.addEventListener('click', function() { openSortMenu(span, k.col); });
    });

    /* ---------- wiersz filtrow ---------- */

    const filtrRow = document.createElement('tr');
    filtrRow.className = 'filtr-row';
    kolumny.forEach(function(k) {
        const th = document.createElement('th');
        th.setAttribute('data-col', k.col);
        if (k.konfigurowalna) {
            const cell = document.createElement('div');
            cell.className = 'filtr-cell';
            const input = document.createElement('input');
            input.type = 'text';
            input.setAttribute('aria-label', 'Filtruj: ' + k.label);
            input.addEventListener('input', applyFilters);
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'filtr-btn';
            btn.title = 'Filtr';
            btn.innerHTML = IKONA_LEJEK;
            btn.addEventListener('click', function() { openFilterMenu(btn, k.col); });
            cell.appendChild(input);
            cell.appendChild(btn);
            th.appendChild(cell);
        }
        filtrRow.appendChild(th);
    });
    headerRow.parentNode.appendChild(filtrRow);

    /* ---------- pasek nad tabela + obszar z zakladkami ---------- */

    const card = table.closest('.card') || table.parentNode;

    const toolbar = document.createElement('div');
    toolbar.className = 'tabela-toolbar';
    const chipy = document.createElement('div');
    chipy.className = 'filtr-chipy';
    const configBtn = document.createElement('button');
    configBtn.type = 'button';
    configBtn.className = 'config-link';
    configBtn.innerHTML = 'Konfiguracja tabeli &#9662;';
    configBtn.addEventListener('click', toggleConfigMenu);
    toolbar.appendChild(chipy);
    toolbar.appendChild(configBtn);

    const obszar = document.createElement('div');
    obszar.style.cssText = 'position: relative; display: flex; gap: 0;';
    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';
    wrapper.style.cssText = 'flex: 1; min-width: 0; overflow-x: auto;';

    table.parentNode.insertBefore(toolbar, table);
    table.parentNode.insertBefore(obszar, table);
    wrapper.appendChild(table);
    obszar.appendChild(wrapper);

    const sideTabs = document.createElement('div');
    sideTabs.className = 'side-tabs';
    const tabKolumny = document.createElement('button');
    tabKolumny.type = 'button';
    tabKolumny.className = 'side-tab';
    tabKolumny.innerHTML = '&#9636; Kolumny';
    tabKolumny.addEventListener('click', function() {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
    const tabFiltry = document.createElement('button');
    tabFiltry.type = 'button';
    tabFiltry.className = 'side-tab';
    tabFiltry.innerHTML = '&#9662; Filtry';
    tabFiltry.addEventListener('click', function() {
        filtrRow.style.display = filtrRow.style.display === 'none' ? '' : 'none';
    });
    sideTabs.appendChild(tabKolumny);
    sideTabs.appendChild(tabFiltry);
    obszar.appendChild(sideTabs);

    /* ---------- panel kolumn ---------- */

    const panel = document.createElement('div');
    panel.className = 'kolumny-panel';
    panel.style.display = 'none';
    panel.innerHTML = '<div class="kolumny-header">Kolumny</div><div class="kolumny-info">Przeciągnij aby zmienić kolejność</div>';
    const lista = document.createElement('ul');
    lista.className = 'kolumny-lista';
    kolumny.forEach(function(k) {
        if (!k.konfigurowalna) return;
        const li = document.createElement('li');
        li.className = 'kolumny-item';
        li.setAttribute('data-col', k.col);
        li.draggable = true;
        const handle = document.createElement('span');
        handle.className = 'drag-handle';
        handle.innerHTML = '&#8942;&#8942;';
        const label = document.createElement('label');
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.addEventListener('change', function() { toggleKolumne(cb); });
        label.appendChild(cb);
        label.appendChild(document.createTextNode(' ' + k.label));
        li.appendChild(handle);
        li.appendChild(label);
        lista.appendChild(li);
    });
    panel.appendChild(lista);
    obszar.appendChild(panel);

    /* ---------- paginacja + przyciski stopki ---------- */

    const pagination = document.createElement('div');
    pagination.className = 'pagination';
    pagination.innerHTML =
        '<span>Rekordów na stronę:</span>' +
        '<select class="per-page-select"><option value="10">10</option><option value="25">25</option><option value="50">50</option><option value="100">100</option></select>' +
        '<span class="pg-info"></span>' +
        '<div class="pagination-controls">' +
        '<button class="pagination-btn pg-first" disabled>&#171;</button>' +
        '<button class="pagination-btn pg-prev" disabled>&#8249;</button>' +
        '<span class="pg-page"></span>' +
        '<button class="pagination-btn pg-next">&#8250;</button>' +
        '<button class="pagination-btn pg-last">&#187;</button>' +
        '</div>';
    obszar.parentNode.insertBefore(pagination, obszar.nextSibling);

    const infoEl = pagination.querySelector('.pg-info');
    const pageEl = pagination.querySelector('.pg-page');
    const btnFirst = pagination.querySelector('.pg-first');
    const btnPrev = pagination.querySelector('.pg-prev');
    const btnNext = pagination.querySelector('.pg-next');
    const btnLast = pagination.querySelector('.pg-last');
    pagination.querySelector('.per-page-select').addEventListener('change', function() {
        perPage = parseInt(this.value);
        currentPage = 1;
        renderPage();
    });
    btnFirst.addEventListener('click', function() { goPage('first'); });
    btnPrev.addEventListener('click', function() { goPage('prev'); });
    btnNext.addEventListener('click', function() { goPage('next'); });
    btnLast.addEventListener('click', function() { goPage('last'); });

    const footer = document.createElement('div');
    footer.className = 'table-footer-btns';
    const btnOdswiez = przyciskStopki('&#8635; Odśwież', function() { location.reload(); });
    const btnWyczysc = przyciskStopki('&#10005; Wyczyść filtry', wyczyscFiltry);
    const btnEksport = przyciskStopki('&#8681; Eksportuj', eksportujCSV);
    footer.appendChild(btnOdswiez);
    footer.appendChild(btnWyczysc);
    footer.appendChild(btnEksport);
    pagination.parentNode.insertBefore(footer, pagination.nextSibling);

    function przyciskStopki(html, akcja) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-secondary';
        b.innerHTML = html;
        b.addEventListener('click', akcja);
        return b;
    }

    /* ---------- dropdowny ---------- */

    const sortDropdown = document.createElement('div');
    sortDropdown.className = 'sort-dropdown';
    sortDropdown.style.display = 'none';
    [['asc-alpha', '&#8593; A do Z'], ['desc-alpha', '&#8595; Z do A'], null,
     ['asc-num', '&#8593; Rosnąco'], ['desc-num', '&#8595; Malejąco']].forEach(function(item) {
        if (!item) {
            const d = document.createElement('div');
            d.className = 'sort-divider';
            sortDropdown.appendChild(d);
            return;
        }
        const b = document.createElement('button');
        b.innerHTML = item[1];
        b.addEventListener('click', function() { sortTable(item[0]); });
        sortDropdown.appendChild(b);
    });
    card.appendChild(sortDropdown);

    const filterDropdown = document.createElement('div');
    filterDropdown.className = 'sort-dropdown';
    filterDropdown.style.display = 'none';
    [['contains', 'Zawiera'], ['equals', 'Równa się'], ['starts', 'Zaczyna się od'], ['ends', 'Kończy się na'], null, ['clear', 'Wyczyść filtr']].forEach(function(item) {
        if (!item) {
            const d = document.createElement('div');
            d.className = 'sort-divider';
            filterDropdown.appendChild(d);
            return;
        }
        const b = document.createElement('button');
        b.textContent = item[1];
        b.addEventListener('click', function() { setFilterMode(item[0]); });
        filterDropdown.appendChild(b);
    });
    card.appendChild(filterDropdown);

    const configDropdown = document.createElement('div');
    configDropdown.className = 'sort-dropdown config-dropdown';
    configDropdown.style.display = 'none';
    configDropdown.innerHTML = '<div class="config-title">Zapisane układy</div>';
    const ukladyLista = document.createElement('div');
    configDropdown.appendChild(ukladyLista);
    const divider = document.createElement('div');
    divider.className = 'sort-divider';
    configDropdown.appendChild(divider);
    const saveRow = document.createElement('div');
    saveRow.className = 'config-save-row';
    const nazwaInput = document.createElement('input');
    nazwaInput.type = 'text';
    nazwaInput.placeholder = 'Nazwa układu';
    nazwaInput.maxLength = 100;
    nazwaInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') zapiszUklad(); });
    const saveBtn = document.createElement('button');
    saveBtn.type = 'button';
    saveBtn.textContent = 'Zapisz';
    saveBtn.addEventListener('click', zapiszUklad);
    saveRow.appendChild(nazwaInput);
    saveRow.appendChild(saveBtn);
    configDropdown.appendChild(saveRow);
    const resetBtn = document.createElement('button');
    resetBtn.textContent = 'Resetuj do domyślnego';
    resetBtn.addEventListener('click', resetujUklad);
    configDropdown.appendChild(resetBtn);
    card.appendChild(configDropdown);

    function positionDropdown(dropdown, anchor) {
        const rect = anchor.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 4) + 'px';
        dropdown.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - 240)) + 'px';
        dropdown.style.display = 'block';
    }

    /* ---------- paginacja ---------- */

    function getFilteredRows() {
        return Array.from(table.querySelectorAll('tbody tr'))
            .filter(r => r.getAttribute('data-filtered') !== 'hidden');
    }

    function renderPage() {
        const allRows = Array.from(table.querySelectorAll('tbody tr'));
        const filtered = getFilteredRows();
        const total = filtered.length;
        const totalPages = Math.max(1, Math.ceil(total / perPage));
        if (currentPage > totalPages) currentPage = totalPages;

        allRows.forEach(r => r.style.display = 'none');
        filtered.slice((currentPage - 1) * perPage, currentPage * perPage).forEach(r => r.style.display = '');

        const from = total === 0 ? 0 : (currentPage - 1) * perPage + 1;
        const to = Math.min(currentPage * perPage, total);
        infoEl.textContent = from + ' do ' + to + ' z ' + total;
        pageEl.textContent = 'Strona ' + currentPage + ' z ' + totalPages;
        btnFirst.disabled = currentPage === 1;
        btnPrev.disabled = currentPage === 1;
        btnNext.disabled = currentPage === totalPages;
        btnLast.disabled = currentPage === totalPages;
    }

    function goPage(dir) {
        const total = getFilteredRows().length;
        const totalPages = Math.max(1, Math.ceil(total / perPage));
        if (dir === 'first') currentPage = 1;
        else if (dir === 'prev') currentPage = Math.max(1, currentPage - 1);
        else if (dir === 'next') currentPage = Math.min(totalPages, currentPage + 1);
        else if (dir === 'last') currentPage = totalPages;
        renderPage();
    }

    /* ---------- filtrowanie ---------- */

    function applyFilters() {
        const filters = [];
        filtrRow.querySelectorAll('th[data-col]').forEach(function(th) {
            const input = th.querySelector('input[type="text"]');
            if (input && input.value) {
                const col = th.getAttribute('data-col');
                filters.push({ col: col, raw: input.value, val: input.value.toLowerCase(), mode: filterModes[col] || 'contains' });
            }
        });
        table.querySelectorAll('tbody tr').forEach(function(row) {
            let match = true;
            for (const f of filters) {
                const cell = row.querySelector('td[data-col="' + f.col + '"]');
                const text = cell ? cell.textContent.trim().toLowerCase() : '';
                if (f.mode === 'contains' && !text.includes(f.val)) match = false;
                else if (f.mode === 'equals' && text !== f.val) match = false;
                else if (f.mode === 'starts' && !text.startsWith(f.val)) match = false;
                else if (f.mode === 'ends' && !text.endsWith(f.val)) match = false;
                if (!match) break;
            }
            row.setAttribute('data-filtered', match ? '' : 'hidden');
        });
        renderChips(filters);
        currentPage = 1;
        renderPage();
    }

    function renderChips(filters) {
        chipy.innerHTML = '';
        filters.forEach(function(f) {
            const chip = document.createElement('span');
            chip.className = 'chip';
            const label = document.createElement('span');
            label.textContent = f.raw;
            const x = document.createElement('button');
            x.type = 'button';
            x.className = 'chip-x';
            x.innerHTML = '&#10005;';
            x.addEventListener('click', function() { clearFilter(f.col); });
            chip.appendChild(label);
            chip.appendChild(x);
            chipy.appendChild(chip);
        });
    }

    function clearFilter(col) {
        const input = filtrRow.querySelector('th[data-col="' + col + '"] input[type="text"]');
        if (input) input.value = '';
        applyFilters();
    }

    function wyczyscFiltry() {
        filtrRow.querySelectorAll('input[type="text"]').forEach(i => i.value = '');
        Object.keys(filterModes).forEach(k => delete filterModes[k]);
        applyFilters();
    }

    function openFilterMenu(btn, col) {
        if (activeFilterEl === btn && filterDropdown.style.display !== 'none') {
            filterDropdown.style.display = 'none';
            activeFilterEl = null;
            return;
        }
        activeFilterEl = btn;
        activeFilterCol = String(col);
        positionDropdown(filterDropdown, btn);
    }

    function setFilterMode(mode) {
        if (activeFilterCol !== null) {
            if (mode === 'clear') {
                delete filterModes[activeFilterCol];
                clearFilter(activeFilterCol);
            } else {
                filterModes[activeFilterCol] = mode;
                applyFilters();
            }
        }
        filterDropdown.style.display = 'none';
        activeFilterEl = null;
    }

    /* ---------- sortowanie ---------- */

    function openSortMenu(el, col) {
        if (activeSortEl === el && sortDropdown.style.display !== 'none') {
            sortDropdown.style.display = 'none';
            activeSortEl = null;
            return;
        }
        activeSortEl = el;
        activeSortCol = col;
        positionDropdown(sortDropdown, el);
    }

    function sortTable(mode) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const col = activeSortCol;
        rows.sort(function(a, b) {
            const aC = a.querySelector('td[data-col="' + col + '"]');
            const bC = b.querySelector('td[data-col="' + col + '"]');
            const aT = aC ? aC.textContent.trim() : '';
            const bT = bC ? bC.textContent.trim() : '';
            if (mode === 'asc-alpha') return aT.localeCompare(bT, 'pl');
            if (mode === 'desc-alpha') return bT.localeCompare(aT, 'pl');
            if (mode === 'asc-num') return (parseFloat(aT) || 0) - (parseFloat(bT) || 0);
            if (mode === 'desc-num') return (parseFloat(bT) || 0) - (parseFloat(aT) || 0);
            return 0;
        });
        rows.forEach(r => tbody.appendChild(r));
        sortDropdown.style.display = 'none';
        activeSortEl = null;
        currentPage = 1;
        renderPage();
    }

    /* ---------- kolumny: widocznosc i kolejnosc ---------- */

    function toggleKolumne(checkbox) {
        const col = checkbox.closest('.kolumny-item').getAttribute('data-col');
        table.querySelectorAll('th[data-col="' + col + '"], td[data-col="' + col + '"]').forEach(function(cell) {
            cell.style.display = checkbox.checked ? '' : 'none';
        });
    }

    function listOrder() {
        return Array.from(lista.children).map(li => li.getAttribute('data-col'));
    }

    function applyOrder(order) {
        table.querySelectorAll('tr').forEach(function(row) {
            if (row.children.length < colCount) return;
            const anchor = akcjeKol ? row.querySelector('[data-col="' + akcjeKol + '"]') : null;
            order.forEach(function(col) {
                const cell = row.querySelector('[data-col="' + col + '"]');
                if (!cell) return;
                if (anchor) row.insertBefore(cell, anchor);
                else row.appendChild(cell);
            });
        });
    }

    lista.querySelectorAll('.kolumny-item').forEach(function(item) {
        item.addEventListener('dragstart', function(e) { dragSrc = this; e.dataTransfer.effectAllowed = 'move'; });
        item.addEventListener('dragover', function(e) { e.preventDefault(); this.classList.add('drag-over'); });
        item.addEventListener('dragleave', function() { this.classList.remove('drag-over'); });
        item.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            if (dragSrc && dragSrc !== this) {
                const nodes = Array.from(lista.children);
                const si = nodes.indexOf(dragSrc);
                const di = nodes.indexOf(this);
                if (si < di) lista.insertBefore(dragSrc, this.nextSibling);
                else lista.insertBefore(dragSrc, this);
                applyOrder(listOrder());
            }
            dragSrc = null;
        });
    });

    /* ---------- zmiana szerokosci kolumn ---------- */

    function freezeWidths() {
        if (table.style.tableLayout === 'fixed') return;
        ths.forEach(function(th) {
            if (th.style.display !== 'none') th.style.width = th.offsetWidth + 'px';
        });
        table.style.width = table.offsetWidth + 'px';
        table.style.tableLayout = 'fixed';
    }

    function autoFitColumn(th) {
        freezeWidths();
        const col = th.getAttribute('data-col');
        const meas = document.createElement('div');
        meas.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;left:-9999px;top:0;';
        document.body.appendChild(meas);
        let max = 0;
        table.querySelectorAll('th[data-col="' + col + '"], td[data-col="' + col + '"]').forEach(function(cell) {
            if (cell.style.display === 'none') return;
            if (cell.parentElement.classList.contains('filtr-row')) return;
            const cs = getComputedStyle(cell);
            meas.style.fontFamily = cs.fontFamily;
            meas.style.fontSize = cs.fontSize;
            meas.style.fontWeight = cs.fontWeight;
            meas.textContent = cell.textContent.trim();
            let w = meas.offsetWidth;
            Array.from(cell.children).forEach(function(ch) { w = Math.max(w, ch.offsetWidth); });
            max = Math.max(max, w);
        });
        meas.remove();
        const newW = Math.min(600, Math.max(40, max + 28));
        table.style.width = (table.offsetWidth + newW - th.offsetWidth) + 'px';
        th.style.width = newW + 'px';
    }

    ths.forEach(function(th) {
        const grip = document.createElement('div');
        grip.className = 'col-resizer';
        grip.title = 'Przeciągnij lub kliknij 2x aby dopasować';
        grip.addEventListener('click', function(e) { e.stopPropagation(); });
        grip.addEventListener('dblclick', function(e) {
            e.preventDefault();
            e.stopPropagation();
            autoFitColumn(th);
        });
        th.appendChild(grip);
        grip.addEventListener('mousedown', function(e) {
            e.preventDefault();
            freezeWidths();
            const startX = e.pageX;
            const startW = th.offsetWidth;
            const startTableW = table.offsetWidth;
            document.body.classList.add('col-resizing');
            function onMove(ev) {
                const w = Math.max(40, startW + ev.pageX - startX);
                th.style.width = w + 'px';
                table.style.width = (startTableW + w - startW) + 'px';
            }
            function onUp() {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                document.body.classList.remove('col-resizing');
            }
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    });

    /* ---------- uklady tabeli (konto uzytkownika) ---------- */

    function currentLayout() {
        const widths = {};
        ths.forEach(function(th) {
            if (th.style.width) widths[th.getAttribute('data-col')] = th.style.width;
        });
        const hidden = Array.from(lista.querySelectorAll('input[type="checkbox"]'))
            .filter(cb => !cb.checked)
            .map(cb => cb.closest('.kolumny-item').getAttribute('data-col'));
        return { order: listOrder(), hidden: hidden, widths: widths, tableWidth: table.style.width || '' };
    }

    function resetLayout() {
        lista.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
            if (!cb.checked) { cb.checked = true; toggleKolumne(cb); }
        });
        const defaultOrder = kolumny.filter(k => k.konfigurowalna).map(k => k.col);
        defaultOrder.forEach(function(col) {
            const li = lista.querySelector('.kolumny-item[data-col="' + col + '"]');
            if (li) lista.appendChild(li);
        });
        applyOrder(defaultOrder);
        ths.forEach(function(th) {
            th.style.width = origWidths[th.getAttribute('data-col')] || '';
        });
        table.style.tableLayout = '';
        table.style.width = '';
    }

    function applyLayout(layout) {
        resetLayout();
        if (!layout) return;
        if (Array.isArray(layout.order) && layout.order.length) {
            layout.order.forEach(function(col) {
                const li = lista.querySelector('.kolumny-item[data-col="' + col + '"]');
                if (li) lista.appendChild(li);
            });
            applyOrder(layout.order);
        }
        (layout.hidden || []).forEach(function(col) {
            const cb = lista.querySelector('.kolumny-item[data-col="' + col + '"] input[type="checkbox"]');
            if (cb) { cb.checked = false; toggleKolumne(cb); }
        });
        if (layout.widths && Object.keys(layout.widths).length) {
            Object.keys(layout.widths).forEach(function(col) {
                const th = headerRow.querySelector('th[data-col="' + col + '"]');
                if (th) th.style.width = layout.widths[col];
            });
            if (layout.tableWidth) table.style.width = layout.tableWidth;
            table.style.tableLayout = 'fixed';
        }
    }

    function renderUklady() {
        ukladyLista.innerHTML = '';
        const names = Object.keys(ukladyStore.layouts);
        if (!names.length) {
            const empty = document.createElement('div');
            empty.className = 'uklady-brak';
            empty.textContent = 'Brak zapisanych układów';
            ukladyLista.appendChild(empty);
            return;
        }
        names.forEach(function(name) {
            const row = document.createElement('div');
            row.className = 'uklad-row' + (name === ukladyStore.active ? ' active' : '');
            const pick = document.createElement('button');
            pick.type = 'button';
            pick.className = 'uklad-name';
            pick.textContent = (name === ukladyStore.active ? '✓ ' : '') + name;
            pick.addEventListener('click', function() { wybierzUklad(name); });
            const del = document.createElement('button');
            del.type = 'button';
            del.className = 'uklad-del';
            del.innerHTML = '&#10005;';
            del.title = 'Usuń układ';
            del.addEventListener('click', function(e) { e.stopPropagation(); usunUklad(name); });
            row.appendChild(pick);
            row.appendChild(del);
            ukladyLista.appendChild(row);
        });
    }

    function wybierzUklad(name) {
        if (!ukladyStore.layouts[name]) return;
        ukladyStore.active = name;
        apiPost('/api/uklady/aktywuj/', { tabela: TABELA, nazwa: name });
        applyLayout(ukladyStore.layouts[name]);
        renderUklady();
        nazwaInput.value = name;
        configDropdown.style.display = 'none';
    }

    function usunUklad(name) {
        delete ukladyStore.layouts[name];
        if (ukladyStore.active === name) ukladyStore.active = null;
        apiPost('/api/uklady/usun/', { tabela: TABELA, nazwa: name });
        renderUklady();
    }

    function toggleConfigMenu() {
        if (configDropdown.style.display !== 'none') {
            configDropdown.style.display = 'none';
            return;
        }
        nazwaInput.value = ukladyStore.active || '';
        renderUklady();
        positionDropdown(configDropdown, configBtn);
    }

    async function zapiszUklad() {
        const name = nazwaInput.value.trim();
        if (!name) { nazwaInput.focus(); return; }
        const dane = currentLayout();
        const res = await apiPost('/api/uklady/zapisz/', { tabela: TABELA, nazwa: name, dane: dane });
        if (res && res.ok) {
            ukladyStore.layouts[name] = dane;
            ukladyStore.active = name;
            renderUklady();
            saveBtn.textContent = 'Zapisano ✓';
        } else {
            saveBtn.textContent = 'Błąd zapisu';
        }
        setTimeout(function() { saveBtn.textContent = 'Zapisz'; }, 1400);
    }

    function resetujUklad() {
        ukladyStore.active = null;
        apiPost('/api/uklady/aktywuj/', { tabela: TABELA, nazwa: null });
        applyLayout(null);
        nazwaInput.value = '';
        configDropdown.style.display = 'none';
    }

    async function migrujLocalStorage() {
        if (TABELA !== 'pojazdy') return;
        let stare = null;
        try { stare = JSON.parse(localStorage.getItem('pojazdy-uklady-kolumn')); } catch (e) {}
        if (!stare || !stare.layouts) {
            try {
                const poj = JSON.parse(localStorage.getItem('pojazdy-uklad-kolumn'));
                if (poj) stare = { layouts: { 'Mój układ': poj }, active: 'Mój układ' };
            } catch (e) {}
        }
        localStorage.removeItem('pojazdy-uklady-kolumn');
        localStorage.removeItem('pojazdy-uklad-kolumn');
        if (!stare || !stare.layouts || Object.keys(ukladyStore.layouts).length) return;
        for (const nazwa of Object.keys(stare.layouts)) {
            const res = await apiPost('/api/uklady/zapisz/', { tabela: TABELA, nazwa: nazwa, dane: stare.layouts[nazwa] });
            if (res && res.ok) ukladyStore.layouts[nazwa] = stare.layouts[nazwa];
        }
        ukladyStore.active = (stare.active && ukladyStore.layouts[stare.active]) ? stare.active : null;
        await apiPost('/api/uklady/aktywuj/', { tabela: TABELA, nazwa: ukladyStore.active });
    }

    async function wczytajUklad() {
        try {
            const res = await fetch('/api/uklady/?tabela=' + encodeURIComponent(TABELA), { headers: { 'Accept': 'application/json' } });
            if (!res.ok) return;
            const data = await res.json();
            if (data && data.layouts) ukladyStore = data;
        } catch (e) { return; }
        await migrujLocalStorage();
        if (ukladyStore.active && ukladyStore.layouts[ukladyStore.active]) {
            applyLayout(ukladyStore.layouts[ukladyStore.active]);
        }
    }

    /* ---------- eksport CSV ---------- */

    function eksportujCSV() {
        const headerCells = Array.from(headerRow.children)
            .filter(function(th) {
                const col = th.getAttribute('data-col');
                const k = kolumny.find(x => x.col === col);
                return k && k.konfigurowalna && th.style.display !== 'none';
            });
        const cols = headerCells.map(th => th.getAttribute('data-col'));
        const esc = t => '"' + t.replace(/"/g, '""') + '"';
        const lines = [headerCells.map(th => esc(th.textContent.trim())).join(';')];
        getFilteredRows().forEach(function(row) {
            if (row.children.length < colCount) return;
            lines.push(cols.map(function(c) {
                const cell = row.querySelector('td[data-col="' + c + '"]');
                return esc(cell ? cell.textContent.trim() : '');
            }).join(';'));
        });
        const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = TABELA + '.csv';
        a.click();
        URL.revokeObjectURL(a.href);
    }

    /* ---------- zamykanie dropdownow ---------- */

    function onDocClick(e) {
        if (!document.body.contains(table)) {
            document.removeEventListener('click', onDocClick);
            return;
        }
        if (!sortDropdown.contains(e.target) && !e.target.closest('.th-name')) {
            sortDropdown.style.display = 'none';
            activeSortEl = null;
        }
        if (!filterDropdown.contains(e.target) && !e.target.closest('.filtr-btn')) {
            filterDropdown.style.display = 'none';
            activeFilterEl = null;
        }
        if (!configDropdown.contains(e.target) && e.target !== configBtn) {
            configDropdown.style.display = 'none';
        }
    }
    document.addEventListener('click', onDocClick);

    /* ---------- start ---------- */

    wczytajUklad();
    renderPage();
};
})();
