document.addEventListener('DOMContentLoaded', async () => {
    const path = window.location.pathname;

    // Auth Check & UI Update
    await updateAuthUI();

    // Event Listeners for Global Elements
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            API.clearToken();
            window.location.href = '/login';
        });
    }

    // Page Specific Logic
    if (path === '/' || path === '/index.html') {
        initFeedPage();
    } else if (path === '/login') {
        initLoginPage();
    } else if (path === '/register') {
        initRegisterPage();
    }
});

async function updateAuthUI() {
    const isLoggedIn = !!API.token;
    const user = isLoggedIn ? await API.getMe().catch(() => null) : null;

    // If token exists but invalid, API.getMe() might fail/redirect
    // Assuming API.request handles 401 redirect

    if (user) {
        document.getElementById('nav-login').classList.add('hidden');
        document.getElementById('nav-register').classList.add('hidden');
        document.getElementById('nav-logout').classList.remove('hidden');

        // Save current user info for permission checks
        window.currentUser = user;
    } else {
        document.getElementById('nav-login').classList.remove('hidden');
        document.getElementById('nav-register').classList.remove('hidden');
        document.getElementById('nav-logout').classList.add('hidden');
        API.clearToken(); // Ensure clean state
    }
}

function initLoginPage() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            await API.login(email, password);
            window.location.href = '/';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
        }
    });
}

function initRegisterPage() {
    const form = document.getElementById('register-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirm = document.getElementById('password-confirm').value;
        const errorDiv = document.getElementById('register-error');

        if (password !== confirm) {
            errorDiv.textContent = "비밀번호가 일치하지 않습니다.";
            errorDiv.classList.remove('hidden');
            return;
        }

        try {
            await API.register(email, password);
            alert("회원가입 성공! 로그인해주세요.");
            window.location.href = '/login';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('hidden');
        }
    });
}

async function initFeedPage() {
    const isLoggedIn = !!window.currentUser;
    const authSection = document.getElementById('auth-section');
    const guestSection = document.getElementById('guest-section');
    const feedContainer = document.getElementById('feed-container');
    const postForm = document.getElementById('post-form');

    if (isLoggedIn) {
        authSection.classList.remove('hidden');
        guestSection.classList.add('hidden');
    } else {
        authSection.classList.add('hidden');
        guestSection.classList.remove('hidden');
    }

    // Load Posts
    try {
        const posts = await API.getPosts();
        renderPosts(posts, feedContainer);
    } catch (error) {
        feedContainer.innerHTML = '<p style="text-align: center; color: var(--color-error);">게시물을 불러오는데 실패했습니다.</p>';
    }

    // Post Creation
    if (postForm) {
        postForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = document.getElementById('post-content').value;
            const imageFile = document.getElementById('post-image').files[0];

            if (!imageFile) return;

            try {
                await API.createPost(content, imageFile);
                postForm.reset();
                // Reload posts
                const posts = await API.getPosts();
                renderPosts(posts, feedContainer);
            } catch (error) {
                alert("게시물 작성 실패: " + error.message);
            }
        });
    }
}

function renderPosts(posts, container) {
    container.innerHTML = '';
    const template = document.getElementById('post-template');

    if (posts.length === 0) {
        container.innerHTML = '<p style="text-align: center; grid-column: 1/-1;">첫 게시물을 작성해보세요!</p>';
        return;
    }

    posts.forEach(post => {
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.post-card');

        clone.querySelector('.post-image').src = post.img_path;
        clone.querySelector('.post-author').textContent = post.user_email;
        clone.querySelector('.post-date').textContent = new Date(post.created_at + "Z").toLocaleString(); // UTC to Local
        clone.querySelector('.post-text').textContent = post.content;
        clone.querySelector('.like-count').textContent = post.like_count;
        clone.querySelector('.comment-count').textContent = post.comment_count;

        // Delete Button
        const deleteBtn = clone.querySelector('.btn-delete');
        if (window.currentUser && window.currentUser.id === post.user_id) {
            deleteBtn.classList.remove('hidden');
            deleteBtn.addEventListener('click', async () => {
                if (confirm("정말 삭제하시겠습니까?")) {
                    await API.deletePost(post.id);
                    card.remove();
                }
            });
        }

        // Like Button
        const likeBtn = clone.querySelector('.btn-like');
        likeBtn.addEventListener('click', async () => {
            if (!window.currentUser) {
                alert("로그인이 필요합니다.");
                return;
            }
            try {
                const res = await API.likePost(post.id);
                const countSpan = likeBtn.querySelector('.like-count');
                let count = parseInt(countSpan.textContent);
                countSpan.textContent = res.liked ? count + 1 : count - 1;
            } catch (error) {
                console.error(error);
            }
        });

        // Show/Hide Comments
        const commentBtn = clone.querySelector('.btn-comment');
        const commentsSection = clone.querySelector('.post-comments');
        commentBtn.addEventListener('click', async () => {
            if (commentsSection.classList.contains('hidden')) {
                commentsSection.classList.remove('hidden');
                await loadComments(post.id, commentsSection.querySelector('.comment-list'));
            } else {
                commentsSection.classList.add('hidden');
            }
        });

        // Add Comment
        const commentForm = clone.querySelector('.comment-form');
        commentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!window.currentUser) {
                alert("로그인이 필요합니다.");
                return;
            }
            const input = commentForm.querySelector('.comment-input');
            try {
                await API.createComment(post.id, input.value);
                input.value = '';
                // Reload comments
                await loadComments(post.id, commentsSection.querySelector('.comment-list'));
                // Update count
                const countSpan = clone.querySelector('.comment-count'); // Note: this reference might be lost if we re-render whole list.
                // Ideally we update DOM locally.
                const postCard = e.target.closest('.post-card');
                const currentCount = parseInt(postCard.querySelector('.comment-count').textContent);
                postCard.querySelector('.comment-count').textContent = currentCount + 1;

            } catch (error) {
                alert("댓글 작성 실패");
            }
        });

        container.appendChild(clone);
    });
}

async function loadComments(postId, listContainer) {
    try {
        const data = await API.getPost(postId);
        const comments = data.comments;
        listContainer.innerHTML = '';
        comments.forEach(comment => {
            const li = document.createElement('li');
            li.style.marginBottom = 'var(--space-2xs)';
            li.innerHTML = `<strong class="text-step--1">${comment.user_email}</strong> <span class="text-step--1">${comment.comment}</span>`;
            listContainer.appendChild(li);
        });
    } catch (error) {
        console.error("댓글 로딩 실패", error);
    }
}
