const API_BASE = '/api';

class API {
    static get token() {
        return localStorage.getItem('access_token');
    }

    static set token(value) {
        localStorage.setItem('access_token', value);
    }

    static clearToken() {
        localStorage.removeItem('access_token');
    }

    static get headers() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            ...options,
            headers: { ...this.headers, ...options.headers },
        };

        // If body is FormData, let browser set Content-Type
        if (options.body instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // Token expired or invalid
                this.clearToken();
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Something went wrong');
            }

            return response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    static async login(email, password) {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const data = await this.request('/auth/login', {
            method: 'POST',
            body: formData,
        });

        if (data.access_token) {
            this.token = data.access_token;
        }
        return data;
    }

    static async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    static async getMe() {
        return this.request('/users/me');
    }

    static async getPosts() {
        return this.request('/posts');
    }

    static async createPost(content, imageFile) {
        const formData = new FormData();
        formData.append('content', content);
        formData.append('image', imageFile);

        return this.request('/posts', {
            method: 'POST',
            body: formData,
        });
    }

    static async deletePost(postId) {
        return this.request(`/posts/${postId}`, {
            method: 'DELETE',
        });
    }

    static async likePost(postId) {
        return this.request(`/posts/${postId}/like`, {
            method: 'POST',
        });
    }

    static async getPost(postId) {
        return this.request(`/posts/${postId}`);
    }

    static async createComment(postId, comment) {
        return this.request(`/posts/${postId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ comment }),
        });
    }
}
