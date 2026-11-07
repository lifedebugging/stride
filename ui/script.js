const toggleBtn = document.getElementById('sidebar-toggle');
const drawer = document.getElementById('sidebar-drawer');
const historyItems = document.querySelectorAll('.history-item');

// Toggle sidebar drawer and trigger logo rotation
toggleBtn.addEventListener('click', () => {
    const isOpen = drawer.classList.contains('open');

    if (isOpen) {
        closeSidebar();
    } else {
        openSidebar();
    }
});

function openSidebar() {
    drawer.classList.add('open');
    toggleBtn.classList.add('open');
    toggleBtn.classList.remove('close-anim');
}

function closeSidebar() {
    drawer.classList.remove('open');
    toggleBtn.classList.remove('open');
    toggleBtn.classList.add('close-anim');
}

// Automatically close the sidebar when selecting any chat history item
historyItems.forEach(item => {
    item.addEventListener('click', () => {
        // ...logic to load selected chat...
        closeSidebar();
    });
});