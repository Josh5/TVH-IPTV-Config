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
    ref="channelInfoDialogRef"
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
                  v-if="number === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="number"
                  readonly
                  label="Channel Number (edit from channel list)"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="name === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="name"
                  label="Channel Name"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="logoUrl === null"
                  type="QInput"/>
                <q-input
                  v-else
                  v-model="logoUrl"
                  type="textarea"
                  label="Logo URL"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="tags === null"
                  type="QInput"/>
                <q-select
                  v-else
                  use-input
                  use-chips
                  multiple
                  hide-dropdown-icon
                  input-debounce="0"
                  new-value-mode="add-unique"
                  v-model="tags"
                  label="Categories"
                  @keyup.tab="addTag"
                />
              </div>

              <!--START EPG CONFIG-->
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="epgSource === null"
                  type="QInput"/>
                <q-select
                  v-else
                  v-model="epgSource"
                  :options="epgSourceOptions"
                  emit-value
                  map-options
                  label="EPG Source"
                  @input="updateCurrentEpgChannelOptions"
                />
              </div>
              <div class="q-gutter-sm">
                <q-skeleton
                  v-if="epgChannel === null || epgChannelOptions === null"
                  type="QInput"/>
                <q-select
                  v-else
                  label="EPG Channel"
                  v-model="epgChannel"
                  :options="epgChannelOptions"
                  emit-value
                  map-options
                  use-input
                  input-debounce="0"
                  @filter="filterEpg"
                  behavior="menu"
                  @input="updateCurrentEpgChannelOptions"
                />
              </div>
              <!--END EPG CONFIG-->

              <!--START SOURCES CONFIG-->
              <div class="q-gutter-sm">
                <q-list
                  bordered
                  separator
                  class="rounded-borders q-pl-none"
                  style="">

                  <draggable
                    group="channels"
                    item-key="number"
                    handle=".handle"
                    :component-data="{ tag: 'ul', name: 'flip-list', type: 'transition' }"
                    v-model="listOfChannelSources"
                    v-bind="dragOptions"
                  >
                    <template #item="{ element, index }">
                      <q-item
                        :key="index"
                        class="q-px-none rounded-borders"
                        active-class="library-plugin-flow-item">

                        <!--START DRAGGABLE HANDLE-->
                        <q-item-section avatar class="q-px-sm q-mx-sm handle">
                          <q-avatar rounded>
                            <q-icon name="drag_handle" class="" style="max-width: 30px;">
                              <q-tooltip class="bg-white text-primary">Drag to move and set priority</q-tooltip>
                            </q-icon>
                          </q-avatar>
                        </q-item-section>
                        <!--END DRAGGABLE HANDLE-->

                        <q-separator inset vertical class="gt-xs"/>

                        <!--START CHANNEL NUMBER-->
                        <q-item-section side class="q-px-sm q-mx-sm" style="max-width: 60px;">
                          <q-item-label lines="1" class="text-left">
                            <span class="text-weight-medium">{{ index + 1 }}</span>
                            <q-tooltip
                              anchor="bottom middle" self="center middle"
                              class="bg-white text-primary">Channel Number (Click to edit)
                            </q-tooltip>
                          </q-item-label>
                        </q-item-section>
                        <!--END CHANNEL NUMBER-->

                        <q-separator inset vertical class="gt-xs"/>

                        <!--START NAME / DESCRIPTION-->
                        <q-item-section top class="q-mx-md">
                          <q-item-label lines="1" class="text-left">
                            <span class="text-weight-medium q-ml-sm">{{ element.stream_name }}</span>
                          </q-item-label>
                          <q-item-label caption lines="1" class="text-left q-ml-sm">
                            <!--TODO: Limit length of description-->
                            {{ element.playlist_name }}
                          </q-item-label>
                        </q-item-section>
                        <!--END NAME / DESCRIPTION-->

                        <q-separator inset vertical class="gt-xs"/>

                        <q-item-section side class="q-mr-md">
                          <div class="text-grey-8 q-gutter-xs">
                            <!--                        <q-btn class="gt-xs" size="12px" flat dense round icon="delete"/>-->
                            <q-btn size="12px" flat dense round icon="tune"
                                   @click="openChannelSettings(element.number)">
                              <q-tooltip class="bg-white text-primary">Edit</q-tooltip>
                            </q-btn>
                          </div>
                        </q-item-section>

                      </q-item>
                    </template>
                  </draggable>

                </q-list>

                <q-bar class="bg-transparent q-mb-sm">
                  <q-space/>
                  <q-btn
                    round
                    flat
                    color="primary"
                    icon="add"
                    @click="selectChannelSourceFromList">
                  </q-btn>
                </q-bar>


                <!--                <q-skeleton
                                  v-if="name === null"
                                  type="QInput"/>
                                <q-badge color="secondary" multi-line>
                                  Model: "{{ channelSources }}"
                                </q-badge>-->
                <!--                <q-input
                                  v-else
                                  v-model="name"
                                  label="Sources"
                                />-->
                <!--                <q-select
                                  filled
                                  multiple
                                  use-input
                                  use-chips
                                  stack-label
                                  input-debounce="0"
                                  label="Simple filter"
                                  v-model="channelSources"
                                  :options="channelSourceOptions"
                                  style="width: 250px"
                                >
                                  <template v-slot:no-option>
                                    <q-item>
                                      <q-item-section class="text-grey">
                                        No results
                                      </q-item-section>
                                    </q-item>
                                  </template>
                                </q-select>-->

                <!--                <q-select
                                  filled
                                  use-input
                                  input-debounce="0"
                                  label="Hide selected"
                                  v-model="channelSources"
                                  :options="channelSourceOptions"
                                  @filter="filterChannelSourcesFn"
                                  style="width: 250px"
                                  behavior="menu"
                                  emit-value
                                >
                                  <template v-slot:no-option>
                                    <q-item>
                                      <q-item-section class="text-grey">
                                        No results
                                      </q-item-section>
                                    </q-item>
                                  </template>
                                </q-select>-->

                <!--                <q-select
                                  filled
                                  multiple
                                  use-chips
                                  v-model="channelSources"
                                  :options="channelSourceOptions"
                                  label="Standard"
                                  @filter="filterChannelSourcesFn"
                                >
                                  <template v-slot:no-option>
                                    <q-item>
                                      <q-item-section class="text-grey">
                                        No results
                                      </q-item-section>
                                    </q-item>
                                  </template>
                                </q-select>-->
              </div>
              <!--END SOURCES CONFIG-->

              <div>
                <q-btn label="Save" type="submit" color="primary"/>
                <q-btn
                  @click="deleteChannel()"
                  class="q-ml-md"
                  color="red"
                  label="Delete"/>
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
import draggable from "vuedraggable";
import ChannelStreamSelectorDialog from "components/ChannelStreamSelectorDialog.vue";

export default {
  name: 'ChannelInfoDialog',
  components: {draggable},
  props: {
    channelId: {
      type: String
    },
    newChannelNumber: {
      type: Number
    },
  },
  emits: [
    // REQUIRED
    'ok', 'hide', 'path'
  ],
  data() {
    return {
      canSave: ref(false),
      enabled: ref(null),
      number: ref(null),
      name: ref(null),
      logoUrl: ref(null),
      tags: ref(null),
      newTag: ref(''),
      epgSourceOptions: ref(null),
      epgSource: ref(null),
      epgChannelAllOptions: ref(null),
      epgChannelDefaultOptions: ref(null),
      epgChannelOptions: ref(null),
      epgChannel: ref(null),

      listOfChannelSources: ref(null),

      channelSourceOptions: ref(null),
      channelSourceOptionsFiltered: ref(null),
      channelSources: ref(null),
    }
  },
  methods: {
    // following method is REQUIRED
    // (don't change its name --> "show")
    show() {
      this.$refs.channelInfoDialogRef.show();
      this.fetchEpgData();
      if (this.channelId) {
        this.fetchData();
        return
      }
      this.enabled = true
      this.number = (this.newChannelNumber ? this.newChannelNumber : '');
      this.name = ''
      this.logoUrl = ''
      this.tags = []
      this.epgSourceOptions = []
      this.epgSource = ''
      this.epgChannelDefaultOptions = []
      this.epgChannelOptions = []
      this.epgChannel = ''

      this.listOfChannelSources = []

      this.channelSourceOptions = []
      this.channelSourceOptionsFiltered = []
      this.channelSources = []
    },

    // following method is REQUIRED
    // (don't change its name --> "hide")
    hide() {
      this.$refs.channelInfoDialogRef.hide();
    },

    onDialogHide() {
      // required to be emitted
      // when QDialog emits "hide" event
      this.$emit('ok', {})
      this.$emit('hide')
    },

    fetchData: function () {
      // Fetch from server
      axios({
        method: 'GET',
        url: '/tic-api/channels/settings/' + this.channelId,
      }).then((response) => {
        this.enabled = response.data.data.enabled
        this.number = response.data.data.number
        this.name = response.data.data.name
        this.logoUrl = response.data.data.logo_url
        this.tags = response.data.data.tags
        // Fetch data for EPG
        this.epgSource = response.data.data.guide.epg_id
        this.epgChannel = response.data.data.guide.channel_id
        // Fetch list of channel sources and pipe to a list ordered by the 'priority'
        this.listOfChannelSources = Object.keys(response.data.data.sources)
          .map((key) => ({id: key, ...response.data.data.sources[key]}))
          .sort((a, b) => a.priority - b.priority);

        // Enable saving the form
        this.canSave = true;
      });
    },
    fetchEpgData: function () {
      // Fetch from server
      axios({
        method: 'GET',
        url: '/tic-api/epgs/get'
      }).then((response) => {
        this.epgSourceOptions = []
        for (let epg in response.data.data) {
          this.epgSourceOptions.push(
            {
              label: response.data.data[epg].name,
              value: epg,
            }
          );
        }
      });
      axios({
        method: 'GET',
        url: '/tic-api/epgs/channels'
      }).then((response) => {
        this.epgChannelAllOptions = {}
        for (let epg_id in response.data.data) {
          let epg_channels = response.data.data[epg_id]
          this.epgChannelAllOptions[epg_id] = []
          for (let i = 0; i < epg_channels.length; i++) {
            let channel_info = epg_channels[i];
            this.epgChannelAllOptions[epg_id].push(
              {
                label: channel_info.display_name,
                value: channel_info.channel_id,
              }
            );
          }
        }
        this.updateCurrentEpgChannelOptions()
      });
    },
    updateCurrentEpgChannelOptions: function () {
      this.epgChannelDefaultOptions = this.epgChannelAllOptions[this.epgSource]
      this.epgChannelOptions = this.epgChannelAllOptions[this.epgSource]
    },
    save: function () {
      let channelId = this.channelId
      if (!channelId) {
        channelId = (Math.random() + 1).toString(36).substring(5);
      }
      // Re-create sources object in the order of priority
      let sources = {}
      for (let i = 0; i < this.listOfChannelSources.length; i++) {
        let source = this.listOfChannelSources[i]
        if (!source.hasOwnProperty("id")) {
          source['id'] = (Math.random() + 1).toString(36).substring(5);
        }
        sources[source['id']] = {
          'priority': (i + 1),
          'playlist_id': source['playlist_id'],
          'stream_name': source['stream_name'],
        }
      }
      let data = {
        channels: {
          [channelId]: {
            enabled: this.enabled,
            name: this.name,
            logo_url: this.logoUrl,
            tags: this.tags,
            guide: {
              epg_id: this.epgSource,
              channel_id: this.epgChannel,
            },
            sources: sources,
          }
        }
      }
      if (this.newChannelNumber) {
        data.channels[channelId].number = this.newChannelNumber
      }
      axios({
        method: 'POST',
        url: `/tic-api/channels/settings/${channelId}/save`,
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
    deleteChannel: function () {
      let channelId = this.channelId
      if (!channelId) {
        console.warn(`No channel ID provided - '${channelId}'`)
        return
      }
      axios({
        method: 'DELETE',
        url: `/tic-api/channels/settings/${channelId}/delete`,
      }).then((response) => {
        // Save success, show feedback
        this.$q.notify({
          color: 'positive',
          position: 'top',
          icon: 'cloud_done',
          message: 'Channel successfully deleted',
          timeout: 200
        })
        this.hide()
      }).catch(() => {
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: 'Failed to delete channel',
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
      });
    },

    selectChannelSourceFromList: function () {
      this.$q.dialog({
        component: ChannelStreamSelectorDialog,
        componentProps: {
          hidePlugins: [],
        },
      }).onOk((payload) => {
        if (typeof payload.selectedStreams !== 'undefined' && payload.selectedStreams !== null) {
          // Add selected stream to list
          let enabledStreams = structuredClone(this.listOfChannelSources)
          for (const i in payload.selectedStreams) {
            enabledStreams.push(payload.selectedStreams[i]);
          }
          this.listOfChannelSources = enabledStreams;
          // Save the current settings
          //this.save()
        }
      }).onDismiss(() => {
      })
    },
    addTag: function () {
      if (this.newTag) {
        this.tags[this.tags.length] = this.newTag;
        this.newTag = null;
      }
    },
    filterEpg(val, update) {
      if (val === '') {
        update(() => {
          this.epgChannelOptions = this.epgChannelDefaultOptions
        })
        return
      }

      update(() => {
        const needle = val.toLowerCase()
        this.epgChannelOptions = this.epgChannelDefaultOptions.filter(v => v.label.toLowerCase().indexOf(needle) > -1)
      })
    }
  },
  computed: {
    dragOptions() {
      return {
        animation: 100,
        group: "pluginFlow",
        disabled: false,
        ghostClass: "ghost",
        direction: "vertical",
        delay: 200,
        delayOnTouchOnly: true,
      };
    }
  },
  watch: {
    epgSource(value) {
      if (value.length > 0 && this.epgChannelAllOptions) {
        this.updateCurrentEpgChannelOptions()
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
