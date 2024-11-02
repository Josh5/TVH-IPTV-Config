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
                    Connections Limit: {{ playlist.connections }}
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

      <q-card flat>
        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <q-form @submit="save">

            <h5 class="q-mt-none q-mb-none">Stream Config</h5>

            <div class="q-gutter-sm">
              <q-item tag="label" dense class="q-pl-none q-mr-none">
                <q-item-section avatar>
                  <q-checkbox v-model="enableStreamBuffer" val="createClientUser" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Enable Stream Buffer</q-item-label>
                </q-item-section>
              </q-item>
            </div>

            <div
              v-if="enableStreamBuffer"
              class="q-gutter-sm">
              <q-skeleton
                v-if="defaultFfmpegPipeArgs === null"
                type="QInput" />
              <q-input
                v-else
                v-model="defaultFfmpegPipeArgs"
                label="Default FFmpeg Stream Buffer Options"
                hint="Note: [URL] and [SERVICE_NAME] will be replaced with the stream source and the service name respectively."
              />
            </div>

            <q-separator />

            <div>
              <q-btn label="Save" type="submit" color="primary" class="q-mt-lg" />
            </div>

          </q-form>
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
      appUrl: ref(`${window.location.origin}`),

      // Application Settings
      enableStreamBuffer: ref(null),
      defaultFfmpegPipeArgs: ref(null)
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
      axios({
        method: "get",
        url: "/tic-api/get-settings"
      }).then((response) => {
        this.appUrl = response.data.data.app_url;
        this.enableStreamBuffer = response.data.data.enable_stream_buffer;
        this.defaultFfmpegPipeArgs = response.data.data.default_ffmpeg_pipe_args;
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
            message: "URL copied to clipboard"
          });
        })
        .catch((err) => {
          // Handle the error (e.g., clipboard API not supported)et
          console.error("Copy failed", err);
          this.$q.notify({
            color: "red",
            textColor: "white",
            icon: "error",
            message: "Failed to copy URL"
          });
        });
    },
    save: function() {
      // Save settings
      let postData = {
        settings: {
          app_url: this.appUrl,
          enable_stream_buffer: this.enableStreamBuffer,
          default_ffmpeg_pipe_args: this.defaultFfmpegPipeArgs
        }
      };
      axios({
        method: "POST",
        url: "/tic-api/save-settings",
        data: postData
      }).then((response) => {
        // Save success, show feedback
        this.fetchSettings();
        this.$q.notify({
          color: "positive",
          icon: "cloud_done",
          message: "Saved",
          timeout: 200
        });
      }).catch(() => {
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to save settings",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    }
  },
  created() {
    this.fetchSettings();
  }
});
</script>
