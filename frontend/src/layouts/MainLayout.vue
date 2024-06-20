<template>
  <q-layout view="hHh LpR lFf">
    <q-header elevated class="bg-primary text-white" height-hint="98">
      <q-toolbar class="q-px-xl">
        <q-toolbar-title>
          TVH IPTV Config
        </q-toolbar-title>

        <q-tabs v-if="aioMode" no-caps align="left">
          <q-btn flat label="Show Tvheadend Admin" @click="loadTvheadendAdmin = true; showTvheadendAdmin = true" />
        </q-tabs>

        <q-dialog
          v-if="aioMode"
          v-model="loadTvheadendAdmin"
          :class="{'hidden': !showTvheadendAdmin}"
          full-screen full-width persistent>
          <q-card class="full-screen-card">
            <q-bar class="bg-primary text-white">
              <div class="text-h6">Tvheadend Admin</div>
              <q-space />
              <q-btn flat round dense icon="close" @click="showTvheadendAdmin = false" />
            </q-bar>

            <q-card-section class="full-screen-iframe">
              <iframe id="f1" ref="frame1" :src="'/tic-tvh/'"></iframe>
            </q-card-section>
          </q-card>
        </q-dialog>

        <div
          @click="copyUrlToClipboard"
          class="cursor-pointer">
          <span
            class="q-ml-sm text-weight-bold text-orange-7">
            EPG URL:
          </span>
          <span
            class="text-orange-3">
            {{ epgUrl }}
          </span>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      elevated
      side="left" behavior="desktop"
    >
      <q-list>
        <q-item-label
          header
        >
          <!--          Essential Links-->
        </q-item-label>

        <EssentialLink
          v-for="link in essentialLinks"
          :key="link.title"
          v-bind="link"
        />
      </q-list>

      <q-separator class="q-my-lg" />

      <q-list>
        <q-item-label
          style="padding-left:10px"
          header>
          <q-btn
            flat round dense
            :color="pendingTasksStatus === 'paused' ? '' : ''"
            :icon="pendingTasksStatus === 'paused' ? 'play_circle' : 'pause_circle'"
            :tooltip="'running'"
            @click="tasksPauseResume">
            <q-tooltip class="bg-accent">
              Background task queue {{ pendingTasksStatus }}
            </q-tooltip>
          </q-btn>
          Upcoming background tasks:
        </q-item-label>
        <q-item
          v-for="(task, index) in pendingTasks"
          :key="index">
          <q-item-section avatar>
            <q-icon
              color="primary"
              :class="pendingTasksStatus === 'paused' ? 'rotating-icon' : ''"
              :name="pendingTasksStatus === 'paused' ? 'motion_photos_on' : task.icon" />
          </q-item-section>

          <q-item-section>
            <q-item-label caption>{{ task.name }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<style>
.rotating-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.hidden {
  display: none;
}

.full-screen-card {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  padding: 1px;
}

.full-screen-iframe {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.full-screen-iframe iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.note-card {
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.warning-card {
  background-color: #fdddcd;
  border: 1px solid #ffdfc4;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>

<script>
import {defineComponent, onMounted, ref} from 'vue';
import EssentialLink from 'components/EssentialLink.vue';
import pollForBackgroundTasks from 'src/mixins/backgroundTasksMixin';
import axios from 'axios';
import {copyToClipboard, useQuasar} from 'quasar';

const linksList = [
  {
    title: 'General',
    caption: 'General TVH-IPTV-Config settings',
    icon: 'tune',
    link: '/general',
  },
  {
    title: 'TVheadend',
    caption: 'Connect to TVheadend',
    icon: 'img:https://avatars.githubusercontent.com/u/1908588?s=280&v=4',
    link: '/tvheadend',
  },
  {
    title: 'Playlists',
    caption: 'Configure Playlist Sources',
    icon: 'playlist_play',
    link: '/playlists',
  },
  {
    title: 'EPGs',
    caption: 'Configure a list of EPG sources',
    icon: 'calendar_month',
    link: '/epgs',
  },
  {
    title: 'Channels',
    caption: 'Configure Channels',
    icon: 'queue_play_next',
    link: '/channels',
  },
];

export default defineComponent({
  name: 'MainLayout',

  components: {
    EssentialLink,
  },

  setup() {
    const $q = useQuasar();
    const leftDrawerOpen = ref(false);
    const {pendingTasks, pendingTasksStatus} = pollForBackgroundTasks();
    const tasksArePaused = ref(false);

    const aioMode = ref(false);
    const loadTvheadendAdmin = ref(true);
    const showTvheadendAdmin = ref(false);
    const epgUrl = ref(`${window.location.origin}/tic-web/epg.xml`);

    const copyUrlToClipboard = () => {
      copyToClipboard(epgUrl.value).then(() => {
        // Notify user of success
        $q.notify({
          color: 'green',
          textColor: 'white',
          icon: 'done',
          message: 'EPG URL copied to clipboard',
        });
      }).catch((err) => {
        // Handle the error (e.g., clipboard API not supported)
        console.error('Copy failed', err);
        $q.notify({
          color: 'red',
          textColor: 'white',
          icon: 'error',
          message: 'Failed to copy URL',
        });
      });
    };

    const tasksPauseResume = () => {
      // tasksArePaused.value = !tasksArePaused.value;
      // Your logic to toggle pause/resume the tasks
      axios({
        method: 'GET',
        url: '/tic-api/toggle-pause-background-tasks',
      }).catch(() => {
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to pause task queue',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}],
        });
      });
    };

    onMounted(() => {
      // Fetch current settings
      axios({
        method: 'get',
        url: '/tic-api/get-settings',
      }).then((response) => {
        epgUrl.value = `${response.data.data.app_url}/tic-web/epg.xml`;
      }).catch(() => {
      });
      axios({
        method: 'get',
        url: '/tic-api/tvh-running',
      }).then((response) => {
        aioMode.value = response.data.data.running;
      }).catch(() => {
      });
    });

    return {
      aioMode,
      loadTvheadendAdmin,
      showTvheadendAdmin,
      epgUrl,
      essentialLinks: linksList,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
      copyUrlToClipboard,
      pendingTasks,
      pendingTasksStatus,
      tasksPauseResume,
      tasksArePaused,
    };
  },
});
</script>
