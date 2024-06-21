<template>
  <q-layout view="hHh LpR lFf">
  </q-layout>
</template>

<script>
import axios from 'axios';
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {useQuasar} from 'quasar';

export default {
  setup() {
    const $q = useQuasar();
    const router = useRouter();

    const checkAuth = async () => {
      $q.loading.show();
      try {
        // Initial request to check authentication status
        const response = await axios.get('/tic-api/require-auth');
        if (response.status === 200) {
          // Navigate to the general route after successful authentication
          $q.loading.hide();
          await router.push({path: '/'});
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          // Authentication required
          $q.loading.hide();
          location.reload();
        } else {
          console.error('Error during authentication check', error);
          $q.loading.hide();
          location.reload();
        }
      }
    };

    onMounted(() => {
      checkAuth();
    });

    return {};
  },
};
</script>
