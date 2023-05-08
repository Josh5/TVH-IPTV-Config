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

              <q-separator/>

              <div class="q-gutter-sm">
                <q-checkbox v-model="enableStreamBuffer" label="Enable Stream Buffer"/>
              </div>

              <div
                v-if="enableStreamBuffer"
                class="q-gutter-sm">
                <q-skeleton
                  v-if="defaultPipeArgs === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="defaultPipeArgs"
                  label="Default FFmpeg Stream Buffer Options"
                  hint="Note: [URL] and [SERVICE_NAME] will be replaced with the stream source and the service name respectively."
                />
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
      enableStreamBuffer: ref(true),
      defaultPipeArgs: ref(null)
    }
  },
  methods: {
    fetchSettings: function () {
      // Fetch current settings
      axios({
        method: 'get',
        url: '/tic-api/tvheadend/get-settings'
      }).then((response) => {
        this.tvhHost = response.data.data.tvheadend.host
        this.tvhPort = response.data.data.tvheadend.port
        this.tvhUsername = response.data.data.tvheadend.username
        this.tvhPassword = response.data.data.tvheadend.password
        this.enableStreamBuffer = response.data.data.enable_stream_buffer
        this.defaultPipeArgs = response.data.data.default_ffmpeg_pipe_args
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
      // Save settings
      let data = {
        settings: {
          tvheadend: {
            host: this.tvhHost,
            port: this.tvhPort,
            username: this.tvhUsername,
            password: this.tvhPassword,
          },
          enable_stream_buffer: this.enableStreamBuffer,
          default_ffmpeg_pipe_args: this.defaultPipeArgs,
        }
      }
      axios({
        method: 'POST',
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
