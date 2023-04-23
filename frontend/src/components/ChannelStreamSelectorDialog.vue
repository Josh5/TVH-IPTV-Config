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
              <q-table
                flat bordered
                title="Streams"
                :rows="rows"
                :columns="columns"
                :visible-columns="visibleColumns"
                :filter="filter"
                virtual-scroll
                v-model:pagination="pagination"
                :rows-per-page-options="[0]"
                :loading="loading"
                :row-key="genRowIndex"
                :selected-rows-label="getSelectedString"
                v-model:selected="selected"
                selection="multiple"

                no-data-label="I didn't find anything for you"
                no-results-label="The filter didn't uncover any results"
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

                <template v-slot:body="props">
                    <q-tr :props="props">
                        <q-td auto-width>
                            <q-checkbox v-model="props.selected" color="primary" />
                        </q-td>
                        <q-td key="name" :props="props">
                            <q-avatar rounded>
                                <img :src="props.row.tvg_logo" style="height:40px; width:auto; max-width:120px;"/>
                            </q-avatar>
                        </q-td>
                        <q-td key="name" :props="props">
                            {{ props.row.name }}
                        </q-td>
                        <q-td key="playlist_name" :props="props">
                            <q-badge color="green">
                                {{ props.row.playlist_name }}
                            </q-badge>
                        </q-td>
                    </q-tr>
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
  {name: 'tvg_logo', required: true, align: 'left', label: 'Logo', field: 'tvg_logo', sortable: false},
  {name: 'name', required: true, align: 'left', label: 'Name', field: 'name', sortable: false},
  {name: 'playlist_name', required: true, align: 'left', label: 'Playlist', field: 'playlist_name', sortable: false},
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
    hideStreams: {
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
          'id': selected['id'],
          'playlist_id': selected['playlist_id'],
          'playlist_name': selected['playlist_name'],
          'channel_id': selected['channel_id'],
          'stream_name': selected['name'],
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
        this.rows = response.data.data.streams
        this.loading = false
      });
    },
    getSelectedString: function () {
      return this.selected.length === 0 ? '' : `${this.selected.length} record${this.selected.length > 1 ? 's' : ''} selected of ${this.rows.length}`
    },
    genRowIndex: function (row) {
      return `${row.playlist_id}-${row.name}`
    }
  },
  data: function () {
    return {
      maximizedToggle: true,
      currentPlugin: ref(null),
      plugins: ref([]),

      columns,
      rows: ref([]),

      visibleColumns: ref(['name', 'playlist_name', 'logo']),
      filter: ref(''),
      selected: ref([]),
      pagination,
      loading: ref(false),

    }
  }
}
</script>
