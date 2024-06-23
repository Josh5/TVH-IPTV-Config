<template>
  <!--
    TODO:
      - Configure mobile view such that the form elements on the settings tab are not padded
      - Fix header wrapping on mobile view
    -->

  <!-- START DIALOG CONFIG
  Right fullscreen pop-up
  Note: Update template q-dialog ref="" value

  All Platforms:
   - Swipe right to dismiss
  Desktop:
   - Width 700px
   - Minimise button top-right
  Mobile:
   - Full screen
   - Back button top-left
  -->
  <q-dialog
    ref="playlistInfoDialogRef"
    :maximized="$q.platform.is.mobile"
    :transition-show="$q.platform.is.mobile ? 'jump-left' : 'slide-left'"
    :transition-hide="$q.platform.is.mobile ? 'jump-right' : 'slide-right'"
    full-height
    position="right"
    @before-hide="beforeDialogHide"
    @hide="onDialogHide">

    <q-card
      v-touch-swipe.touch.right="hide"
      :style="$q.platform.is.mobile ? 'max-width: 100vw;' : 'max-width: 95vw;'"
      style="width:700px;">

      <q-card-section class="bg-card-head">
        <div class="row items-center no-wrap">
          <div
            v-if="$q.platform.is.mobile"
            class="col">
            <q-btn
              color="grey-7"
              dense
              round
              flat
              icon="arrow_back"
              v-close-popup>
            </q-btn>
          </div>

          <div class="col">
            <div class="text-h6 text-blue-10">
              Playlist Settings
            </div>
          </div>

          <div
            v-if="!$q.platform.is.mobile"
            class="col-auto">
            <q-btn
              color="grey-7"
              dense
              round
              flat
              icon="arrow_forward"
              v-close-popup>
              <q-tooltip class="bg-white text-primary">Close</q-tooltip>
            </q-btn>
          </div>
        </div>
      </q-card-section>
      <!-- END DIALOG CONFIG -->

      <q-separator />

      <div class="row">
        <div class="col col-12 q-pa-lg">
          <div>
            <q-form
              @submit="save"
              class="q-gutter-md"
            >
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="enabled === null"
                  type="QCheckbox" />
                <q-checkbox v-model="enabled" label="Enabled" />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="name === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="name"
                  label="Playlist Name"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="url === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="url"
                  type="textarea"
                  label="Playlist URL"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="connections === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model.number="connections"
                  type="number"
                  label="Connections"
                  style="max-width: 200px"
                />
              </div>
              <div class="q-gutter-sm">
                <q-item tag="label" v-ripple>
                  <q-item-section avatar>
                    <q-skeleton
                      v-if="useHlsProxy === null"
                      type="QCheckbox" />
                    <q-checkbox
                      v-else
                      v-model="useHlsProxy" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Use HLS proxy</q-item-label>
                    <q-item-label caption>TVH-IPTV-Config comes with an inbuilt HLS (M3U8) playlist proxy. Selecting
                      this will modify all playlist URLs to use it.
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </div>
              <div
                v-if="useHlsProxy"
                class="q-gutter-sm">
                <q-item tag="label" v-ripple>
                  <q-item-section avatar>
                    <q-skeleton
                      v-if="useCustomHlsProxy === null"
                      type="QCheckbox" />
                    <q-checkbox
                      v-else
                      v-model="useCustomHlsProxy" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Use a custom HLS Proxy path</q-item-label>
                    <q-item-label caption>If unselected, the playlist will be prefixed with the inbuilt HLS proxy URL.
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </div>
              <div
                v-if="useHlsProxy && useCustomHlsProxy"
                class="q-gutter-sm">
                <q-input
                  v-model="hlsProxyPath"
                  label="HLS Proxy Path"
                  hint="Note: Insert [URL] or [B64_URL] in the URL as a placeholder for the playlist URL. If '[B64 URL]' is used, then the URL will be base64 encoded before inserting"
                />
              </div>

              <div>
                <q-btn label="Save" type="submit" color="primary" />
              </div>

            </q-form>

          </div>
        </div>
      </div>

    </q-card>

  </q-dialog>
</template>

<script>

import axios from "axios";
import { ref } from "vue";

export default {
  name: "PlaylistInfoDialog",
  props: {
    playlistId: {
      type: String
    }
  },
  emits: [
    // REQUIRED
    "ok", "hide", "path"
  ],
  data() {
    return {
      enabled: ref(null),
      name: ref(null),
      url: ref(null),
      connections: ref(null),
      useHlsProxy: ref(null),
      useCustomHlsProxy: ref(null),
      hlsProxyPath: ref(null)
    };
  },
  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.playlistInfoDialogRef.show();
      if (this.playlistId) {
        this.fetchPlaylistData();
        return;
      }
      // Set default values for new playlist
      this.enabled = true;
      this.name = "";
      this.url = "";
      this.connections = 1;
      this.useHlsProxy = false;
      this.useCustomHlsProxy = false;
      this.hlsProxyPath = window.location.origin + '/tic-hls-proxy.m3u8?url=[URL]';
    },

    // following method is REQUIRED
    // (don't change its name --> "hide")
    hide() {
      this.$refs.playlistInfoDialogRef.hide();
    },

    onDialogHide() {
      // required to be emitted
      // when QDialog emits "hide" event
      this.$emit("ok", {});
      this.$emit("hide");
    },

    fetchPlaylistData: function() {
      // Fetch from server
      axios({
        method: "GET",
        url: "/tic-api/playlists/settings/" + this.playlistId
      }).then((response) => {
        this.enabled = response.data.data.enabled;
        this.name = response.data.data.name;
        this.url = response.data.data.url;
        this.connections = response.data.data.connections;
        this.useHlsProxy = response.data.data.use_hls_proxy;
        this.useCustomHlsProxy = response.data.data.use_custom_hls_proxy;
        this.hlsProxyPath = response.data.data.hls_proxy_path;
      });
    },
    save: function() {
      let url = "/tic-api/playlists/new";
      if (this.playlistId) {
        url = `/tic-api/playlists/settings/${this.playlistId}/save`;
      }
      let data = {
        enabled: this.enabled,
        name: this.name,
        url: this.url,
        connections: this.connections,
        use_hls_proxy: this.useHlsProxy,
        use_custom_hls_proxy: this.useCustomHlsProxy,
        hls_proxy_path: this.hlsProxyPath
      };
      axios({
        method: "POST",
        url: url,
        data: data
      }).then((response) => {
        // Save success, show feedback
        this.$q.notify({
          color: "positive",
          icon: "cloud_done",
          message: "Saved",
          timeout: 200
        });
        this.hide();
      }).catch(() => {
        this.$q.notify({
          color: "negative",
          position: "top",
          message: "Failed to save settings",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    },

    updateAndTriggerSave: function(key, value) {
      for (let i = 0; i < this.settings.length; i++) {
        if (this.settings[i].key_id === key) {
          this.settings[i].value = value;
          break;
        }
      }
      this.save();
    }
  },
  watch: {
    uuid(value) {
      if (value.length > 0) {
        this.currentUuid = this.uuid;
      }
    }
  }
};
</script>

<style>

</style>
