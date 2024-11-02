<template>
  <q-page padding>

    <div class="q-pa-none">

      <div class="row">
        <div class="col-sm-7 col-md-8">
          <div :class="$q.platform.is.mobile ? 'q-ma-sm' : 'q-ma-sm q-pa-md'">

            <q-form @submit="save" class="q-gutter-md">

              <h5 class="text-primary q-mb-none">Authentication</h5>

              <div v-if="aioMode === false"
                   class="q-gutter-sm">
                <q-item tag="label" dense class="q-pl-none q-mr-none">
                  <q-item-section avatar>
                    <q-checkbox v-model="enableAdminUser" val="enableAdminUser" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Enable authentication on TIC web interface</q-item-label>
                  </q-item-section>
                </q-item>
              </div>

              <div
                v-if="aioMode === true || enableAdminUser === true"
                class="q-gutter-sm">
                <q-skeleton
                  v-if="adminUsername === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="adminUsername"
                  readonly
                  label="Admin Username"
                  :hint="(aioMode === true) ? `Note: This admin user is for both TIC and TVheadend (username cannot be modified).` : `Note: Username cannot be modified.`"
                />
              </div>
              <div
                v-if="aioMode === true || enableAdminUser === true"
                class="q-gutter-sm">
                <q-skeleton
                  v-if="adminPassword === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="adminPassword"
                  label="Admin Password"
                  :hint="(aioMode === true) ? `Note: The admin password configured here will be also applied to TVheadend.` : ``"
                  :type="hideAdminPassword ? 'password' : 'text'">
                  <template v-slot:append>
                    <q-icon
                      :name="hideAdminPassword ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer"
                      @click="hideAdminPassword = !hideAdminPassword"
                    />
                  </template>
                </q-input>
              </div>

              <h5 class="text-primary q-mb-none">Connections</h5>

              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="appUrl === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="appUrl"
                  label="TIC Host"
                  hint="External access host & port. This is needed for other applications to connect to TIC. This will be used in the generated XMLTV EPG, Custom Playlist and HDHomeRun Tuner Emulators. Ensure this is set to something that external services can use to reach TIC."
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

                <q-separator inset spaced v-if="aioMode === true" />

                <q-item v-if="aioMode === true">
                  <q-item-section>
                    <q-item-label>
                      1. Configure the Admin username and password. This user should not be used for streaming clients.
                    </q-item-label>
                  </q-item-section>
                </q-item>
                <q-item v-if="aioMode === true">
                  <q-item-section>
                    <q-item-label>
                      2. Configure the connection details that clients should use to connect to TIC.
                      This will be applied to the playlists and guide data supplied to these clients.
                    </q-item-label>
                  </q-item-section>
                </q-item>

              </q-list>
            </q-card-section>
            <q-card-section>
              <div class="text-h5 q-mb-none">Notes:</div>
              <q-list>

                <q-separator inset spaced v-if="aioMode === true" />

                <q-item-label class="text-primary" v-if="aioMode === true">
                  Authentication:
                </q-item-label>
                <q-item v-if="aioMode === true">
                  <q-item-section>
                    <q-item-label>
                      Authentication is shared between TIC and the TVheadend Backend.
                      Updating the admin user here will also update the admin user in TVheadend.
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
  name: 'GeneralPage',

  setup() {
    return {};
  },
  data() {
    return {
      // UI Elements
      aioMode: ref(null),
      hideAdminPassword: ref(true),
      prevAdminPassword: ref(null),

      // Application Settings
      appUrl: ref(null),
      enableAdminUser: ref(null),
      adminUsername: ref('admin'),
      adminPassword: ref(null),

      // Defaults
      defSet: ref({
        appUrl: window.location.origin,
        enableAdminUser: false,
        adminPassword: '',
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
        // Write the previous admin password as the one fetched
        this.prevAdminPassword = this.adminPassword;
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
        settings: {},
      };
      // Dynamically populate settings from component data, falling back to defaults
      Object.keys(this.defSet).forEach((key) => {
        const snakeCaseKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
        postData.settings[snakeCaseKey] = this[key] ?? this.defSet[key];
      });
      this.$q.loading.show();
      axios({
        method: 'POST',
        url: '/tic-api/save-settings',
        data: postData,
      }).then((response) => {
        this.$q.loading.hide();
        // Save success, show feedback
        this.$q.notify({
          color: 'positive',
          icon: 'cloud_done',
          message: 'Saved',
          timeout: 200,
        });
        if (this.prevAdminPassword !== this.adminPassword) {
          // Reload page to properly trigger the auth refresh
          this.$router.push({name: 'login'});
        }
        this.fetchSettings();
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
