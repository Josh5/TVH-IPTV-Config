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
    ref="epgInfoDialogRef"
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

      <q-separator/>

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
                  type="QCheckbox"/>
                <q-checkbox v-model="enabled" label="Enabled"/>
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="name === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="name"
                  label="Playlist Name"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="url === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="url"
                  type="textarea"
                  label="Playlist URL"
                />
              </div>

              <div>
                <q-btn label="Save" type="submit" color="primary"/>
              </div>

            </q-form>

          </div>
        </div>
      </div>

    </q-card>

  </q-dialog>
</template>

<script>
/*
tab          - The tab to display first ['info', 'settings']
*/

import axios from "axios";
import {ref} from "vue";

export default {
  name: 'EpgInfoDialog',
  props: {
    epgId: {
      type: String
    }
  },
  emits: [
    // REQUIRED
    'ok', 'hide', 'path'
  ],
  data() {
    return {
      enabled: ref(null),
      name: ref(null),
      url: ref(null),
    }
  },
  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.epgInfoDialogRef.show();
      if (this.epgId) {
        this.fetchPlaylistData();
        return
      }
      this.enabled = true
      this.name = ''
      this.url = ''
    },

    // following method is REQUIRED
    // (don't change its name --> "hide")
    hide() {
      this.$refs.epgInfoDialogRef.hide();
    },

    onDialogHide() {
      // required to be emitted
      // when QDialog emits "hide" event
      this.$emit('ok', {})
      this.$emit('hide')
    },

    fetchPlaylistData: function () {
      // Fetch from server
      axios({
        method: 'get',
        url: '/tic-api/epgs/settings/' + this.epgId,
      }).then((response) => {
        this.enabled = response.data.data.enabled
        this.name = response.data.data.name
        this.url = response.data.data.url
      });
    },
    save: function () {
      let epgId = this.epgId
      if (!epgId) {
        epgId = (Math.random() + 1).toString(36).substring(5);
      }
      let data = {
        epgs: {
          [epgId]: {
            enabled: this.enabled,
            name: this.name,
            url: this.url,
          }
        }
      }
      axios({
        method: 'post',
        url: `/tic-api/epgs/settings/${epgId}/save`,
        data: data
      }).then((response) => {
        // Save success, show feedback
        this.$q.notify({
          color: 'positive',
          position: 'top',
          icon: 'cloud_done',
          message: 'Saved',
          timeout: 200
        })
        this.hide()
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

    updateAndTriggerSave: function (key, value) {
      for (let i = 0; i < this.settings.length; i++) {
        if (this.settings[i].key_id === key) {
          this.settings[i].value = value;
          break
        }
      }
      this.save()
    },
  },
  watch: {
    uuid(value) {
      if (value.length > 0) {
        this.currentUuid = this.uuid;
      }
    }
  }
}
</script>

<style>

span.plugin-changelog * {
  margin-top: 0;
  margin-bottom: 0;
}

span.plugin-description {
  width: 100%;
}

span.plugin-description p {
  margin-bottom: 5px;
}

span.plugin-description h2,
span.plugin-description h3,
span.plugin-description h4,
span.plugin-description h5,
span.plugin-description h6 {
  margin-top: 10px;
  margin-bottom: 0;
}

span.plugin-description ul {
  margin-top: 10px;
  margin-bottom: 10px;
}

span.plugin-description pre {
  border: inset thin;
  padding: 10px;
}

.body--light span.plugin-description pre {
  background: #EEE;
}

.body--dark span.plugin-description pre {
  background: #222;
}

span.plugin-description hr {
  margin-top: 10px;
  margin-bottom: 10px;
}

.checkbox-hint {
  line-height: 1;
  font-size: 12px;
  min-height: 20px;
  color: rgba(0, 0, 0, 0.54);
  padding: 8px 12px 0;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}

.q-list--dark .checkbox-hint {
  color: rgba(255, 255, 255, 0.7);
}

.sub-setting {
  margin-left: 30px;
  padding-top: 8px;
  padding-left: 8px;
  border-left: solid thin var(--q-primary);
}

</style>
