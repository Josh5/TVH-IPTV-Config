<template>
  <q-page padding>

    <div class="q-pa-none">

      <q-card flat>
        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="row q-gutter-xs q-mt-xs justify-between">
            <div class="col-auto">
              <q-btn-group>
                <q-btn
                  @click="openEpgSettings(null)"
                  class=""
                  color="primary"
                  icon-right="add"
                  label="Add EPG"/>
              </q-btn-group>
            </div>
          </div>
        </q-card-section>

        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="q-gutter-sm">
            <q-list
              bordered
              separator
              class="rounded-borders">

              <q-item
                v-for="(epg, index) in listOfEpgs"
                v-bind:key="index"
                :class="epg.enabled ? '' : 'bg-grey'">
                <q-item-section avatar>
                  <q-icon name="dvr"/>
                  <!--                  <q-img src="playlist_play"/>-->
                </q-item-section>

                <q-item-section top class="">
                  <q-item-label>{{ epg.name }}</q-item-label>
                  <q-item-label caption lines="3">
                    <span v-html="epg.description"></span>
                  </q-item-label>
                </q-item-section>

                <q-item-section top class="">
                  <q-item-label>{{ epg.url }}</q-item-label>
                </q-item-section>

                <q-separator inset vertical class="q-mx-sm"/>

                <q-item-section center side>
                  <div class="text-grey-8 q-gutter-xs">

                    <q-btn-dropdown
                      flat dense rounded
                      size="12px"
                      no-icon-animation
                      dropdown-icon="more_vert">
                      <q-list>

                        <q-item clickable v-close-popup @click="updateEpg(index)">
                          <q-item-section avatar>
                            <q-icon color="info" name="update"/>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Update</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item clickable v-close-popup @click="openEpgSettings(index)">
                          <q-item-section avatar>
                            <q-icon color="grey-8" name="tune"/>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Configure</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item clickable v-close-popup @click="removeSinglePlugin(plugin.id)">
                          <q-item-section avatar>
                            <q-icon color="negative" name="delete"/>
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
import {defineComponent, ref} from 'vue'
import axios from "axios";
import EpgInfoDialog from "components/EpgInfoDialog.vue";

export default defineComponent({
  name: 'EpgsPage',

  setup() {
    return {}
  },
  data() {
    return {
      listOfEpgs: ref([]),
    }
  },
  methods: {
    fetchSettings: function () {
      // Fetch current settings
      axios({
        method: 'get',
        url: '/tic-api/epgs/get'
      }).then((response) => {
        this.listOfEpgs = response.data.data
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
    openEpgSettings: function (epgId) {
      if (!epgId) {
        epgId = null
      }
      // Display the dialog
      this.$q.dialog({
        component: EpgInfoDialog,
        componentProps: {
          epgId: epgId,
        },
      }).onOk((payload) => {
        this.fetchSettings();
      }).onDismiss(() => {
      })
    },
    updateEpg: function (epgId) {
      // Fetch current settings
      this.$q.loading.show()
      axios({
        method: 'POST',
        url: '/tic-api/epgs/update/' + epgId
      }).then((response) => {
        this.$q.loading.hide()
        this.$q.notify({
          color: 'positive',
          position: 'top',
          icon: 'cloud_done',
          message: 'EPG Updated',
          timeout: 200
        })
      }).catch(() => {
        this.$q.loading.hide()
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: "Failed to update EPG",
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
