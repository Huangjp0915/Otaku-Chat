const state = {
  allCharacters: [],
  friendCharacters: [],
  momentsFeed: [],
  currentMomentsCharacterId: null,
  currentCharacterId: null,
  currentCharacterDetail: null,
  currentConversation: null,
  runtime: null,
  currentView: 'chat',
  pendingByCharacter: {},
  contextCharacterId: null,
  proactiveTimer: null,
  userAvatar: '',
  userProfile: { birthday_month_day: '' },
  friendRequests: [],
  contactsMainMode: 'overview',
};

const els = {
  navChat: document.getElementById('navChat'),
  navContacts: document.getElementById('navContacts'),
  navMoments: document.getElementById('navMoments'),
  navSettings: document.getElementById('navSettings'),
  openAddContactBtn: document.getElementById('openAddContactBtn'),
  searchInput: document.getElementById('searchInput'),
  sessionTitleBar: document.getElementById('sessionTitleBar'),
  chatList: document.getElementById('chatList'),
  contactList: document.getElementById('contactList'),
  settingsShortcutList: document.getElementById('settingsShortcutList'),
  mainHeader: document.getElementById('mainHeader'),
  headerAvatar: document.getElementById('headerAvatar'),
  headerName: document.getElementById('headerName'),
  headerDesc: document.getElementById('headerDesc'),
  chatPage: document.getElementById('chatPage'),
  settingsPage: document.getElementById('settingsPage'),
  chatArea: document.getElementById('chatArea'),
  composer: document.getElementById('composer'),
  messageInput: document.getElementById('messageInput'),
  sendBtn: document.getElementById('sendBtn'),
  toggleProfileBtn: document.getElementById('toggleProfileBtn'),
  detailMask: document.getElementById('detailMask'),
  detailDrawer: document.getElementById('detailDrawer'),
  detailProfile: document.getElementById('detailProfile'),
  detailEvents: document.getElementById('detailEvents'),
  detailTabProfile: document.getElementById('detailTabProfile'),
  detailTabEvents: document.getElementById('detailTabEvents'),
  closeDetailBtn: document.getElementById('closeDetailBtn'),
  addContactMask: document.getElementById('addContactMask'),
  addContactDrawer: document.getElementById('addContactDrawer'),
  addContactSearchInput: document.getElementById('addContactSearchInput'),
  addContactResults: document.getElementById('addContactResults'),
  closeAddContactBtn: document.getElementById('closeAddContactBtn'),
  settingsModeSelect: document.getElementById('settingsModeSelect'),
  settingsOllamaStatus: document.getElementById('settingsOllamaStatus'),
  settingsModelSelect: document.getElementById('settingsModelSelect'),
  settingsShortcutSelect: document.getElementById('settingsShortcutSelect'),
  settingsIntervalInput: document.getElementById('settingsIntervalInput'),
  settingsBirthdayInput: document.getElementById('settingsBirthdayInput'),
  saveSettingsBtn: document.getElementById('saveSettingsBtn'),
  saveBirthdayBtn: document.getElementById('saveBirthdayBtn'),
  refreshModelsBtn: document.getElementById('refreshModelsBtn'),
  avatarToolGrid: document.getElementById('avatarToolGrid'),
  contextMenu: document.getElementById('contextMenu'),
  contextPinBtn: document.getElementById('contextPinBtn'),
  contextDeleteBtn: document.getElementById('contextDeleteBtn'),

  toastStack: document.getElementById('toastStack'),
  appDialogMask: document.getElementById('appDialogMask'),
  appDialog: document.getElementById('appDialog'),
  appDialogTitle: document.getElementById('appDialogTitle'),
  appDialogContent: document.getElementById('appDialogContent'),
  appDialogCancelBtn: document.getElementById('appDialogCancelBtn'),
  appDialogConfirmBtn: document.getElementById('appDialogConfirmBtn'),
};

function escapeHtml(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(url, body, isFormData = false) {
  const options = { method: 'POST' };
  if (body !== undefined && body !== null) {
    if (isFormData) {
      options.body = body;
    } else {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }
  }
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function byId(id) {
  return state.allCharacters.find((item) => item.id === id);
}

function formatTime(iso) {
  if (!iso) return '';
  return String(iso).replace('T', ' ');
}

let dialogResolver = null;

function showToast(message, type = 'info', duration = 2400) {
  if (!els.toastStack) return;

  const toast = document.createElement('div');
  toast.className = `app-toast ${type}`;
  toast.textContent = String(message || '');
  els.toastStack.appendChild(toast);

  window.setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-6px)';
    toast.style.transition = 'all 0.18s ease';
    window.setTimeout(() => toast.remove(), 180);
  }, duration);
}

function closeAppDialog(result) {
  els.appDialog.classList.add('hidden');
  els.appDialogMask.classList.add('hidden');
  els.appDialog.classList.remove('danger');

  const resolve = dialogResolver;
  dialogResolver = null;

  if (resolve) {
    resolve(result);
  }
}

function showAppDialog({
  title = '提示',
  content = '',
  confirmText = '确定',
  cancelText = '',
  danger = false,
} = {}) {
  return new Promise((resolve) => {
    dialogResolver = resolve;

    els.appDialogTitle.textContent = title;
    els.appDialogContent.textContent = content;
    els.appDialogConfirmBtn.textContent = confirmText || '确定';

    if (cancelText) {
      els.appDialogCancelBtn.textContent = cancelText;
      els.appDialogCancelBtn.classList.remove('hidden');
    } else {
      els.appDialogCancelBtn.classList.add('hidden');
    }

    els.appDialog.classList.toggle('danger', !!danger);
    els.appDialogMask.classList.remove('hidden');
    els.appDialog.classList.remove('hidden');
  });
}

function showInfoDialog(title, content, confirmText = '知道了') {
  return showAppDialog({
    title,
    content,
    confirmText,
    cancelText: '',
    danger: false,
  });
}

function showConfirmDialog(title, content, confirmText = '确定', cancelText = '取消', danger = false) {
  return showAppDialog({
    title,
    content,
    confirmText,
    cancelText,
    danger,
  });
}

function normalizeMonthDay(value) {
  const compact = String(value || '').trim();
  if (!compact) return '';

  const match = compact.match(/^(\d{2})-(\d{2})$/);
  if (!match) return null;

  const month = Number(match[1]);
  const day = Number(match[2]);
  const probe = new Date(2000, month - 1, day);

  if (
    Number.isNaN(month) ||
    Number.isNaN(day) ||
    probe.getFullYear() !== 2000 ||
    probe.getMonth() !== month - 1 ||
    probe.getDate() !== day
  ) {
    return null;
  }

  return `${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function displayListDate(iso) {
  if (!iso) return '';
  return String(iso).slice(11, 16);
}

function shouldShowTimeDivider(prevTs, currentTs) {
  if (!prevTs) return true;
  const prev = new Date(prevTs).getTime();
  const curr = new Date(currentTs).getTime();
  if (Number.isNaN(prev) || Number.isNaN(curr)) return false;
  return curr - prev > 5 * 60 * 1000 || String(prevTs).slice(0, 10) !== String(currentTs).slice(0, 10);
}

function sortFriends(items) {
  return [...items].sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
    return (b.last_message_time || '').localeCompare(a.last_message_time || '');
  });
}

function getContactSortLetter(item) {
  if (!item) return '#';

  if (item.sort_letter && /^[A-Za-z]$/.test(String(item.sort_letter).charAt(0))) {
    return String(item.sort_letter).charAt(0).toUpperCase();
  }

  const name = String(item.name || '').trim();
  if (!name) return '#';

  const first = name.charAt(0).toUpperCase();
  if (/^[A-Z]$/.test(first)) return first;
  if (/^[0-9]$/.test(first)) return '#';

  return '#';
}

function sortContactsForAddressBook(items) {
  return [...items].sort((a, b) => {
    const letterA = getContactSortLetter(a);
    const letterB = getContactSortLetter(b);

    if (letterA !== letterB) {
      if (letterA === '#') return 1;
      if (letterB === '#') return -1;
      return letterA.localeCompare(letterB);
    }

    return String(a.name || '').localeCompare(String(b.name || ''), 'zh-CN');
  });
}

function groupContactsByLetter(items) {
  const grouped = {};
  const sorted = sortContactsForAddressBook(items);

  sorted.forEach((item) => {
    const letter = getContactSortLetter(item);
    if (!grouped[letter]) grouped[letter] = [];
    grouped[letter].push(item);
  });

  return Object.keys(grouped)
    .sort((a, b) => {
      if (a === '#') return 1;
      if (b === '#') return -1;
      return a.localeCompare(b);
    })
    .map((letter) => ({
      letter,
      items: grouped[letter],
    }));
}

function activateNav(view) {
  els.navChat.classList.toggle('active', view === 'chat');
  els.navContacts.classList.toggle('active', view === 'contacts');
  els.navMoments.classList.toggle('active', view === 'moments');
  els.navSettings.classList.toggle('active', view === 'settings');
}

function clearMainSearch() {
  els.searchInput.value = '';
}

function setView(view) {
  state.currentView = view;
  activateNav(view);

  els.chatList.classList.toggle('hidden', view !== 'chat');
  els.contactList.classList.toggle('hidden', !['contacts', 'moments'].includes(view));
  els.settingsShortcutList.classList.toggle('hidden', view !== 'settings');

  els.settingsPage.classList.toggle('hidden', view !== 'settings');
  els.chatPage.classList.toggle('hidden', view === 'settings');
  els.composer.classList.toggle('hidden', view !== 'chat');

  if (view === 'chat') {
    els.sessionTitleBar.textContent = '聊天';
    renderChatList();
    if (state.currentConversation) renderConversation();
    else renderEmptyMain('还没有联系人', '请点击左上角 + 搜索并添加角色联系人。');
  } else if (view === 'contacts') {
    els.sessionTitleBar.textContent = '通讯录';
    renderContactList();
    renderContactsMain();
  } else if (view === 'moments') {
    els.sessionTitleBar.textContent = '朋友圈';
    renderMomentsSidebar();
    renderMomentsMain();
  } else {
    els.sessionTitleBar.textContent = '设置';
    renderSettingsShortcutList();
    renderSettingsMain();
  }
}

function renderEmptyMain(title, sub) {
  els.headerAvatar.classList.add('hidden');
  els.mainHeader.classList.remove('clickable');
  els.headerName.textContent = title;
  els.headerDesc.textContent = sub;
  els.chatArea.className = 'chat-area empty';
  els.chatArea.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">💬</div>
      <div class="empty-title">${escapeHtml(title)}</div>
      <div class="empty-sub">${escapeHtml(sub)}</div>
    </div>
  `;
}

function getCurrentUserAvatarHtml() {
  if (state.userAvatar) {
    return `<img class="msg-avatar" src="${state.userAvatar}" alt="你" />`;
  }
  return `<div class="msg-avatar self-avatar">你</div>`;
}

function renderChatList() {
  const keyword = els.searchInput.value.trim().toLowerCase();
  state.friendCharacters = state.allCharacters.filter((item) => item.is_friend);

  const items = sortFriends(state.friendCharacters).filter((item) => {
    if (!keyword) return true;
    return (
      item.name.toLowerCase().includes(keyword) ||
      item.source.toLowerCase().includes(keyword) ||
      (item.last_message_preview || '').toLowerCase().includes(keyword)
    );
  });

  if (!items.length) {
    els.chatList.innerHTML = '<div class="empty-list">暂无聊天。点击左上角 + 添加联系人。</div>';
    return;
  }

  const simultaneousUnreadCount = items.filter((item) => item.unread_count > 0).length;

  els.chatList.innerHTML = items.map((item) => {
    const showCompetitionHint = simultaneousUnreadCount >= 2 && item.unread_count > 0;

    return `
      <div class="session-item ${item.id === state.currentCharacterId ? 'active' : ''}" data-id="${item.id}">
        <img class="avatar" src="${item.avatar}" alt="${escapeHtml(item.name)}" />
        <div class="session-main">
          <div class="session-topline">
            <div class="session-name">
              ${escapeHtml(item.name)}
              ${item.is_pinned ? '<span class="pin-badge">📌</span>' : ''}
            </div>
            <div class="session-time">${displayListDate(item.last_message_time)}</div>
          </div>
          <div class="session-subtitle">
            <span class="presence-dot ${item.presence_status || 'idle'}"></span>
            ${escapeHtml(item.presence_text || item.title)}
            ${showCompetitionHint ? '<span class="meta-light"> · 同时来消息</span>' : ''}
          </div>
          <div class="session-preview">${escapeHtml(item.last_message_preview || '还没有消息')}</div>
        </div>
        <div>
          ${item.unread_count > 0 ? `<div class="unread-dot">${Math.min(item.unread_count, 99)}</div>` : ''}
        </div>
      </div>
    `;
  }).join('');

  els.chatList.querySelectorAll('.session-item').forEach((node) => {
    node.addEventListener('click', async () => {
      clearMainSearch();
      await openConversation(node.dataset.id);
      setView('chat');
    });

    node.addEventListener('contextmenu', (event) => {
      event.preventDefault();
      const item = byId(node.dataset.id);
      showContextMenu(node.dataset.id, !!item?.is_pinned, event.clientX, event.clientY);
    });
  });
}

function renderContactList() {
  const keyword = els.searchInput.value.trim().toLowerCase();

  const contacts = state.allCharacters
    .filter((item) => item.is_friend)
    .filter((item) => {
      if (!keyword) return true;
      return item.name.toLowerCase().includes(keyword) || item.source.toLowerCase().includes(keyword);
    });

  const groupedContacts = groupContactsByLetter(contacts);
  const pendingCount = state.friendRequests.filter((item) => item.status === 'pending').length;
  const totalRequestCount = state.friendRequests.length;

  const systemEntries = [
    {
      key: 'new_friends',
      icon: '👋',
      color: 'green',
      title: '新的朋友',
      subtitle: totalRequestCount ? `共 ${totalRequestCount} 条申请记录` : '查看好友申请记录和验证结果',
      count: pendingCount || '',
    },
    { key: 'group_chat', icon: '👥', color: 'blue', title: '群聊', subtitle: '预留入口', count: '' },
    { key: 'contacts', icon: '📒', color: 'gray', title: '联系人', subtitle: `已添加 ${contacts.length} 位角色`, count: contacts.length || '' },
  ];

  const systemHtml = systemEntries.map((entry) => `
    <div class="system-entry" data-entry-key="${entry.key}">
      <div class="entry-icon ${entry.color}">${entry.icon}</div>
      <div class="contact-main">
        <div class="session-name">${entry.title}</div>
        <div class="contact-subtitle">${entry.subtitle}</div>
      </div>
      <div class="system-count">${entry.count}</div>
    </div>
  `).join('');

  let groupedHtml = '';
  if (groupedContacts.length) {
    groupedHtml = groupedContacts.map((group) => `
      <div class="contact-letter">${group.letter}</div>
      ${group.items.map((item) => `
        <div class="contact-item" data-id="${item.id}">
          <img class="avatar" src="${item.avatar}" alt="${escapeHtml(item.name)}" />
          <div class="contact-main">
            <div class="session-name">${escapeHtml(item.name)}</div>
            <div class="contact-subtitle">
              <span class="presence-dot ${item.presence_status || 'idle'}"></span>
              ${escapeHtml(item.presence_text || item.source)}
            </div>
            <div class="contact-preview">${escapeHtml(item.title)}</div>
          </div>
          <div class="meta-light">${item.unread_count > 0 ? `<span class="unread-dot">${Math.min(item.unread_count, 99)}</span>` : '已添加'}</div>
        </div>
      `).join('')}
    `).join('');
  } else {
    groupedHtml = '<div class="empty-list">还没有已添加联系人。请点击左上角 + 搜索添加。</div>';
  }

  els.contactList.innerHTML = systemHtml + groupedHtml;

  els.contactList.querySelectorAll('.contact-item').forEach((node) => {
    node.addEventListener('click', async () => {
      clearMainSearch();
      await openConversation(node.dataset.id);
      setView('chat');
    });

    node.addEventListener('contextmenu', (event) => {
      event.preventDefault();
      const item = byId(node.dataset.id);
      showContextMenu(node.dataset.id, !!item?.is_pinned, event.clientX, event.clientY);
    });
  });

  els.contactList.querySelectorAll('.system-entry').forEach((node) => {
    node.addEventListener('click', () => {
      const key = node.dataset.entryKey;

      if (key === 'new_friends') {
        state.contactsMainMode = 'new_friends';
        renderContactsMain();
        return;
      }

      if (key === 'group_chat') {
        showInfoDialog('群聊功能后续再接。');
        return;
      }

      if (key === 'contacts') {
        state.contactsMainMode = 'overview';
        renderContactsMain();

        const firstLetter = els.contactList.querySelector('.contact-letter');
        if (firstLetter) {
          firstLetter.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
}

function renderSettingsShortcutList() {
  els.settingsShortcutList.classList.add('contact-list');
  els.settingsShortcutList.innerHTML = `
    <div class="settings-nav-item">
      <div class="entry-icon green">🤖</div>
      <div class="contact-main">
        <div class="session-name">模型设置</div>
        <div class="contact-subtitle">mock / Ollama 模式切换</div>
      </div>
      <div></div>
    </div>
    <div class="settings-nav-item">
      <div class="entry-icon blue">💬</div>
      <div class="contact-main">
        <div class="session-name">聊天设置</div>
        <div class="contact-subtitle">快捷键、主动消息频率</div>
      </div>
      <div></div>
    </div>
    <div class="settings-nav-item">
      <div class="entry-icon gray">🖼️</div>
      <div class="contact-main">
        <div class="session-name">头像管理</div>
        <div class="contact-subtitle">你自己和角色都可替换头像</div>
      </div>
      <div></div>
    </div>
  `;
}

function getFriendRequestStatusClass(status) {
  if (status === 'accepted') return 'accepted';
  if (status === 'ignored') return 'ignored';
  if (status === 'rejected') return 'rejected';
  return 'pending';
}

function renderNewFriendsPage() {
  els.mainHeader.classList.remove('clickable');
  els.headerAvatar.classList.add('hidden');
  els.headerName.textContent = '新的朋友';

  const pendingCount = state.friendRequests.filter((item) => item.status === 'pending').length;
  els.headerDesc.textContent = pendingCount
    ? `还有 ${pendingCount} 条申请等待验证`
    : '这里会显示好友申请记录、处理状态与系统通知';

  const items = [...state.friendRequests].sort((a, b) =>
    (b.requested_at || '').localeCompare(a.requested_at || '')
  );

  els.chatArea.className = 'chat-area new-friends-mode';

  if (!items.length) {
    els.chatArea.innerHTML = `
      <div class="new-friends-wrap">
        <div class="empty-state">
          <div class="empty-icon">👋</div>
          <div class="empty-title">还没有好友申请记录</div>
          <div class="empty-sub">点击下方按钮，开始添加第一个角色联系人。</div>
          <div style="margin-top: 16px;">
            <button id="emptyAddFriendBtn" class="primary-btn">添加朋友</button>
          </div>
        </div>
      </div>
    `;
    document.getElementById('emptyAddFriendBtn')?.addEventListener('click', openAddContactDrawer);
    return;
  }

  els.chatArea.innerHTML = `
    <div class="new-friends-wrap">
      <div class="new-friends-toolbar">
        <div>
          <div class="new-friends-toolbar-title">好友申请记录</div>
          <div class="new-friends-toolbar-subtitle">已发送的申请、处理结果和系统通知都会保留在这里</div>
        </div>
        <div class="new-friends-toolbar-actions">
          <button id="backToContactsBtn" class="secondary-btn">返回通讯录</button>
          <button id="newFriendsAddBtn" class="primary-btn">添加朋友</button>
        </div>
      </div>

      <div class="new-friends-list">
        ${items.map((item) => {
          const actionHtml = item.is_friend
            ? `<button class="secondary-btn friend-request-action" data-id="${item.character_id}" data-action="chat">发消息</button>`
            : item.status === 'pending'
              ? `<button class="secondary-btn friend-request-action" disabled>等待验证</button>`
              : `<button class="primary-btn friend-request-action" data-id="${item.character_id}" data-action="retry">重新申请</button>`;

          return `
            <div class="friend-request-card" data-id="${item.character_id}">
              <div class="friend-request-top">
                <img class="avatar" src="${item.avatar}" alt="${escapeHtml(item.character_name)}" />
                <div class="friend-request-main">
                  <div class="friend-request-name-row">
                    <div class="session-name">${escapeHtml(item.character_name)}</div>
                    <span class="status-badge ${getFriendRequestStatusClass(item.status)}">${escapeHtml(item.status_text)}</span>
                    ${item.is_friend ? '<span class="status-badge added">已添加</span>' : ''}
                  </div>
                  <div class="drawer-result-subtitle">${escapeHtml(item.source || '')}</div>
                  <div class="request-meta-row">
                    <span>发送时间：${formatTime(item.requested_at)}</span>
                    ${
                      item.resolved_at
                        ? `<span>处理时间：${formatTime(item.resolved_at)}</span>`
                        : `<span>最早处理：${formatTime(item.review_after)}</span>`
                    }
                  </div>
                </div>
                <div class="friend-request-actions">${actionHtml}</div>
              </div>

              ${item.system_notice_text ? `
                <div class="request-info request-system-notice">
                  <strong>系统通知</strong>
                  <div>${escapeHtml(item.system_notice_text)}</div>
                </div>
              ` : ''}

              ${item.result_text ? `
                <div class="request-info request-result-text">
                  <strong>${item.status === 'accepted' ? '通过消息' : '处理结果'}</strong>
                  <div>${escapeHtml(item.result_text)}</div>
                </div>
              ` : ''}

              ${item.reason_text ? `
                <div class="request-info request-reason-text">
                  <strong>为什么会通过你</strong>
                  <div>${escapeHtml(item.reason_text)}</div>
                </div>
              ` : ''}
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;

  document.getElementById('newFriendsAddBtn')?.addEventListener('click', openAddContactDrawer);
  document.getElementById('backToContactsBtn')?.addEventListener('click', () => {
    state.contactsMainMode = 'overview';
    renderContactsMain();
  });

  els.chatArea.querySelectorAll('.friend-request-action').forEach((button) => {
    button.addEventListener('click', async () => {
      const characterId = button.dataset.id;
      const action = button.dataset.action;

      if (!characterId || !action) return;

      if (action === 'chat') {
        await openConversation(characterId);
        setView('chat');
        return;
      }

      if (action === 'retry') {
        await addContact(characterId);
      }
    });
  });
}

function renderMomentsSidebar() {
  const keyword = els.searchInput.value.trim().toLowerCase();
  const friends = state.allCharacters
    .filter((item) => item.is_friend)
    .filter((item) => {
      if (!keyword) return true;
      return item.name.toLowerCase().includes(keyword) || item.source.toLowerCase().includes(keyword);
    });

  const systemHtml = `
    <div class="system-entry" data-entry-key="all_moments">
      <div class="entry-icon green">📰</div>
      <div class="contact-main">
        <div class="session-name">全部动态</div>
        <div class="contact-subtitle">查看所有已添加好友的朋友圈</div>
      </div>
      <div class="system-count">${state.momentsFeed.length || ''}</div>
    </div>
  `;

  const friendHtml = friends.length
    ? friends.map((item) => `
      <div class="contact-item ${state.currentMomentsCharacterId === item.id ? 'active' : ''}" data-id="${item.id}">
        <img class="avatar" src="${item.avatar}" alt="${escapeHtml(item.name)}" />
        <div class="contact-main">
          <div class="session-name">${escapeHtml(item.name)}</div>
          <div class="contact-subtitle">${escapeHtml(item.source || '')}</div>
          <div class="contact-preview">查看 TA 的个人动态</div>
        </div>
        <div class="meta-light">›</div>
      </div>
    `).join('')
    : '<div class="empty-list">还没有已添加联系人，朋友圈暂时为空。</div>';

  els.contactList.innerHTML = systemHtml + friendHtml;

  els.contactList.querySelector('[data-entry-key="all_moments"]')?.addEventListener('click', async () => {
    await openMomentsView(null);
  });

  els.contactList.querySelectorAll('.contact-item').forEach((node) => {
    node.addEventListener('click', async () => {
      await openMomentsView(node.dataset.id);
    });
  });
}

function renderMomentsMain() {
  const selectedCharacter = state.currentMomentsCharacterId
    ? byId(state.currentMomentsCharacterId)
    : null;

  if (selectedCharacter) {
    els.mainHeader.classList.remove('clickable');
    els.headerAvatar.src = selectedCharacter.avatar;
    els.headerAvatar.classList.remove('hidden');
    els.headerName.textContent = `${selectedCharacter.name} 的朋友圈`;
    els.headerDesc.textContent = `${selectedCharacter.source} · 只看这个角色的动态`;
  } else {
    els.mainHeader.classList.remove('clickable');
    els.headerAvatar.classList.add('hidden');
    els.headerName.textContent = '朋友圈';
    els.headerDesc.textContent = '这里会显示所有已添加好友角色发出的动态';
  }

  els.chatArea.className = 'chat-area moments-mode';

  if (!state.friendCharacters.length) {
    els.chatArea.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📰</div>
        <div class="empty-title">朋友圈还没有开启</div>
        <div class="empty-sub">先添加角色联系人，之后这里才会出现她们的动态。</div>
      </div>
    `;
    return;
  }

  if (!state.momentsFeed.length) {
    els.chatArea.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">✨</div>
        <div class="empty-title">暂时还没有动态</div>
        <div class="empty-sub">${selectedCharacter ? '这个角色还没有发动态。' : '你的好友们暂时还没有更新朋友圈。'}</div>
      </div>
    `;
    return;
  }

  els.chatArea.innerHTML = `
    <div class="moments-wrap">
      <div class="moments-toolbar">
        <div>
          <div class="moments-toolbar-title">${selectedCharacter ? '个人朋友圈' : '主朋友圈'}</div>
          <div class="moments-toolbar-subtitle">
            ${selectedCharacter ? '只看这个角色的动态记录' : '按时间倒序显示所有好友角色的动态'}
          </div>
        </div>
        ${selectedCharacter ? '<button id="backToAllMomentsBtn" class="secondary-btn">返回全部动态</button>' : ''}
      </div>

      <div class="moments-feed">
        ${state.momentsFeed.map((item) => `
          <div class="moment-card" data-id="${item.id}">
            <div class="moment-top">
              <img class="avatar moment-open-character" src="${item.avatar}" alt="${escapeHtml(item.character_name)}" data-character-id="${item.character_id}" />
              <div class="moment-head-main">
                <div class="session-name moment-open-character" data-character-id="${item.character_id}">
                  ${escapeHtml(item.character_name)}
                </div>
                <div class="drawer-result-subtitle">${escapeHtml(item.source || '')}</div>
                <div class="moment-time">${formatTime(item.created_at)}</div>
              </div>
            </div>

            <div class="moment-content">${escapeHtml(item.content)}</div>

            ${item.topic_refs?.length ? `
              <div class="moment-tags">
                ${item.topic_refs.map((tag) => `<span class="moment-tag">#${escapeHtml(tag)}</span>`).join('')}
              </div>
            ` : ''}

            <div class="moment-actions">
              <button class="secondary-btn moment-like-btn ${item.liked_by_me ? 'liked' : ''}" data-id="${item.id}">
                ${item.liked_by_me ? '已点赞' : '点赞'} (${item.like_count || 0})
              </button>
              <button class="secondary-btn moment-open-btn" data-character-id="${item.character_id}">
                只看 TA
              </button>
            </div>

            <div class="moment-comments">
              <div class="moment-comments-title">评论</div>
              ${
                item.comments?.length
                  ? item.comments.map((comment) => `
                    <div class="moment-comment-item">
                      <span class="moment-comment-user">${escapeHtml(comment.user_name || '你')}</span>
                      <span class="moment-comment-text">${escapeHtml(comment.content)}</span>
                      <span class="moment-comment-time">${formatTime(comment.created_at)}</span>
                    </div>
                  `).join('')
                  : '<div class="moment-comment-empty">还没有评论，留下第一条吧。</div>'
              }
            </div>

            <div class="moment-comment-box">
              <input class="normal-input moment-comment-input" type="text" placeholder="写下评论..." />
              <button class="primary-btn moment-comment-send" data-id="${item.id}">发送</button>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  document.getElementById('backToAllMomentsBtn')?.addEventListener('click', async () => {
    await openMomentsView(null);
  });

  els.chatArea.querySelectorAll('.moment-like-btn').forEach((button) => {
    button.addEventListener('click', async () => {
      try {
        await apiPost(`/api/moments/${button.dataset.id}/like`);
        await loadMomentsFeed(state.currentMomentsCharacterId);
        renderMomentsSidebar();
        renderMomentsMain();
      } catch (error) {
        showToast('点赞失败：' + error.message);
      }
    });
  });

  els.chatArea.querySelectorAll('.moment-open-btn, .moment-open-character').forEach((button) => {
    button.addEventListener('click', async () => {
      const characterId = button.dataset.characterId;
      if (!characterId) return;
      await openMomentsView(characterId);
    });
  });

  els.chatArea.querySelectorAll('.moment-comment-send').forEach((button) => {
    button.addEventListener('click', async () => {
      const card = button.closest('.moment-card');
      const input = card?.querySelector('.moment-comment-input');
      const content = input?.value?.trim() || '';
      if (!content) {
        showToast('评论不能为空。');
        return;
      }

      try {
        await apiPost(`/api/moments/${button.dataset.id}/comment`, { content });
        await loadMomentsFeed(state.currentMomentsCharacterId);
        renderMomentsSidebar();
        renderMomentsMain();
      } catch (error) {
        showToast('评论失败：' + error.message);
      }
    });
  });

  els.chatArea.querySelectorAll('.moment-comment-input').forEach((input) => {
    input.addEventListener('keydown', async (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      const button = input.closest('.moment-card')?.querySelector('.moment-comment-send');
      button?.click();
    });
  });
}

function renderContactsMain() {
  if (state.contactsMainMode === 'new_friends') {
    renderNewFriendsPage();
    return;
  }

  els.mainHeader.classList.remove('clickable');
  els.headerAvatar.classList.add('hidden');
  els.headerName.textContent = '通讯录';
  els.headerDesc.textContent = '新的朋友、群聊、已添加联系人';
  els.chatArea.className = 'chat-area empty';
  els.chatArea.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📒</div>
      <div class="empty-title">通讯录管理</div>
      <div class="empty-sub">未添加的角色不会显示在这里。请点击左上角 + 搜索并添加。</div>
    </div>
  `;
}

function renderSettingsMain() {
  els.mainHeader.classList.remove('clickable');
  els.headerAvatar.classList.add('hidden');
  els.headerName.textContent = '设置';
  els.headerDesc.textContent = '模型、聊天行为与头像管理';
  renderSettingsPage();
}

function renderProfile() {
  if (!state.currentCharacterDetail || !state.currentConversation) {
    els.detailProfile.innerHTML = '';
    return;
  }
  const c = state.currentCharacterDetail;
  const s = state.currentConversation;
  els.detailProfile.innerHTML = `
    <div class="profile-top">
      <img class="profile-big-avatar" src="${c.avatar}" alt="${escapeHtml(c.name)}" />
      <div class="profile-name">${escapeHtml(c.name)}</div>
      <div class="profile-source">${escapeHtml(c.source)} · ${escapeHtml(c.title)}</div>
      <div class="profile-lore">${escapeHtml(c.lore)}</div>
      <div class="kv">
        <span class="chip">好感 ${s.affection}</span>
        <span class="chip">信任 ${s.trust}</span>
        <span class="chip">情绪 ${escapeHtml(s.mood)}</span>
        <span class="chip">剧情 ${escapeHtml(s.story_stage)}</span>
      </div>
      <div class="kv">${(c.personality || []).map((x) => `<span class="chip">${escapeHtml(x)}</span>`).join('')}</div>
      <div class="profile-actions">
        <button id="openCharacterMomentsBtn" class="secondary-btn full-btn">查看 TA 的朋友圈</button>
      </div>
    </div>
  `;

  document.getElementById('openCharacterMomentsBtn')?.addEventListener('click', async () => {
    closeDetailDrawer();
    await openMomentsView(c.id);
  });
}

function renderEvents() {
  if (!state.currentConversation) {
    els.detailEvents.innerHTML = '';
    return;
  }
  const items = state.currentConversation.event_reviews || [];
  if (!items.length) {
    els.detailEvents.innerHTML = `
      <div class="event-card">
        <div class="event-title">还没有事件</div>
        <div class="event-desc">继续聊天并触发关键词后，事件会在这里出现。</div>
      </div>
    `;
    return;
  }
  els.detailEvents.innerHTML = items.slice().reverse().map((item) => `
    <div class="event-card">
      <div class="event-title">${escapeHtml(item.title)}</div>
      <div class="event-desc">${escapeHtml(item.description)}</div>
      <div class="event-desc">${escapeHtml(item.reply)}</div>
      <div class="event-time">${formatTime(item.timestamp)}</div>
    </div>
  `).join('');
}

function getPendingMessages(characterId) {
  return state.pendingByCharacter[characterId] || [];
}

function createPendingMessage(content) {
  const ts = new Date().toISOString().slice(0, 19);
  const localId = `local_${Date.now()}_${Math.random()}`;
  return [
    {
      local_id: localId,
      role: 'user',
      content,
      timestamp: ts,
      meta_type: 'chat',
      send_status: 'sending',
    },
    {
      local_id: `${localId}_typing`,
      role: 'assistant',
      content: '正在输入...',
      timestamp: ts,
      meta_type: 'typing',
      send_status: 'typing',
    },
  ];
}

function markPendingFailed(characterId) {
  const arr = getPendingMessages(characterId);
  state.pendingByCharacter[characterId] = arr.filter((x) => x.meta_type !== 'typing').map((x) => ({
    ...x,
    send_status: 'failed',
  }));
}

function clearPending(characterId) {
  state.pendingByCharacter[characterId] = [];
}

function renderConversation() {
  if (!state.currentConversation || !state.currentCharacterDetail) {
    renderEmptyMain('请选择联系人', '未添加联系人时，请点击左上角 + 搜索并添加。');
    return;
  }

  els.mainHeader.classList.add('clickable');
  els.headerAvatar.src = state.currentCharacterDetail.avatar;
  els.headerAvatar.classList.remove('hidden');
  els.headerName.textContent = state.currentCharacterDetail.name;
  const summary = byId(state.currentCharacterId);
  const presenceText = summary?.presence_text || state.currentConversation.mood;
  const lastSeenText = summary?.last_seen_text || '';
  const showLastSeen = ['idle', 'busy', 'sleeping'].includes(summary?.presence_status || '');
  els.headerDesc.textContent = `${state.currentCharacterDetail.source} · ${presenceText}${showLastSeen && lastSeenText ? ` · ${lastSeenText}` : ''}`;

  els.chatArea.className = 'chat-area';
  const baseMessages = (state.currentConversation.messages || []).filter((msg) => msg.role !== 'system');
  const pendingMessages = getPendingMessages(state.currentCharacterId);
  const messages = [...baseMessages, ...pendingMessages];

  let prevTimestamp = '';
  const parts = [];
  messages.forEach((msg) => {
    if (shouldShowTimeDivider(prevTimestamp, msg.timestamp)) {
      parts.push(`<div class="time-divider"><span>${formatTime(msg.timestamp)}</span></div>`);
    }
    prevTimestamp = msg.timestamp;

    const rowClass = [
      'msg-row',
      msg.role === 'user' ? 'user' : 'assistant',
      msg.meta_type === 'event' ? 'event' : '',
      msg.meta_type === 'typing' ? 'typing' : '',
    ].filter(Boolean).join(' ');

    const avatarHtml = msg.role === 'user'
      ? getCurrentUserAvatarHtml()
      : `<img class="msg-avatar" src="${state.currentCharacterDetail.avatar}" alt="${escapeHtml(state.currentCharacterDetail.name)}" />`;

    const statusText = msg.send_status === 'sending'
      ? '<span class="msg-status">发送中...</span>'
      : msg.send_status === 'failed'
        ? '<span class="msg-status failed">发送失败</span>'
        : '';

    const bubbleHtml = `
      <div class="msg-wrap">
        <div class="msg-bubble">${escapeHtml(msg.content)}</div>
        <div class="msg-meta">${formatTime(msg.timestamp)} ${statusText}</div>
      </div>
    `;

    parts.push(`<div class="${rowClass}">${msg.role === 'user' ? `${bubbleHtml}${avatarHtml}` : `${avatarHtml}${bubbleHtml}`}</div>`);
  });

  els.chatArea.innerHTML = parts.join('');
  els.chatArea.scrollTop = els.chatArea.scrollHeight;
  renderProfile();
  renderEvents();
}

function renderAvatarTool() {
  const items = [
    {
      id: '__user__',
      name: '你',
      avatar: state.userAvatar,
      source: '用户头像',
      isUser: true,
    },
    ...state.allCharacters.map((item) => ({ ...item, isUser: false })),
  ];

  els.avatarToolGrid.innerHTML = items.map((item) => `
    <div class="avatar-tool-card" data-id="${item.id}">
      <div class="avatar-tool-top">
        ${item.avatar ? `<img class="avatar-tool-img" src="${item.avatar}" alt="${escapeHtml(item.name)}" />` : '<div class="avatar-tool-img self-avatar">你</div>'}
        <div>
          <div class="avatar-tool-name">${escapeHtml(item.name)}</div>
          <div class="avatar-tool-source">${escapeHtml(item.source || '')}</div>
        </div>
      </div>
      <input class="avatar-file-input" type="file" accept=".png,.jpg,.jpeg,.svg" />
      <div class="avatar-tool-actions">
        <button class="primary-btn upload-btn">上传头像</button>
        <button class="secondary-btn reset-btn">恢复默认</button>
      </div>
    </div>
  `).join('');

  els.avatarToolGrid.querySelectorAll('.avatar-tool-card').forEach((card) => {
    const id = card.dataset.id;
    const fileInput = card.querySelector('.avatar-file-input');
    card.querySelector('.upload-btn').addEventListener('click', async () => {
      if (!fileInput.files || !fileInput.files.length) {
        showToast('请先选择图片文件。');
        return;
      }
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      try {
        if (id === '__user__') {
          await apiPost('/api/avatar/upload-user', formData, true);
        } else {
          await apiPost(`/api/avatar/upload/${id}`, formData, true);
        }
        await refreshAllData(true);
      } catch (error) {
        showToast('上传失败：' + error.message);
      }
    });
    card.querySelector('.reset-btn').addEventListener('click', async () => {
      try {
        if (id === '__user__') {
          await apiPost('/api/avatar/reset-user');
        } else {
          await apiPost(`/api/avatar/reset/${id}`);
        }
        await refreshAllData(true);
      } catch (error) {
        showToast('恢复失败：' + error.message);
      }
    });
  });
}

function renderSettingsPage() {
  if (!state.runtime) return;

  els.settingsModeSelect.value = state.runtime.llm_mode || 'mock';
  els.settingsOllamaStatus.textContent = state.runtime.ollama_connected ? '已连接' : '未连接';
  els.settingsShortcutSelect.value = state.runtime.send_shortcut || 'enter';
  els.settingsIntervalInput.value = state.runtime.auto_check_interval_seconds || 20;
  els.settingsBirthdayInput.value = state.userProfile?.birthday_month_day || '';

  els.settingsModelSelect.innerHTML = '';
  const models = state.runtime.available_models || [];
  if (!models.length) {
    const option = document.createElement('option');
    option.value = state.runtime.ollama_model || '';
    option.textContent = state.runtime.ollama_model || '无可用模型';
    els.settingsModelSelect.appendChild(option);
  } else {
    models.forEach((model) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      option.selected = model === state.runtime.ollama_model;
      els.settingsModelSelect.appendChild(option);
    });
  }

  renderAvatarTool();
}

function renderAddContactResults() {
  const keyword = els.addContactSearchInput.value.trim().toLowerCase();

  const items = state.allCharacters
    .filter((item) => !item.is_friend)
    .filter((item) => {
      if (!keyword) return true;
      return item.name.toLowerCase().includes(keyword) || item.source.toLowerCase().includes(keyword);
    });

  if (!items.length) {
    els.addContactResults.innerHTML = '<div class="add-contact-empty">没有可添加的角色，或者已经全部添加完成。</div>';
    return;
  }

  els.addContactResults.innerHTML = items.map((item) => {
    const pending = item.friend_request_status === 'pending';
    return `
      <div class="drawer-result-item ${pending ? 'pending' : ''}" data-id="${item.id}">
        <img class="avatar" src="${item.avatar}" alt="${escapeHtml(item.name)}" />
        <div>
          <div class="session-name">${escapeHtml(item.name)}</div>
          <div class="drawer-result-subtitle">${escapeHtml(item.source)}</div>
          <div class="session-preview">${escapeHtml(item.title)}</div>
        </div>
        <button class="primary-btn add-result-btn" ${pending ? 'disabled' : ''}>
          ${pending ? '等待验证' : '添加'}
        </button>
      </div>
    `;
  }).join('');

  els.addContactResults.querySelectorAll('.drawer-result-item').forEach((node) => {
    const item = state.allCharacters.find((x) => x.id === node.dataset.id);
    const pending = item?.friend_request_status === 'pending';

    if (!pending) {
      node.querySelector('.add-result-btn').addEventListener('click', async (event) => {
        event.stopPropagation();
        await addContact(node.dataset.id);
      });

      node.addEventListener('click', async () => {
        await addContact(node.dataset.id);
      });
    }
  });
}

function openDetailDrawer(tab = 'profile') {
  if (!state.currentConversation) return;
  els.detailMask.classList.remove('hidden');
  els.detailDrawer.classList.remove('hidden');
  if (tab === 'events') {
    els.detailTabEvents.click();
  } else {
    els.detailTabProfile.click();
  }
}

function closeDetailDrawer() {
  els.detailMask.classList.add('hidden');
  els.detailDrawer.classList.add('hidden');
}

function openAddContactDrawer() {
  els.addContactMask.classList.remove('hidden');
  els.addContactDrawer.classList.remove('hidden');
  els.addContactSearchInput.value = '';
  renderAddContactResults();
  setTimeout(() => els.addContactSearchInput.focus(), 0);
}

function closeAddContactDrawer() {
  els.addContactMask.classList.add('hidden');
  els.addContactDrawer.classList.add('hidden');
}

function showContextMenu(characterId, isPinned, x, y) {
  state.contextCharacterId = characterId;
  els.contextPinBtn.textContent = isPinned ? '取消置顶' : '置顶聊天';
  els.contextMenu.style.left = `${x}px`;
  els.contextMenu.style.top = `${y}px`;
  els.contextMenu.classList.remove('hidden');
}

function hideContextMenu() {
  state.contextCharacterId = null;
  els.contextMenu.classList.add('hidden');
}

async function loadRuntime() {
  state.runtime = await apiGet('/api/runtime/status');
  state.userAvatar = state.runtime.user_avatar || '';
}

async function loadUserProfile() {
  state.userProfile = await apiGet('/api/user/profile');
}

async function loadCharacters() {
  const data = await apiGet('/api/characters');
  state.allCharacters = data.items;
  state.friendCharacters = state.allCharacters.filter((item) => item.is_friend);
}

async function openMomentsView(characterId = null) {
  state.currentMomentsCharacterId = characterId;
  await loadMomentsFeed(characterId);
  setView('moments');
}

async function loadMomentsFeed(characterId = null) {
  const url = characterId
    ? `/api/moments/character/${characterId}`
    : '/api/moments/feed';
  const data = await apiGet(url);
  state.momentsFeed = data.items || [];
}

async function loadFriendRequests() {
  const data = await apiGet('/api/friends/requests');
  state.friendRequests = data.items || [];
}

async function openConversation(characterId) {
  state.currentCharacterId = characterId;
  state.currentCharacterDetail = await apiGet(`/api/characters/${characterId}`);
  state.currentConversation = await apiGet(`/api/conversations/${characterId}`);
  const item = byId(characterId);
  if (item) item.unread_count = 0;
  renderChatList();
  renderContactList();
  if (state.currentView === 'chat') {
    renderConversation();
  }
}

async function addContact(characterId) {
  const result = await apiPost(`/api/contacts/${characterId}/add`);

  await loadCharacters();
  await loadFriendRequests();
  await loadMomentsFeed(state.currentMomentsCharacterId);

  clearMainSearch();
  els.addContactSearchInput.value = '';
  renderChatList();
  renderContactList();
  renderAddContactResults();

  if (state.currentView === 'contacts') {
    renderContactsMain();
  }

  if (state.currentView === 'moments') {
    renderMomentsSidebar();
    renderMomentsMain();
  }

  if (result.status === 'accepted') {
    closeAddContactDrawer();
    await openConversation(characterId);
    setView('chat');
    return;
  }

  if (result.status === 'pending') {
    if (state.currentView !== 'contacts') {
      setView('contacts');
    }
    state.contactsMainMode = 'new_friends';
    renderContactsMain();
    closeAddContactDrawer();
    showToast(result.message || '好友申请已发送，正在等待验证。');
    return;
  }

  showToast(result.message || '申请已提交。');
}

async function deleteContact(characterId) {
  await apiPost(`/api/contacts/${characterId}/delete`);
  if (state.currentCharacterId === characterId) {
    state.currentCharacterId = null;
    state.currentCharacterDetail = null;
    state.currentConversation = null;
    closeDetailDrawer();
  }
  await refreshAllData(false);
  if (!state.currentCharacterId) {
    renderEmptyMain('联系人已删除', '你可以点击左上角 + 重新添加。');
  }
}

async function togglePin(characterId) {
  const item = byId(characterId);
  if (!item) return;
  await apiPost(`/api/contacts/${characterId}/pin`, { value: !item.is_pinned });
  await refreshAllData(true);
}

async function sendMessage() {
  if (!state.currentCharacterId || !state.currentConversation) return;

  const sendingCharacterId = state.currentCharacterId;
  const message = els.messageInput.value.trim();
  if (!message) return;

  els.messageInput.value = '';
  els.sendBtn.disabled = true;

  try {
    await apiPost('/api/chat', {
      character_id: sendingCharacterId,
      message,
    });

    await loadCharacters();

    if (state.currentCharacterId === sendingCharacterId) {
      await openConversation(sendingCharacterId);
    } else {
      renderChatList();
      renderContactList();
    }
  } catch (error) {
    showToast('发送失败：' + error.message);
  } finally {
    els.sendBtn.disabled = false;
  }
}

async function saveSettings() {
  try {
    await apiPost('/api/runtime/update', {
      llm_mode: els.settingsModeSelect.value,
      ollama_model: els.settingsModelSelect.value,
      send_shortcut: els.settingsShortcutSelect.value,
      auto_check_interval_seconds: Number(els.settingsIntervalInput.value || 20),
    });
    await loadRuntime();
    restartProactiveTimer();
    renderSettingsPage();
    showToast('设置已保存。');
  } catch (error) {
    showToast('保存失败：' + error.message);
  }
}

async function saveBirthday() {
  const normalized = normalizeMonthDay(els.settingsBirthdayInput.value);
  if (normalized === null) {
    showToast('生日格式需要是 MM-DD，例如 08-17。');
    return;
  }

  try {
    state.userProfile = await apiPost('/api/user/profile', {
      birthday_month_day: normalized,
    });
    els.settingsBirthdayInput.value = state.userProfile.birthday_month_day || '';
    showToast(normalized ? '生日已保存。' : '生日已清空。');
  } catch (error) {
    showToast('生日保存失败：' + error.message);
  }
}

async function refreshAllData(preserveSelection = true) {
  const selected = preserveSelection ? state.currentCharacterId : null;

  await loadRuntime();
  await loadUserProfile();
  await loadCharacters();
  await loadFriendRequests();

  if (
    state.currentMomentsCharacterId &&
    !state.allCharacters.some((item) => item.id === state.currentMomentsCharacterId && item.is_friend)
  ) {
    state.currentMomentsCharacterId = null;
  }

  await loadMomentsFeed(state.currentMomentsCharacterId);

  if (selected && state.allCharacters.some((item) => item.id === selected && item.is_friend)) {
    await openConversation(selected);
  } else if (state.currentCharacterId && state.allCharacters.some((item) => item.id === state.currentCharacterId && item.is_friend)) {
    await openConversation(state.currentCharacterId);
  } else if (state.friendCharacters.length) {
    await openConversation(sortFriends(state.friendCharacters)[0].id);
  } else {
    state.currentCharacterId = null;
    state.currentCharacterDetail = null;
    state.currentConversation = null;
  }

  renderChatList();
  renderContactList();
  renderSettingsShortcutList();
  renderAddContactResults();

  if (state.currentView === 'contacts') {
    renderContactsMain();
  }

  if (state.currentView === 'moments') {
    renderMomentsSidebar();
    renderMomentsMain();
  }

  if (state.currentView === 'settings') {
    renderSettingsPage();
  }
}

async function checkProactive() {
  if (!state.runtime) return;

  const data = await apiGet(`/api/proactive/check-all${state.currentCharacterId ? `?current_character_id=${state.currentCharacterId}` : ''}`);
  const hasUpdates = data.items.some((item) => item.sent);

  if (hasUpdates) {
    const currentId = state.currentCharacterId;
    await loadCharacters();
    await loadFriendRequests();
    await loadMomentsFeed(state.currentMomentsCharacterId);

    if (currentId && state.allCharacters.some((item) => item.id === currentId && item.is_friend)) {
      await openConversation(currentId);
    }

    renderChatList();
    renderContactList();
    renderAddContactResults();

    if (state.currentView === 'contacts') {
      renderContactsMain();
    }

    if (state.currentView === 'moments') {
      renderMomentsSidebar();
      renderMomentsMain();
    }
    return;
  }

  data.items.forEach((item) => {
    const target = byId(item.character_id);
    if (target) {
      target.unread_count = item.unread_count;
      target.presence_status = item.presence_status || target.presence_status;
      target.presence_text = item.presence_text || target.presence_text;
      target.last_seen_text = item.last_seen_text || target.last_seen_text;
    }
  });

  renderChatList();
  renderContactList();
  renderAddContactResults();

  if (state.currentView === 'contacts') {
    renderContactsMain();
  }

  if (state.currentView === 'moments') {
    renderMomentsSidebar();
    renderMomentsMain();
  }
}

function restartProactiveTimer() {
  if (state.proactiveTimer) {
    clearInterval(state.proactiveTimer);
  }
  const seconds = Number(state.runtime?.auto_check_interval_seconds || 20);
  state.proactiveTimer = setInterval(checkProactive, Math.max(5, seconds) * 1000);
}

els.navChat.addEventListener('click', () => setView('chat'));
els.navContacts.addEventListener('click', () => setView('contacts'));
els.navMoments.addEventListener('click', async () => {
  await openMomentsView(state.currentMomentsCharacterId);
});
els.navSettings.addEventListener('click', () => setView('settings'));
els.openAddContactBtn.addEventListener('click', openAddContactDrawer);
els.searchInput.addEventListener('input', () => {
  if (state.currentView === 'chat') renderChatList();
  else if (state.currentView === 'contacts') renderContactList();
  else if (state.currentView === 'moments') renderMomentsSidebar();
});
els.addContactSearchInput.addEventListener('input', renderAddContactResults);
els.sendBtn.addEventListener('click', sendMessage);

els.messageInput.addEventListener('keydown', (event) => {
  const mode = state.runtime?.send_shortcut || 'enter';
  const shouldSend =
    (mode === 'enter' && event.key === 'Enter' && !event.shiftKey) ||
    (mode === 'ctrl_enter' && event.key === 'Enter' && event.ctrlKey);
  if (shouldSend) {
    event.preventDefault();
    sendMessage();
  }
});

els.mainHeader.addEventListener('click', () => {
  if (state.currentConversation && state.currentView === 'chat') openDetailDrawer('profile');
});
els.toggleProfileBtn.addEventListener('click', () => openDetailDrawer('profile'));
els.detailMask.addEventListener('click', closeDetailDrawer);
els.closeDetailBtn.addEventListener('click', closeDetailDrawer);
els.addContactMask.addEventListener('click', closeAddContactDrawer);
els.closeAddContactBtn.addEventListener('click', closeAddContactDrawer);

els.detailTabProfile.addEventListener('click', () => {
  els.detailTabProfile.classList.add('active');
  els.detailTabEvents.classList.remove('active');
  els.detailProfile.classList.remove('hidden');
  els.detailEvents.classList.add('hidden');
});

els.detailTabEvents.addEventListener('click', () => {
  els.detailTabEvents.classList.add('active');
  els.detailTabProfile.classList.remove('active');
  els.detailEvents.classList.remove('hidden');
  els.detailProfile.classList.add('hidden');
});

els.saveSettingsBtn.addEventListener('click', saveSettings);
els.saveBirthdayBtn.addEventListener('click', saveBirthday);

els.appDialogConfirmBtn.addEventListener('click', () => {
  closeAppDialog(true);
});

els.appDialogCancelBtn.addEventListener('click', () => {
  closeAppDialog(false);
});

els.appDialogMask.addEventListener('click', () => {
  closeAppDialog(false);
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !els.appDialog.classList.contains('hidden')) {
    closeAppDialog(false);
  }
});

els.refreshModelsBtn.addEventListener('click', async () => {
  await loadRuntime();
  renderSettingsPage();
});

document.addEventListener('click', (event) => {
  if (!els.contextMenu.contains(event.target)) {
    hideContextMenu();
  }
});

els.contextPinBtn.addEventListener('click', async () => {
  if (!state.contextCharacterId) return;
  await togglePin(state.contextCharacterId);
  hideContextMenu();
});

els.contextDeleteBtn.addEventListener('click', async () => {
  if (!state.contextCharacterId) return;
  const ok = await showConfirmDialog(
    '删除联系人',
    '确定要删除这个联系人吗？删除后聊天记录也会一起删除。',
    '删除',
    '取消',
    true
  );
  if (!ok) return;

  await deleteContact(state.contextCharacterId);
  showToast('联系人已删除。', 'success');
  hideContextMenu();
});

async function bootstrap() {
  await refreshAllData(false);
  restartProactiveTimer();
  setView('chat');
  if (!state.currentConversation) {
    renderEmptyMain('还没有联系人', '请点击左上角 + 搜索并添加角色联系人。');
  }
}

bootstrap().catch((error) => {
  showInfoDialog('启动失败：' + error.message);
});