import {defineStore} from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    appRuntimeKey: null,
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
        if (this.isAuthenticated) {
          let payload = await response.data;
          if (this.appRuntimeKey === null) {
            this.appRuntimeKey = payload.runtime_key;
          } else if (this.appRuntimeKey !== payload.runtime_key) {
            console.log('Reload window as backed was restarted');
            location.reload();
          }
        }
      } catch (error) {
        console.error(error);
        this.isAuthenticated = false;
      } finally {
        this.loading = false;
      }
    },
  },
});
