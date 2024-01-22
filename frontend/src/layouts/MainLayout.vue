<template>
  <q-layout view="lhh LpR lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          TVH IPTV Config
        </q-toolbar-title>

        <div>
          <span class="q-ml-sm text-weight-bold">EPG URL:</span>
          <span
            class="cursor-pointer"
            @click="copyUrlToClipboard"
          >{{ epgUrl }}</span>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
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
</style>

<script>
import { defineComponent, ref } from "vue";
import EssentialLink from "components/EssentialLink.vue";
import pollForBackgroundTasks from "src/mixins/backgroundTasksMixin";
import axios from "axios";
import { copyToClipboard, useQuasar } from "quasar";

const linksList = [
  {
    title: "TVheadend",
    caption: "Connect to TVheadend",
    icon: "img:https://avatars.githubusercontent.com/u/1908588?s=280&v=4",
    link: "/tvheadend"
  },
  {
    title: "Playlists",
    caption: "Configure Playlist Sources",
    icon: "playlist_play",
    link: "/playlists"
  },
  {
    title: "EPGs",
    caption: "Configure a list of EPG sources",
    icon: "calendar_month",
    link: "/epgs"
  },
  {
    title: "Channels",
    caption: "Configure Channels",
    icon: "queue_play_next",
    link: "/channels"
  }
];

export default defineComponent({
  name: "MainLayout",

  components: {
    EssentialLink
  },

  setup() {
    const $q = useQuasar();
    const leftDrawerOpen = ref(false);
    const { pendingTasks, pendingTasksStatus } = pollForBackgroundTasks();
    const tasksArePaused = ref(false);

    const epgUrl = ref(`${window.location.origin}/tic-web/epg.xml`);

    const copyUrlToClipboard = () => {
      copyToClipboard(epgUrl.value)
        .then(() => {
          // Notify user of success
          $q.notify({
            color: "green",
            textColor: "white",
            icon: "done",
            message: "EPG URL copied to clipboard"
          });
        })
        .catch((err) => {
          // Handle the error (e.g., clipboard API not supported)
          console.error("Copy failed", err);
          $q.notify({
            color: "red",
            textColor: "white",
            icon: "error",
            message: "Failed to copy URL"
          });
        });
    };

    const tasksPauseResume = () => {
      // tasksArePaused.value = !tasksArePaused.value;
      // Your logic to toggle pause/resume the tasks
      axios({
        method: "GET",
        url: "/tic-api/toggle-pause-background-tasks"
      }).catch(() => {
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to pause task queue",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    };

    return {
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
      tasksArePaused
    };
  }
});
</script>
