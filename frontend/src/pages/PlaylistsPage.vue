<template>
  <q-page padding>

    <div class="q-pa-none">

      <q-card flat>
        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="row q-gutter-xs q-mt-xs justify-between">
            <div class="col-auto">
              <q-btn-group>
                <q-btn
                  @click="openPlaylistSettings(null)"
                  class=""
                  color="primary"
                  icon-right="add"
                  label="Add Playlist" />
              </q-btn-group>
            </div>
          </div>
        </q-card-section>

        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="q-gutter-sm">
            <q-list bordered separator class="rounded-borders">

              <q-item
                v-for="(playlist, index) in listOfPlaylists"
                v-bind:key="index"
                :class="playlist.enabled ? '' : 'bg-grey-3'">

                <q-item-section avatar top>
                  <q-icon name="playlist_play" color="" size="34px" />
                </q-item-section>

                <q-item-section top>
                  <q-item-label lines="1">
                    <span class="text-weight-medium">{{ playlist.name }}</span>
                    <span class="text-grey-8"> - {{ playlist.url }}</span>
                  </q-item-label>
                  <q-item-label caption lines="1">
                    Maximum Connections: {{ playlist.connections }}
                  </q-item-label>
                  <q-item-label lines="1" class="q-mt-xs text-body2 text-primary">
                    <span class="text-weight-bold text-uppercase">HDHomeRun Device URL: </span>
                    <span
                      class="cursor-pointer"
                      @click="copyUrlToClipboard(`${appUrl}/tic-api/hdhr_device/${playlist.id}`)">
                      {{ appUrl }}/tic-api/hdhr_device/{{ playlist.id }}
                    </span>
                  </q-item-label>
                </q-item-section>

                <q-item-section top side>
                  <div class="text-grey-8 q-gutter-xs">
                    <q-btn-dropdown
                      flat dense rounded
                      size="12px"
                      no-icon-animation
                      dropdown-icon="more_vert">
                      <q-list>

                        <q-item clickable v-close-popup @click="updatePlaylist(playlist.id)">
                          <q-item-section avatar>
                            <q-icon color="info" name="update" />
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Update</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item clickable v-close-popup @click="openPlaylistSettings(playlist.id)">
                          <q-item-section avatar>
                            <q-icon color="grey-8" name="tune" />
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Configure</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item clickable v-close-popup @click="removePlaylist(playlist.id)">
                          <q-item-section avatar>
                            <q-icon color="negative" name="delete" />
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Delete</q-item-label>
                          </q-item-section>
                        </q-item>

                      </q-list>
                    </q-btn-dropdown>

                  </div>
                </q-item-section>

              </q-item>

            </q-list>
          </div>
        </q-card-section>
      </q-card>

    </div>

  </q-page>
</template>

<script>
import { defineComponent, ref } from "vue";
import axios from "axios";
import PlaylistInfoDialog from "components/PlaylistInfoDialog.vue";
import { copyToClipboard } from "quasar";

export default defineComponent({
  name: "PlaylistsPage",

  setup() {
    return {};
  },
  data() {
    return {
      listOfPlaylists: ref([]),
      appUrl: ref(`${window.location.origin}`)
    };
  },
  methods: {
    fetchSettings: function() {
      // Fetch current settings
      axios({
        method: "get",
        url: "/tic-api/playlists/get"
      }).then((response) => {
        this.listOfPlaylists = response.data.data;
      }).catch(() => {
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to fetch settings",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    },
    openPlaylistSettings: function(playlistId) {
      if (!playlistId) {
        playlistId = null;
      }
      // Display the dialog
      this.$q.dialog({
        component: PlaylistInfoDialog,
        componentProps: {
          playlistId: playlistId
        }
      }).onOk((payload) => {
        this.fetchSettings();
      }).onDismiss(() => {
      });
    },
    updatePlaylist: function(playlistId) {
      // Fetch current settings
      this.$q.loading.show();
      axios({
        method: "POST",
        url: `/tic-api/playlists/update/${playlistId}`
      }).then((response) => {
        this.$q.loading.hide();
        this.$q.notify({
          color: "positive",
          position: "top",
          icon: "cloud_done",
          message: "Playlist update queued",
          timeout: 200
        });
      }).catch(() => {
        this.$q.loading.hide();
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to queue update of playlist",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    },
    removePlaylist: function(playlistId) {
      // Fetch current settings
      this.$q.loading.show();
      axios({
        method: "DELETE",
        url: `/tic-api/playlists/${playlistId}/delete`
      }).then((response) => {
        this.$q.loading.hide();
        this.$q.notify({
          color: "positive",
          position: "top",
          icon: "cloud_done",
          message: "Playlist removed",
          timeout: 200
        });
        this.fetchSettings();
      }).catch(() => {
        this.$q.loading.hide();
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to remove playlist",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    },
    copyUrlToClipboard: function(textToCopy) {
      copyToClipboard(textToCopy)
        .then(() => {
          // Notify user of success
          this.$q.notify({
            color: "green",
            textColor: "white",
            icon: "done",
            message: "EPG URL copied to clipboard"
          });
        })
        .catch((err) => {
          // Handle the error (e.g., clipboard API not supported)
          console.error("Copy failed", err);
          this.$q.notify({
            color: "red",
            textColor: "white",
            icon: "error",
            message: "Failed to copy URL"
          });
        });
    }
  },
  created() {
    this.fetchSettings();
  }
});
</script>
