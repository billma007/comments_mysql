(function () {
    const mountId = 'hexo-comments-root';
    const root = document.getElementById(mountId);
    if (!root) {
        console.warn(`[comments.js] 未找到 #${mountId} 容器。`);
        return;
    }

    const config = window.HEX0_COMMENTS_CONFIG || {};
    const apiBase = config.apiBase || window.location.origin;
    const postId = config.postId || root.dataset.postId || window.location.pathname;

    const style = document.createElement('style');
    style.textContent = `
        #${mountId} .hx-shell { border: 1px solid #e5e7eb; padding: 1rem; border-radius: 0.5rem; background: #fff; }
        #${mountId} .hx-login { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
        #${mountId} input, #${mountId} textarea { border: 1px solid #d1d5db; border-radius: 0.375rem; padding: 0.5rem; }
        #${mountId} button { background: #111827; color: #fff; border: none; border-radius: 0.375rem; padding: 0.5rem 0.75rem; cursor: pointer; }
        #${mountId} .hx-comment { border-top: 1px solid #e5e7eb; padding: 0.75rem 0; }
        #${mountId} .hx-comment:first-child { border-top: none; }
        #${mountId} .hx-comment__meta { font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem; }
        #${mountId} .hx-comment__actions { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem; }
        #${mountId} .hx-replies { margin-left: 1rem; border-left: 1px solid #e5e7eb; padding-left: 0.75rem; }
        #${mountId} .hx-like[data-liked="yes"] { background: #2563eb; }
        #${mountId} .hx-status { min-height: 1.25rem; font-size: 0.9rem; color: #2563eb; margin-bottom: 0.5rem; }
    `;
    document.head.appendChild(style);

    const html = `
        <div class="hx-shell">
            <div class="hx-status" id="hx-status"></div>
            <div class="hx-login">
                <input id="hx-login-username" placeholder="用户名" />
                <input id="hx-login-password" placeholder="密码" type="password" />
                <button id="hx-login-button">登录</button>
                <button id="hx-register-button">注册</button>
            </div>
            <textarea id="hx-comment-input" rows="4" placeholder="写下你的想法..."></textarea>
            <button id="hx-submit">发布评论</button>
            <div class="hx-list" id="hx-list"></div>
        </div>
    `;
    root.innerHTML = html;

    const statusEl = document.getElementById('hx-status');
    const listEl = document.getElementById('hx-list');
    const commentInput = document.getElementById('hx-comment-input');
    const loginUser = document.getElementById('hx-login-username');
    const loginPass = document.getElementById('hx-login-password');

    const storageKey = 'hexo-comment-token';

    function setStatus(message) {
        statusEl.textContent = message || '';
    }

    function getToken() {
        return window.localStorage.getItem(storageKey);
    }

    function saveToken(token) {
        window.localStorage.setItem(storageKey, token);
    }

    async function fetchJSON(url, options) {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error((await response.text()) || '请求失败');
        }
        return response.json();
    }

    async function loadComments() {
        setStatus('正在加载评论...');
        try {
            const token = getToken();
            const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
            const data = await fetchJSON(`${apiBase}/api/comments?post_id=${encodeURIComponent(postId)}`, {
                headers: headers || {}
            });
            renderComments(data.items || []);
            setStatus('');
        } catch (err) {
            setStatus('加载评论失败');
            console.error(err);
        }
    }

    function renderComments(items) {
        listEl.innerHTML = '';
        if (!items.length) {
            listEl.innerHTML = '<p>还没有评论。</p>';
            return;
        }
        items.forEach(item => renderComment(item, listEl));
    }

    function renderComment(item, parent) {
        const container = document.createElement('div');
        container.className = 'hx-comment';
        const header = document.createElement('div');
        header.className = 'hx-comment__meta';
        header.textContent = `${item.username} • ${item.created_at}`;
        const body = document.createElement('p');
        body.textContent = item.content;
        const actions = document.createElement('div');
        actions.className = 'hx-comment__actions';
        const likeBtn = document.createElement('button');
        likeBtn.className = 'hx-like';
        likeBtn.dataset.id = item.id;
        likeBtn.dataset.liked = item.liked_by_viewer ? 'yes' : 'no';
        likeBtn.textContent = `👍 ${item.like_count}`;
        const replyBtn = document.createElement('button');
        replyBtn.className = 'hx-reply';
        replyBtn.dataset.id = item.id;
        replyBtn.textContent = '回复';
        actions.appendChild(likeBtn);
        actions.appendChild(replyBtn);
        container.appendChild(header);
        container.appendChild(body);
        container.appendChild(actions);
        parent.appendChild(container);

        likeBtn.addEventListener('click', () => handleLike(item.id));
        replyBtn.addEventListener('click', () => handleReply(item));

        if (item.replies && item.replies.length) {
            const repliesContainer = document.createElement('div');
            repliesContainer.className = 'hx-replies';
            item.replies.forEach(reply => renderComment(reply, repliesContainer));
            container.appendChild(repliesContainer);
        }
    }

    async function handleAuth(endpoint) {
        setStatus(endpoint === 'login' ? '正在登录...' : '正在注册...');
        try {
            const data = await fetchJSON(`${apiBase}/api/users/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: loginUser.value,
                    password: loginPass.value,
                }),
            });
            if (data.token) {
                saveToken(data.token);
                setStatus(`欢迎 ${data.username}！`);
            } else {
                setStatus('注册成功，请登录。');
            }
        } catch (err) {
            setStatus(err.message);
        }
    }

    async function submitComment() {
        const token = getToken();
        if (!token) {
            setStatus('评论前请先登录。');
            return;
        }
        if (!commentInput.value.trim()) {
            setStatus('内容不能为空。');
            return;
        }
        setStatus('正在提交评论...');
        try {
            await fetchJSON(`${apiBase}/api/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    post_id: postId,
                    content: commentInput.value,
                }),
            });
            commentInput.value = '';
            setStatus('评论已发布！');
            loadComments();
        } catch (err) {
            setStatus(err.message);
        }
    }

    async function handleLike(commentId) {
        const token = getToken();
        if (!token) {
            setStatus('点赞前请先登录。');
            return;
        }
        setStatus('正在更新点赞...');
        try {
            await fetchJSON(`${apiBase}/api/comments/${commentId}/like`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            await loadComments();
        } catch (err) {
            setStatus(err.message);
        }
    }

    async function handleReply(item) {
        const token = getToken();
        if (!token) {
            setStatus('回复前请先登录。');
            return;
        }
        const content = prompt(`回复 ${item.username}：`);
        if (!content || !content.trim()) {
            return;
        }
        setStatus('正在发布回复...');
        try {
            await fetchJSON(`${apiBase}/api/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    post_id: postId,
                    content: content.trim(),
                    parent_comment_id: item.id,
                }),
            });
            setStatus('回复已发布！');
            loadComments();
        } catch (err) {
            setStatus(err.message);
        }
    }

    document.getElementById('hx-login-button').addEventListener('click', () => handleAuth('login'));
    document.getElementById('hx-register-button').addEventListener('click', () => handleAuth('register'));
    document.getElementById('hx-submit').addEventListener('click', submitComment);

    loadComments();
})();
