const toggleBtn = document.getElementById('mascot');
const drawer = document.getElementById('sidebar-drawer');
const historyItems = document.querySelectorAll('.history-item');

toggleBtn.addEventListener('click', () => {
    const isOpen = drawer.classList.contains('open');

    setSidebarOpen(!isOpen);
});

function closeSidebar() {
    setSidebarOpen(false);
}

function setSidebarOpen(isOpen) {
    drawer.classList.toggle('open', isOpen);
    drawer.setAttribute('aria-hidden', String(!isOpen));
    toggleBtn.setAttribute('aria-expanded', String(isOpen));
    toggleBtn.setAttribute('aria-label', isOpen ? 'Close sidebar' : 'Open sidebar');
    toggleBtn.classList.toggle('open', isOpen);
    toggleBtn.classList.toggle('facing-left', !isOpen);
    toggleBtn.classList.add('running');
}

// Automatically close the sidebar when selecting any chat history item
historyItems.forEach(item => {
    item.addEventListener('click', () => {
        // ...logic to load selected chat...
        closeSidebar();
    });
});

toggleBtn.addEventListener('transitionend', event => {
    if (event.target === toggleBtn && event.propertyName === 'transform') {
        toggleBtn.classList.remove('running');
        if (!drawer.classList.contains('open')) {
            toggleBtn.classList.remove('facing-left');
        }
    }
});