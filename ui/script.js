const toggleBtn = document.getElementById('mascot');
const drawer = document.getElementById('sidebar-drawer');
const newChatBtn = document.querySelector('.new-chat-btn');
const chatMessages = document.querySelector('.chat-messages');
const chatInput = document.querySelector('.chat-input');
const chatHistoryList = document.querySelector('.chat-history-list');
const newChatDialog = document.getElementById('new-chat-dialog');
const closeDialogBtn = document.querySelector('.dialog-close-btn');
let mascotTurnTimer;

if (
    !(toggleBtn instanceof HTMLButtonElement) ||
    !(drawer instanceof HTMLElement) ||
    !(newChatBtn instanceof HTMLButtonElement) ||
    !(chatMessages instanceof HTMLElement) ||
    !(chatInput instanceof HTMLTextAreaElement) ||
    !(chatHistoryList instanceof HTMLUListElement) ||
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
});

closeDialogBtn.addEventListener('click', () => newChatDialog.close());

window.addEventListener('stride:authentication-required', () => {
    if (!newChatDialog.open) {
        newChatDialog.showModal();
    }
});

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

chatHistoryList.addEventListener('click', event => {
    if (!(event.target instanceof Element)) {
        return;
    }

    const historyButton = event.target.closest('button.history-item');
    const chatId = historyButton?.getAttribute('data-chat-id');
    if (chatId) {
        window.dispatchEvent(new CustomEvent('stride:load-chat', { detail: { chatId } }));
        closeSidebar();
    }
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