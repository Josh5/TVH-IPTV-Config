import {defineStore} from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    loading: false,
  }),
  actions: {
    async checkAuthentication() {
      this.loading = true;
      try {
        const response = await axios.get('/tic-api/check-auth', {
          cache: 'no-store',
          credentials: 'include',
        });
        this.isAuthenticated = response.status === 200;
      } catch (error) {
        this.isAuthenticated = false;
      } finally {
        this.loading = false;
      }
    },
  },
});
