<template>
  <q-layout view="hHh LpR lFf">
    <q-header elevated class="bg-primary text-white" height-hint="98">
      <q-toolbar class="bg-primary text-white q-my-md shadow-2">
        <q-toolbar-title class="q-mx-lg">
          <q-avatar size="2rem" font-size="82px">
            <img src="~assets/icon.png">
          </q-avatar>
          TVH IPTV Config
        </q-toolbar-title>
        <q-separator dark vertical inset />

        <q-tabs v-if="aioMode" no-caps align="left">
          <!--TODO: Find a way to prevent this from being destroyed from the DOM when showTvheadendAdmin is False-->
          <q-btn icon-right="fa-solid fa-window-restore" label="Show Tvheadend Backend"
                 @click="loadTvheadendAdmin = true; showTvheadendAdmin = true" />
          <q-dialog
            v-if="aioMode"
            v-model="showTvheadendAdmin"
            :class="{'hidden': !showTvheadendAdmin}"
            full-screen full-width persistent>
            <q-card class="full-screen-card">
              <q-bar class="bg-primary text-white">
                <div class="text-h6">Tvheadend Backend</div>
                <q-space />
                <q-btn
                  flat round dense
                  icon="open_in_new"
                  href="/tic-tvh/" target="_blank"
                  @click="showTvheadendAdmin = false">
                  <q-tooltip class="bg-white text-primary">
                    Open in new window
                  </q-tooltip>
                </q-btn>
                <q-btn
                  flat round dense
                  icon="close"
                  @click="showTvheadendAdmin = false">
                  <q-tooltip class="bg-white text-primary">
                    Close
                  </q-tooltip>
                </q-btn>
              </q-bar>

              <q-card-section class="full-screen-iframe">
                <iframe id="f1" ref="frame1" :src="(firstRun) ? '' : '/tic-tvh/'"></iframe>
              </q-card-section>
            </q-card>
          </q-dialog>
          <q-separator dark vertical inset />

          <q-btn-dropdown stretch flat
                          label="Show Connection Details">
            <q-list>
              <q-item-label header>EPG</q-item-label>
              <q-item clickable @click="copyUrlToClipboard(epgUrl)"
                      tabindex="0">
                <q-item-section avatar>
                  <q-avatar
                    icon="calendar_month"
                    color="secondary"
                    text-color="white" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>XMLTV Guide</q-item-label>
                  <q-item-label caption>{{ epgUrl }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="content_copy" />
                </q-item-section>
              </q-item>

              <q-separator inset spaced />

              <q-item-label header>Proxied M3U Playlists</q-item-label>
              <q-item v-for="playlist in enabledPlaylists" :key="`x.${playlist}`"
                      clickable
                      @click="copyUrlToClipboard(`${appUrl}/tic-api/tvh_playlist/${playlist.id}/channels.m3u`)"
                      tabindex="0">
                <q-item-section avatar>
                  <q-avatar
                    v-if="true"
                    icon="playlist_play"
                    color="secondary"
                    text-color="white" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ playlist.name }}</q-item-label>
                  <q-item-label caption>{{ appUrl }}/tic-api/tvh_playlist/{{ playlist.id }}/channels.m3u</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="content_copy" />
                </q-item-section>
              </q-item>

              <q-separator inset spaced />

              <q-item-label header>Proxied HDHomeRun Tuner Emulators</q-item-label>
              <q-item v-for="playlist in enabledPlaylists" :key="`x.${playlist}`"
                      clickable @click="copyUrlToClipboard(`${appUrl}/tic-api/hdhr_device/${playlist.id}`)"
                      tabindex="0">
                <q-item-section avatar>
                  <q-avatar size="2rem" font-size="82px">
                    <img src="~assets/hd-icon.png">
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ playlist.name }}</q-item-label>
                  <q-item-label caption>{{ appUrl }}/tic-api/hdhr_device/{{ playlist.id }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="content_copy" />
                </q-item-section>
              </q-item>

            </q-list>
          </q-btn-dropdown>
          <q-separator dark vertical inset />
        </q-tabs>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      elevated
      side="left" behavior="desktop"
    >
      <q-list>
        <q-item-label header>
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
        <q-item-label style="padding-left:10px" header>
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
import aioStartupTasks from 'src/mixins/aioFunctionsMixin';
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
    const tasksArePaused = ref(false);
    const {pendingTasks, pendingTasksStatus} = pollForBackgroundTasks();
    const {firstRun, aioMode} = aioStartupTasks();

    const loadTvheadendAdmin = ref(true);
    const showTvheadendAdmin = ref(false);
    const appUrl = ref(window.location.origin);
    const epgUrl = ref(`${window.location.origin}/tic-web/epg.xml`);

    const enabledPlaylists = ref([]);

    const copyUrlToClipboard = (textToCopy) => {
      copyToClipboard(textToCopy).then(() => {
        // Notify user of success
        $q.notify({
          color: 'green',
          textColor: 'white',
          icon: 'done',
          message: 'URL copied to clipboard',
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
        appUrl.value = response.data.data.app_url;
        epgUrl.value = `${response.data.data.app_url}/tic-web/epg.xml`;
      }).catch(() => {
      });
      // Fetch playlists list
      axios({
        method: 'get',
        url: '/tic-api/playlists/get',
      }).then((response) => {
        enabledPlaylists.value = response.data.data;
      }).catch(() => {
      });
    });

    return {
      firstRun,
      aioMode,
      loadTvheadendAdmin,
      showTvheadendAdmin,
      enabledPlaylists,
      appUrl,
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
