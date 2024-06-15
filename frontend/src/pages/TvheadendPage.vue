<template>
  <q-page padding>

    <div class="q-pa-none">

      <div class="row">
        <div class="col-sm-12 col-md-10 col-lg-8">
          <div :class="$q.platform.is.mobile ? 'q-ma-sm' : 'q-ma-sm q-pa-md'">

            <q-form
              @submit="save"
              class="q-gutter-md"
            >

              <h5 class="q-mb-none">TVheadend Connection</h5>

              <div class="q-gutter-sm">
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
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhPort === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="tvhPort"
                  label="TVheadend Port"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhUsername === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="tvhUsername"
                  label="TVheadend Admin Username"
                  hint="This is optional. If your TVH server is not configured with an admin user, leave this blank."
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhPassword === null"
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

              <q-separator />

              <h5 class="q-mb-none">TVheadend Stream Config</h5>

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

              <h5 class="q-mb-none">TVheadend Users Config</h5>

              <div class="q-gutter-sm">
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
                v-if="createClientUser"
                class="q-gutter-sm">
                <div class="q-gutter-sm">
                  <q-skeleton
                    v-if="clientUsername === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="clientUsername"
                    :rules="[clientUsername => !!clientUsername || 'Username cannot be blank']"
                    label="TVheadend Client Username"
                  />
                </div>
                <div class="q-gutter-sm">
                  <q-skeleton
                    v-if="clientPassword === null"
                    type="QInput" />
                  <q-input
                    v-else
                    v-model="clientPassword"
                    :rules="[clientPassword => !!clientPassword || 'A password is required']"
                    :type="hideclientPassword ? 'password' : 'text'"
                    label="TVheadend Client Password"
                    hint="This is optional. If your TVH server is not configured with an admin user, leave this blank.">
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

              <div>
                <q-btn label="Save" type="submit" color="primary" class="q-mt-lg" />
              </div>

            </q-form>
          </div>
        </div>
      </div>
    </div>


  </q-page>
</template>

<script>
import { defineComponent, ref } from "vue";
import axios from "axios";

export default defineComponent({
  name: "TvheadendPage",

  setup() {
    return {};
  },
  data() {
    return {
      // UI Elements
      hideTvhPassword: ref(true),
      hideclientPassword: ref(true),

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
        tvhPort: "9981",
        tvhUsername: "",
        tvhPassword: "",
        appUrl: window.location.origin,
        hlsProxyPrefix: "http://" + window.location.host.split(":")[0] + ":9987",
        enableStreamBuffer: true,
        defaultFfmpegPipeArgs: "-hide_banner -loglevel error -probesize 10M -analyzeduration 0 -fpsprobesize 0 -i [URL] -c copy -metadata service_name=[SERVICE_NAME] -f mpegts pipe:1",
        createClientUser: false,
        clientUsername: "user",
        clientPassword: "user"
      })
    };
  },
  methods: {
    convertToCamelCase(str) {
      return str.replace(/([-_][a-z])/g, (group) => group.toUpperCase().replace("-", "").replace("_", ""));
    },
    fetchSettings: function() {
      // Fetch current settings
      axios({
        method: "get",
        url: "/tic-api/get-settings"
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
          if (typeof value !== "object") {
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
          color: "negative",
          position: "top",
          message: "Failed to fetch settings",
          icon: "report_problem",
          actions: [{ icon: "close", color: "white" }]
        });
      });
    },
    save: function() {
      // Save settings
      let postData = {
        settings: {
          tvheadend: {}
        }
      };

      // Dynamically populate settings from component data, falling back to defaults
      Object.keys(this.defSet).forEach((key) => {
        const snakeCaseKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);

        if (key.startsWith("tvh")) {
          // Handle tvheadend settings
          const tvhKey = key.replace("tvh", "").toLowerCase(); // Convert tvhHost to host, etc.
          postData.settings.tvheadend[tvhKey] = this[key] ?? this.defSet[key];
        } else {
          // Handle other application settings
          postData.settings[snakeCaseKey] = this[key] ?? this.defSet[key];
        }
      });

      axios({
        method: "POST",
        url: "/tic-api/save-settings",
        data: postData
      }).then((response) => {
        // Save success, show feedback
        this.fetchSettings();
        this.$q.notify({
          color: "positive",
          position: "top",
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
