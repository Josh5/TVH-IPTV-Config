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
      style="width:1000px;">

      <q-card-section class="bg-card-head">
        <div class="row items-center no-wrap">
          <div
            v-if="$q.platform.is.mobile"
            class="col">
            <q-btn
              v-if="selected.length > 0"
              color="grey-7"
              dense
              round
              flat
              icon="publish"
              v-close-popup />
            <q-btn
              v-else
              color="grey-7"
              dense
              round
              flat
              icon="arrow_back"
              v-close-popup />
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
              v-if="selected.length > 0"
              color="grey-7"
              dense
              round
              flat
              icon="publish"
              v-close-popup>
              <q-tooltip class="bg-white text-primary">Import Selected Streams As Channels</q-tooltip>
            </q-btn>
            <q-btn
              v-else
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

            <div class="q-pa-none">
              <q-table
                ref="tableRef"
                :style="tableStyle"
                flat bordered
                title="Streams"
                :rows="rows"
                :columns="columns"
                :visible-columns="visibleColumns"
                :filter="filter"
                v-model:pagination="pagination"
                :rows-per-page-options="[0]"
                :loading="loading"
                :row-key="genRowIndex"
                :selected-rows-label="getSelectedString"
                v-model:selected="selected"
                selection="multiple"
                binary-state-sort
                @request="fetchStreamsList"

                no-data-label="I didn't find anything for you"
                no-results-label="The filter didn't uncover any results"
              >
                <template v-slot:top-right>
                  <q-input borderless dense debounce="300" v-model="filter" placeholder="Search">
                    <template v-slot:append>
                      <q-icon name="search" />
                    </template>
                  </q-input>
                </template>

                <template v-slot:no-data="{ icon, message, filter }">
                  <div class="full-width row flex-center text-primary q-gutter-sm">
                    <q-icon size="2em" :name="filter ? 'filter_b_and_w' : icon" />
                    <span>{{ message }}</span>
                    <q-icon size="2em" :name="filter ? 'filter_b_and_w' : icon" />
                  </div>
                </template>

                <template v-slot:body="props">
                  <q-tr :props="props">
                    <q-td auto-width>
                      <q-checkbox v-model="props.selected" color="primary" />
                    </q-td>
                    <q-td key="name" :props="props" style="max-width: 60px;">
                      <q-avatar rounded>
                        <img :src="props.row.tvg_logo" style="height:40px; width:auto; max-width:120px;" />
                      </q-avatar>
                    </q-td>
                    <q-td key="name" :props="props"
                          style="max-width: 200px; white-space: normal; word-wrap: break-word;">
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

import axios from 'axios';
import {ref} from 'vue';

const columns = [
  {name: 'tvg_logo', required: true, align: 'left', label: 'Logo', field: 'tvg_logo', sortable: false},
  {name: 'name', required: true, align: 'left', label: 'Name', field: 'name', sortable: true},
  {name: 'playlist_name', required: true, align: 'left', label: 'Playlist', field: 'playlist_name', sortable: false},
];

export default {
  name: 'ChannelStreamSelectorDialog',
  props: {
    dialogHeader: {
      type: String,
      default: ' --- header --- ',
    },
    hideStreams: {
      type: Array,
    },
  },
  emits: [
    // REQUIRED
    'ok', 'hide', 'path',
  ],
  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.channelStreamSelectorDialogRef.show();
      this.fetchStreamsList({
        pagination: this.pagination,
        filter: this.filter,
      });
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
      let returnItems = [];
      for (const i in this.selected) {
        let selected = this.selected[i];
        returnItems.push({
          'id': selected['id'],
          'playlist_id': selected['playlist_id'],
          'playlist_name': selected['playlist_name'],
          'channel_id': selected['channel_id'],
          'stream_name': selected['name'],
        });
      }
      this.$emit('ok', {selectedStreams: returnItems});
      this.$emit('hide');
    },
    fetchStreamsList: function(props) {
      const {page, rowsPerPage, sortBy, descending} = props.pagination;
      const filter = props.filter;

      // Show loading animation
      this.loading = true;

      // get all rows if "All" (0) is selected
      const fetchCount = rowsPerPage === 0 ? pagination.value.rowsNumber : rowsPerPage;

      // calculate starting row of data
      const startRow = (page - 1) * rowsPerPage;

      // Fetch from server
      let data = {
        start: startRow,
        length: fetchCount,
        search_value: filter,
        order_by: sortBy,
        order_direction: descending ? 'desc' : 'asc',
      };
      // Fetch from server
      this.rows = [];
      axios({
        method: 'POST',
        url: '/tic-api/playlists/streams',
        data: data,
      }).then((response) => {
        // update rowsCount with appropriate value
        this.pagination.rowsNumber = response.data.data.records_filtered;

        // Set returned data from server results
        const returnedData = [];
        for (let i = 0; i < response.data.data.streams.length; i++) {
          let stream = response.data.data.streams[i];
          returnedData[i] = {
            id: stream.id,
            channel_id: stream.channel_id,
            name: stream.name,
            url: stream.url,
            playlist_id: stream.playlist_id,
            playlist_name: stream.playlist_name,
            tvg_logo: stream.tvg_logo,
          };
        }

        // clear out existing data and add new
        this.rows.splice(0, this.rows.length, ...returnedData);

        // update local pagination object
        this.pagination.page = page;
        this.pagination.rowsPerPage = rowsPerPage;
        this.pagination.sortBy = sortBy;
        this.pagination.descending = descending;

        // Hide loading animation
        this.loading = false;
      });
    },
    getSelectedString: function() {
      return this.selected.length === 0 ?
        '' :
        `${this.selected.length} record${this.selected.length > 1 ? 's' : ''} selected of ${this.rows.length}`;
    },
    genRowIndex: function(row) {
      return `${row.playlist_id}-${row.name}`;
    },
  },
  computed: {
    tableStyle() {
      const dialogHeight = this.$refs.channelStreamSelectorDialogRef.$el.offsetHeight;
      const tableHeight = (dialogHeight - 150);
      return `height:${tableHeight}px;`;
    },
  },
  data: function() {
    return {
      maximizedToggle: true,
      currentPlugin: ref(null),
      plugins: ref([]),

      columns,
      rows: ref([]),

      visibleColumns: ref(['name', 'playlist_name', 'logo']),
      filter: ref(''),
      selected: ref([]),
      pagination: ref({
        sortBy: 'name',
        descending: false,
        page: 1,
        rowsPerPage: 15,
        rowsNumber: 10,
      }),
      loading: ref(false),

    };
  },
};
</script>
