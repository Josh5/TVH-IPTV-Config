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

              <h5 class="q-mb-none">Connections</h5>

              <div class="q-gutter-sm q-mt-sm">
                <q-skeleton
                  v-if="appUrl === null"
                  type="QInput" />
                <q-input
                  v-else
                  v-model="appUrl"
                  label="TVH IPTV Config Host"
                  hint="This is needed for other applications to connect to TIC as a proxy. This will be used in the generated XMLTV EPG and HDHomeRun proxy. Ensure this is set to something that external services can use to reach TIC."
                />
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
  name: "GeneralPage",

  setup() {
    return {};
  },
  data() {
    return {
      // Application Settings
      appUrl: ref(null),

      // Defaults
      defSet: ref({
        appUrl: window.location.origin
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
        settings: {}
      };
      // Dynamically populate settings from component data, falling back to defaults
      Object.keys(this.defSet).forEach((key) => {
        const snakeCaseKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
        postData.settings[snakeCaseKey] = this[key] ?? this.defSet[key];
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
