<template>
  <q-page padding>

    <div class="q-pa-none">

      <div class="row">
        <div class="col-sm-7 col-md-8">
          <div :class="$q.platform.is.mobile ? 'q-ma-sm' : 'q-ma-sm q-pa-md'">

            <q-form @submit="save" class="q-gutter-md">

              <h5 v-if="aioMode === false" class="text-primary q-mb-none">TVheadend Connection</h5>

              <div v-if="aioMode === false">
                <div>
                  <q-skeleton
                    v-if="tvhHost === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="tvhHost"
                    label="TVheadend Host"
                    hint="Set Ensure you also set this to an hostname or IP that is accessible to all applications that will connect to TVH. Not just this application."
                  />
                </div>
                <div>
                  <q-skeleton
                    v-if="tvhPort === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="tvhPort"
                    label="TVheadend Port"
                  />
                </div>
                <div>
                  <q-skeleton
                    v-if="tvhUsername === null || aioMode === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="tvhUsername"
                    :readonly="aioMode"
                    label="TVheadend Admin Username"
                    hint="This is optional. If your TVH server is not configured with an admin user, leave this blank."
                  />
                </div>
                <div>
                  <q-skeleton
                    v-if="tvhPassword === null || aioMode === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="tvhPassword"
                    label="TVheadend Admin Password"
                    hint="This is optional. If your TVH server is not configured with an admin user, leave this blank."
                    :type="hideTvhPassword ? 'password' : 'text'">
                    <template v-slot:append>
                      <q-icon
                        :name="hideTvhPassword ? 'visibility_off' : 'visibility'"
                        class="cursor-pointer"
                        @click="hideTvhPassword = !hideTvhPassword"
                      />
                    </template>
                  </q-input>
                </div>
                <q-card
                  v-if="(tvhPassword === null || tvhPassword === '' ) && (aioMode === null || aioMode === false ) "
                  class="warning-card q-mt-md">
                  <q-card-section>
                    <div class="text-h6">Warning:</div>
                    It is recommended that you secure your TVH installation.
                    You really should add an admin user to your TVH server and then come back here.
                  </q-card-section>
                </q-card>

                <q-separator />
              </div>

              <h5 class="text-primary q-mb-none">TVheadend Users Config</h5>

              <div v-if="aioMode === false"
              >
                <q-item tag="label" dense class="q-pl-none q-mr-none">
                  <q-item-section avatar>
                    <q-checkbox v-model="createClientUser" val="createClientUser" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Create a client user</q-item-label>
                    <q-item-label caption>If checked, this will create a user for clients to connect to TVH.
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </div>

              <div
                v-if="createClientUser || aioMode === true"
              >
                <div>
                  <q-skeleton
                    v-if="clientUsername === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="clientUsername"
                    :rules="[clientUsername => !!clientUsername || 'Username cannot be blank']"
                    label="TVheadend Client Username"
                    :hint="(aioMode === true) ? `Since an admin user is configured, a client user is required.`: ``"
                  />
                </div>
                <div>
                  <q-skeleton
                    v-if="clientPassword === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="clientPassword"
                    :rules="[clientPassword => !!clientPassword || 'A password is required']"
                    :type="hideclientPassword ? 'password' : 'text'"
                    label="TVheadend Client Password"
                    :hint="(aioMode === true) ? `Since an admin user is configured, a client password is required.`: `This is optional. If your TVH server is not configured with an admin user, leave this blank.`"
                  >
                    <template v-slot:append>
                      <q-icon
                        :name="hideclientPassword ? 'visibility_off' : 'visibility'"
                        class="cursor-pointer"
                        @click="hideclientPassword = !hideclientPassword"
                      />
                    </template>
                  </q-input>
                </div>
              </div>


              <h5 class="text-primary q-mb-none">Stream Config</h5>

              <div>
                <q-item tag="label" dense class="q-pl-none q-mr-none">
                  <q-item-section avatar>
                    <q-checkbox v-model="enableStreamBuffer" val="createClientUser" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Enable Stream Buffer</q-item-label>
                    <q-item-label caption>
                      Adds a FFmpeg pipe to the TVheadend stream source.
                      This can improve stability from multiple client connections, but will introduce latency for the
                      first client that connects.
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </div>

              <div
                v-if="enableStreamBuffer"
                class="sub-setting">
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

              <div>
                <q-btn label="Save" type="submit" color="primary" class="q-mt-lg" />
              </div>

            </q-form>
          </div>
        </div>
        <div class="col-sm-5 col-md-4">
          <q-card class="note-card q-my-md">
            <q-card-section>
              <div class="text-h5 q-mb-none">Setup Steps:</div>
              <q-list>

                <q-separator inset spaced />

                <q-item>
                  <q-item-section>
                    <q-item-label>
                      1. Configure the Client username and password.
                      This will be applied to the playlists and guide data supplied to any clients.
                    </q-item-label>
                  </q-item-section>
                </q-item>

              </q-list>
            </q-card-section>
            <q-card-section>
              <div class="text-h5 q-mb-none">Notes:</div>
              <q-list>

                <q-separator inset spaced />

                <q-item-label class="text-primary">
                  TVheadend Users Config:
                </q-item-label>
                <q-item>
                  <q-item-section>
                    <q-item-label>
                      If you want to have additional client users created, they can be added in the TVheadend Backend.
                    </q-item-label>
                  </q-item-section>
                </q-item>

                <q-separator inset spaced />

                <q-item-label class="text-primary">
                  Stream Config:
                </q-item-label>
                <q-item>
                  <q-item-section>
                    <q-item-label>
                      The <b>Stream Buffer</b> option is not required in order for multiple clients to view a single
                      channel as one connection on that playlist through the TVheadend backend.
                    </q-item-label>
                  </q-item-section>
                </q-item>

              </q-list>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>


  </q-page>
</template>

<script>
import {defineComponent, ref} from 'vue';
import axios from 'axios';
import aioStartupTasks from 'src/mixins/aioFunctionsMixin';

export default defineComponent({
  name: 'TvheadendPage',

  setup() {
    return {};
  },
  data() {
    return {
      // UI Elements
      hideTvhPassword: ref(true),
      hideclientPassword: ref(true),
      aioMode: ref(null),

      // Application Settings
      tvhHost: ref(null),
      tvhPort: ref(null),
      tvhUsername: ref(null),
      tvhPassword: ref(null),
      appUrl: ref(null),
      hlsProxyPrefix: ref(null),
      enableStreamBuffer: ref(null),
      defaultFfmpegPipeArgs: ref(null),
      createClientUser: ref(null),
      clientUsername: ref(null),
      clientPassword: ref(null),

      // Defaults
      defSet: ref({
        tvhHost: window.location.hostname,
        tvhPort: '9981',
        tvhUsername: '',
        tvhPassword: '',
        appUrl: window.location.origin,
        hlsProxyPrefix: 'http://' + window.location.host.split(':')[0] + ':9987',
        enableStreamBuffer: true,
        defaultFfmpegPipeArgs: '-hide_banner -loglevel error -probesize 10M -analyzeduration 0 -fpsprobesize 0 -i [URL] -c copy -metadata service_name=[SERVICE_NAME] -f mpegts pipe:1',
        createClientUser: false,
        clientUsername: 'user',
        clientPassword: 'user',
      }),
    };
  },
  methods: {
    convertToCamelCase(str) {
      return str.replace(/([-_][a-z])/g, (group) => group.toUpperCase().replace('-', '').replace('_', ''));
    },
    fetchSettings: function() {
      // Fetch current settings
      axios({
        method: 'get',
        url: '/tic-api/get-settings',
      }).then((response) => {
        // TVH Connection settings are specially nested (for some reason)
        this.tvhHost = response.data.data.tvheadend.host;
        this.tvhPort = response.data.data.tvheadend.port;
        this.tvhUsername = response.data.data.tvheadend.username;
        this.tvhPassword = response.data.data.tvheadend.password;

        // All other application settings are here
        const appSettings = response.data.data;

        // Iterate over the settings and set values
        Object.entries(appSettings).forEach(([key, value]) => {
          if (typeof value !== 'object') {
            const camelCaseKey = this.convertToCamelCase(key);
            this[camelCaseKey] = value;
          }
        });

        // Fill in any missing values from defaults
        Object.keys(this.defSet).forEach((key) => {
          if (this[key] === undefined || this[key] === null) {
            this[key] = this.defSet[key];
          }
        });

      }).catch(() => {
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to fetch settings',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}],
        });
      });
      const {firstRun, aioMode} = aioStartupTasks();
      this.aioMode = aioMode;
    },
    save: function() {
      // Save settings
      let postData = {
        settings: {
          tvheadend: {},
        },
      };
      // Dynamically populate settings from component data, falling back to defaults
      Object.keys(this.defSet).forEach((key) => {
        const snakeCaseKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);

        if (key.startsWith('tvh')) {
          // Handle tvheadend settings
          const tvhKey = key.replace('tvh', '').toLowerCase(); // Convert tvhHost to host, etc.
          postData.settings.tvheadend[tvhKey] = this[key] ?? this.defSet[key];
        } else {
          // Handle other application settings
          postData.settings[snakeCaseKey] = this[key] ?? this.defSet[key];
        }
      });
      this.$q.loading.show();
      axios({
        method: 'POST',
        url: '/tic-api/save-settings',
        data: postData,
      }).then((response) => {
        this.$q.loading.hide();
        // Save success, show feedback
        this.fetchSettings();
        this.$q.notify({
          color: 'positive',
          icon: 'cloud_done',
          message: 'Saved',
          timeout: 200,
        });
      }).catch(() => {
        this.$q.loading.hide();
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to save settings',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}],
        });
      });
    },
  },
  created() {
    this.fetchSettings();
  },
});
</script>
