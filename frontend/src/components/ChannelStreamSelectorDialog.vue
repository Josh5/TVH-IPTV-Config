<template>

  <!-- START DIALOG CONFIG
  Center full-screen pop-up
  Note: Update template q-dialog ref="" value

  All Platforms:
   - Swipe left/right to dismiss
  Desktop:
   - Width 700px
   - Minimise button top-right
  Mobile:
   - Full screen
   - Back button top-left
  -->
  <q-dialog
    ref="channelStreamSelectorDialogRef"
    :maximized="$q.platform.is.mobile"
    transition-show="jump-left"
    transition-hide="jump-right"
    full-height
    @hide="onDialogHide">

    <q-card
      v-touch-swipe.touch.left.right="hide"
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
              Select Stream From Playlist
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
              icon="close_fullscreen"
              v-close-popup>
              <q-tooltip class="bg-white text-primary">Close</q-tooltip>
            </q-btn>
          </div>
        </div>
      </q-card-section>
      <!-- END DIALOG CONFIG -->

      <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">

        <q-card flat>

          <q-card-section class="q-pa-none">

            <!--            <q-list bordered padding>

                          <q-separator spaced inset/>
                          <div
                            v-for="(plugin, index) in plugins"
                            v-bind:key="index">
                            <q-item
                              clickable v-ripple
                              @click="selectPlugin(plugin)">

                              <q-item-section avatar>
                                <q-img :src="plugin.icon"/>
                              </q-item-section>

                              <q-item-section>
                                <q-item-label>{{ plugin.name }}</q-item-label>
                                <q-item-label caption lines="2">{{ plugin.description }}</q-item-label>
                              </q-item-section>

                            </q-item>
                            <q-separator spaced inset/>
                          </div>

                        </q-list>-->

            <div class="q-pa-md">
              <div class="q-mt-md">
                Selected: {{ JSON.stringify(selected) }}
              </div>
              <q-table
                flat bordered
                title="Streams"
                :rows="rows"
                :columns="columns"
                :filter="filter"
                :loading="loading"
                virtual-scroll
                v-model:pagination="pagination"
                :rows-per-page-options="[0]"
                :selected-rows-label="getSelectedString"
                v-model:selected="selected"
                :visible-columns="visibleColumns"
                selection="multiple"
                no-data-label="I didn't find anything for you"
                no-results-label="The filter didn't uncover any results"
                :key="tableKey"
                item-key="index"
              >
                <template v-slot:top-right>
                  <q-input borderless dense debounce="300" v-model="filter" placeholder="Search">
                    <template v-slot:append>
                      <q-icon name="search"/>
                    </template>
                  </q-input>
                </template>

                <template v-slot:no-data="{ icon, message, filter }">
                  <div class="full-width row flex-center text-primary q-gutter-sm">
                    <q-icon size="2em" :name="filter ? 'filter_b_and_w' : icon"/>
                    <span>{{ message }}</span>
                    <q-icon size="2em" :name="filter ? 'filter_b_and_w' : icon"/>
                  </div>
                </template>
              </q-table>

            </div>

          </q-card-section>

        </q-card>

      </q-card-section>

    </q-card>

  </q-dialog>
</template>

<script>

import axios from "axios";
import {ref} from "vue";

const columns = [
  {name: 'stream_name', required: true, align: 'left', label: 'Name', field: 'stream_name', sortable: false},
  {name: 'playlist_id', required: true, align: 'left', label: 'Playlist', field: 'playlist_id', sortable: false},
]
const pagination = ref({
  rowsPerPage: 0
})

export default {
  name: 'ChannelStreamSelectorDialog',
  props: {
    dialogHeader: {
      type: String,
      default: ' --- header --- '
    },
    hidePlugins: {
      type: Array
    }
  },
  emits: [
    // REQUIRED
    'ok', 'hide', 'path'
  ],
  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.channelStreamSelectorDialogRef.show();
      this.fetchStreamsList();
    },

    // following method is REQUIRED
    // (don't change its name --> "hide")
    hide() {
      this.$refs.channelStreamSelectorDialogRef.hide();
    },

    onDialogHide() {
      // required to be emitted
      // when QDialog emits "hide" event
      // TODO: Insert the playlist name in there
      let returnItems = []
      for (const i in this.selected) {
        let selected = this.selected[i]
        returnItems.push({
          'playlist_id': selected['playlist_id'],
          'playlist_name': '',
          'stream_name': selected['stream_name'],
        })
      }
      this.$emit('ok', {selectedStreams: returnItems})
      this.$emit('hide')
    },

    fetchStreamsList: function () {
      // Fetch from server
      this.rows = []
      this.loading = true
      axios({
        method: 'GET',
        url: '/tic-api/playlists/streams',
      }).then((response) => {
        this.rows = []
        this.rows = Object.entries(response.data.data)
          .flatMap(([playlist_id, names]) =>
            names.map(stream_name => ({stream_name, playlist_id}))
          );
        this.loading = false
      }).catch(() => {
        this.loading = false
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to fetch the master playlist streams list',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
      });
    },
    getSelectedString: function () {
      return this.selected.length === 0 ? '' : `${this.selected.length} record${this.selected.length > 1 ? 's' : ''} selected of ${this.rows.length}`
    }

  },
  computed: {
    tableKey() {
      return index => index; // use the list index as the key
    }
  },
  data: function () {
    return {
      maximizedToggle: true,
      currentPlugin: ref(null),
      plugins: ref([]),

      loading: ref(false),
      filter: ref(''),
      selected: ref([]),
      columns,
      rows: [],
      visibleColumns: ref(['name', 'playlist']),
      pagination,
    }
  }
}
</script>
