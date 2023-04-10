<template>
  <q-page padding>

    <div class="q-pa-none">

      <!--      <h4 class="q-ma-none">{{ $t('headers.librarySettings') }}</h4>-->

      <div class="row">
        <div class="col-sm-12 col-md-10 col-lg-8">
          <div :class="$q.platform.is.mobile ? 'q-ma-sm' : 'q-ma-sm q-pa-md'">

            <q-form
              @submit="save"
              class="q-gutter-md"
            >

              <h5 class="q-mb-none">TVheadend Configuration</h5>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhHost === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="tvhHost"
                  label="TVheadend Host"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhPort === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="tvhPort"
                  label="TVheadend Port"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhUsername === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="tvhUsername"
                  label="TVheadend Admin Username"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tvhPassword === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="tvhPassword"
                  label="TVheadend Admin Password"
                  :type="isPwd ? 'password' : 'text'">
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>
              </div>

              <div>
                <q-btn label="Save" type="submit" color="primary"/>
              </div>

            </q-form>
          </div>
        </div>
      </div>
    </div>


  </q-page>
</template>

<script>
import {defineComponent, ref} from 'vue'
import axios from "axios";

export default defineComponent({
  name: 'TvheadendPage',

  setup() {
    return {}
  },
  data() {
    return {
      tvhHost: ref(null),
      tvhPort: ref(null),
      tvhUsername: ref(null),
      tvhPassword: ref(null),
      isPwd: ref(true),
    }
  },
  methods: {
    fetchSettings: function () {
      // Fetch current settings
      axios({
        method: 'get',
        url: '/tic-api/tvheadend/get-settings'
      }).then((response) => {
        this.tvhHost = response.data.data.host
        this.tvhPort = response.data.data.port
        this.tvhUsername = response.data.data.username
        this.tvhPassword = response.data.data.password
      }).catch(() => {
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: "Failed to fetch settings",
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
      });
    },
    save: function () {
      // TODO: Add settings for setting default ffmpeg pipe args and schedule refresh
      // settings:
      //   default_ffmpeg_pipe_args: -hide_banner -loglevel error -probesize 10M -analyzeduration
      //     0 -fpsprobesize 0 -i [URL] -c copy -metadata service_name=[SERVICE_NAME] -f mpegts
      //     pipe:1
      //     refresh_schedule: 0
      // Save settings
      let data = {
        settings: {
          tvheadend: {
            host: this.tvhHost,
            port: this.tvhPort,
            username: this.tvhUsername,
            password: this.tvhPassword,
          },
        }
      }
      axios({
        method: 'post',
        url: '/tic-api/save-settings',
        data: data
      }).then((response) => {
        // Save success, show feedback
        this.fetchSettings();
        this.$q.notify({
          color: 'positive',
          position: 'top',
          icon: 'cloud_done',
          message: 'Saved',
          timeout: 200
        })
      }).catch(() => {
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to save settings',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
      });
    },
  },
  created() {
    this.fetchSettings();
  }
})
</script>
