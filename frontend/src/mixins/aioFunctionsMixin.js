import {ref, onBeforeUnmount} from 'vue';
import {Notify, useQuasar} from 'quasar';
import axios from 'axios';

export default function aioStartupTasks() {
  const $q = useQuasar();
  const firstRun = ref(null);
  const aioMode = ref(false);

  let pingInterval;
  const pingBackend = () => {
    axios({
      method: 'GET',
      url: '/tic-tvh/ping',
      timeout: 4000,
    }).then((response) => {
      if (response.status === 200 && response.data.includes('PONG')) {
        if (firstRun.value) {
          setTimeout(saveFirstRunSettings, 10000);
        } else {
          $q.loading.hide();
          clearInterval(pingInterval);
        }
      } else {
        $q.loading.show({
          message: `Tvheadend backend returned status code ${response.status}...`,
        });
      }
    }).catch(() => {
      $q.loading.show({
        message: 'Waiting for Tvheadend backend to start...',
      });
    });
  };

  const saveFirstRunSettings = () => {
    let postData = {
      settings: {
        'first_run': true,
        'app_url': window.location.origin,
      },
    };
    axios({
      method: 'POST',
      url: '/tic-api/save-settings',
      data: postData,
    }).then((response) => {
      // Reload page to properly trigger the auth refresh
      location.reload();
    });
  };

  const checkTvhStatus = () => {
    // Fetch current settings
    axios({
      method: 'get',
      url: '/tic-api/get-settings',
    }).then((response) => {
      firstRun.value = response.data.data.first_run;
      axios({
        method: 'get',
        url: '/tic-api/tvh-running',
      }).then((response) => {
        aioMode.value = response.data.data.running;
        if (response.data.data.running) {
          // Fetch settings
          $q.loading.show({
            message: 'Checking status of Tvheadend backend...',
          });
          pingBackend();
          pingInterval = setInterval(pingBackend, 5000);
        }
      }).catch(() => {
      });
    }).catch(() => {
    });
  };

  checkTvhStatus();

  onBeforeUnmount(() => {
    clearInterval(pingInterval);
  });

  return {
    firstRun,
    aioMode,
  };
}
