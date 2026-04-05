// File: frontend/src/services/auth.js

import api from './api';

class AuthService {
  constructor() {
    this.tokenKey = 'access_token';
    this.refreshTokenKey = 'refresh_token';
    this.userKey = 'user';
    this.refreshInterval = null;
  }

  async login(email, password) {
    try {
      const response = await api.post('/api/auth/login', {
        email,
        password
      });
      
      if (response.data.access_token) {
        // Store tokens
        localStorage.setItem(this.tokenKey, response.data.access_token);
        localStorage.setItem(this.refreshTokenKey, response.data.refresh_token);
        
        // Fetch user data
        const user = await this.getCurrentUser();
        localStorage.setItem(this.userKey, JSON.stringify(user));
        
        // Setup auto-refresh
        this.setupAutoRefresh(response.data.expires_in);
        
        return user;
      }
      throw new Error('No access token received');
    } catch (error) {
      console.error('Login error:', error.response?.data || error.message);
      throw error;
    }
  }

  async register(username, email, password, skillLevel = 'beginner') {
    try {
      const response = await api.post('/api/auth/register', {
        username,
        email,
        password,
        skill_level: skillLevel
      });
      
      // Auto login after registration
      await this.login(email, password);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error.response?.data || error.message);
      throw error;
    }
  }

  async getCurrentUser() {
    try {
      const response = await api.get('/api/auth/me');
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        // Try to refresh token
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry getting user
          const retryResponse = await api.get('/api/auth/me');
          return retryResponse.data;
        }
      }
      throw error;
    }
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    if (!refreshToken) return false;

    try {
      const response = await api.post('/api/auth/refresh', {
        refresh_token: refreshToken
      });

      if (response.data.access_token) {
        localStorage.setItem(this.tokenKey, response.data.access_token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Refresh token error:', error);
      this.logout();
      return false;
    }
  }

  setupAutoRefresh(expiresIn) {
    // Clear existing interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    // Refresh 5 minutes before expiry
    const refreshTime = (expiresIn - 300) * 1000;
    
    this.refreshInterval = setInterval(() => {
      this.refreshToken();
    }, refreshTime);
  }

  logout() {
    // Clear all stored data
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
    
    // Clear refresh interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
    
    // Redirect to login
    window.location.href = '/login';
  }

  isAuthenticated() {
    const token = localStorage.getItem(this.tokenKey);
    return !!token;
  }

  getUser() {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }
}

export const authService = new AuthService();
export default authService;
