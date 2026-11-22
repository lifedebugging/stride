const toggleBtn = document.getElementById('mascot');
const drawer = document.getElementById('sidebar-drawer');
const newChatBtn = document.querySelector('.new-chat-btn');
const chatMessages = document.querySelector('.chat-messages');
const chatInput = document.querySelector('.chat-input');
const newChatDialog = document.getElementById('new-chat-dialog');
const closeDialogBtn = document.querySelector('.dialog-close-btn');
const historyItems = document.querySelectorAll('.history-item');
let mascotTurnTimer;

if (
    !(toggleBtn instanceof HTMLButtonElement) ||
    !(drawer instanceof HTMLElement) ||
    !(newChatBtn instanceof HTMLButtonElement) ||
    !(chatMessages instanceof HTMLElement) ||
    !(chatInput instanceof HTMLInputElement) ||
    !(newChatDialog instanceof HTMLDialogElement) ||
    !(closeDialogBtn instanceof HTMLButtonElement)
) {
    throw new Error('Sidebar and new chat elements are missing from the page.');
}

toggleBtn.addEventListener('click', () => {
    const isOpen = drawer.classList.contains('open');

    setSidebarOpen(!isOpen);
});

newChatBtn.addEventListener('click', () => {
    chatMessages.replaceChildren();
    chatInput.value = '';
    document.querySelector('.main-workspace')?.classList.remove('active-chat');
    window.dispatchEvent(new Event('stride:new-chat'));
    closeSidebar();
    newChatDialog.showModal();
});

closeDialogBtn.addEventListener('click', () => newChatDialog.close());

newChatDialog.addEventListener('close', () => chatInput.focus());

newChatDialog.addEventListener('cancel', event => {
    event.preventDefault();
    newChatDialog.close();
});

newChatDialog.addEventListener('click', event => {
    if (event.target === newChatDialog) {
        newChatDialog.close();
    }
});

function closeSidebar() {
    setSidebarOpen(false);
}

function setSidebarOpen(isOpen) {
    clearTimeout(mascotTurnTimer);
    mascotTurnTimer = undefined;
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
        const isOpen = drawer.classList.contains('open');

        mascotTurnTimer = setTimeout(() => {
            if (drawer.classList.contains('open') === isOpen && !toggleBtn.classList.contains('running')) {
                if (isOpen) {
                    toggleBtn.classList.add('facing-left');
                } else {
                    toggleBtn.classList.remove('facing-left');
                }
            }
        }, 500);
    }
});