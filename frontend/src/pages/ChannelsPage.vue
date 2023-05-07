<template>
  <q-page padding>

    <div class="q-pa-none">

      <q-card flat>
        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="row q-gutter-xs q-mt-xs justify-between">
            <div class="col-auto">
              <q-btn-group>
                <q-btn
                  @click="openChannelSettings(null)"
                  class=""
                  color="primary"
                  icon-right="add"
                  label="Add Channel"/>
              </q-btn-group>
              <q-btn-group class="q-ml-sm">
                <q-btn
                  @click="openChannelsImport()"
                  class=""
                  color="primary"
                  icon-right="playlist_add_check"
                  label="Import Channels from playlist"/>
              </q-btn-group>
            </div>
          </div>
        </q-card-section>

        <q-card-section :class="$q.platform.is.mobile ? 'q-px-none' : ''">
          <div class="q-gutter-sm">

            <q-dialog v-model="formVisible">
              <q-card>
                <q-card-section>
                  <q-input
                    label="Edit value"
                    v-model="editedValue"
                    ref="input"
                    type="number"
                    @keydown.enter="submitChannelNumberChange"
                  />
                </q-card-section>

                <q-card-actions align="right">
                  <q-btn label="Cancel" @click="formVisible = false"/>
                  <q-btn label="Save" color="primary" @click="submitChannelNumberChange"/>
                </q-card-actions>
              </q-card>
            </q-dialog>

            <q-list
              bordered
              class="rounded-borders q-pl-none"
              style="">

              <draggable
                group="channels"
                item-key="number"
                handle=".handle"
                :component-data="{ tag: 'ul', name: 'flip-list', type: 'transition' }"
                v-model="listOfChannels"
                v-bind="dragOptions"
                @change="setChannelOrder"
              >
                <template #item="{ element, index }">
                  <q-item
                    :key="index"
                    class="q-px-none rounded-borders"
                    :class="element.enabled ? '' : 'bg-grey-3'"
                    clickable>

                    <!--START DRAGGABLE HANDLE-->
                    <q-item-section avatar class="q-px-sm q-mx-sm handle">
                      <q-avatar rounded>
                        <q-icon name="drag_handle" class="" style="max-width: 30px;">
                          <q-tooltip class="bg-white text-primary">Drag to move and re-order</q-tooltip>
                        </q-icon>
                      </q-avatar>
                    </q-item-section>
                    <!--END DRAGGABLE HANDLE-->

                    <q-separator inset vertical class="gt-xs"/>

                    <!--START CHANNEL NUMBER-->
                    <q-item-section class="q-px-sm q-mx-sm" style="max-width:80px;"
                                    @click="showChannelNumberMod(index)">
                      <q-item-label lines="1" class="text-left">
                        <span class="q-ml-sm">Channel</span>
                      </q-item-label>
                      <q-item-label caption lines="1" class="text-left q-ml-sm">
                        {{ element.number }}
                      </q-item-label>
                    </q-item-section>
                    <!--END CHANNEL NUMBER-->

                    <q-separator inset vertical class="gt-xs"/>

                    <!--START NAME / DESCRIPTION-->
                    <q-item-section top class="q-mx-md" @click="openChannelSettings(element.id)">
                      <q-item-label lines="1" class="text-left">
                        <q-avatar rounded size="35px">
                          <q-img :src="element.logo_url" class="" style="max-width: 30px;"/>
                        </q-avatar>

                        <span class="text-weight-medium q-ml-sm">{{ element.name }}</span>
                      </q-item-label>
                      <q-item-label caption lines="1" class="text-left q-ml-sm">
                        Tags: {{ element.tags }}
                        | Sources: {{ Object.keys(element.sources).map(key => element.sources[key].playlist_name) }}
                      </q-item-label>
                      <q-tooltip
                        anchor="center middle"
                        self="center middle"
                        class="bg-white text-primary lt-sm">
                        {{ element.name }}
                      </q-tooltip>
                    </q-item-section>
                    <!--END NAME / DESCRIPTION-->

                    <q-separator inset vertical class="gt-xs"/>

                    <!--START EPG DETAILS-->
                    <q-item-section class="q-px-sm q-mx-sm" @click="openChannelSettings(element.id)">
                      <q-item-label lines="1" class="text-left">
                        <span class="q-ml-sm">Guide</span>
                      </q-item-label>
                      <q-item-label caption lines="1" class="text-left q-ml-sm">
                        {{ element.guide.epg_name }} - {{ element.guide.channel_id }}
                      </q-item-label>
                      <q-tooltip
                        anchor="center middle"
                        self="center middle"
                        class="bg-white text-primary lt-sm">
                        {{ element.name }}
                      </q-tooltip>
                    </q-item-section>
                    <!--END EPG DETAILS-->

                    <q-separator inset vertical class="gt-xs"/>

                    <q-item-section side class="q-mr-md">
                      <div class="text-grey-8 q-gutter-xs">
                        <!--                        <q-btn class="gt-xs" size="12px" flat dense round icon="delete"/>-->
                        <q-btn size="12px" flat dense round icon="tune" @click="openChannelSettings(element.id)">
                          <q-tooltip class="bg-white text-primary">Edit</q-tooltip>
                        </q-btn>
                      </div>
                    </q-item-section>

                  </q-item>
                </template>
              </draggable>

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
import draggable from "vuedraggable";
import ChannelInfoDialog from "components/ChannelInfoDialog.vue";
import ChannelStreamSelectorDialog from "components/ChannelStreamSelectorDialog.vue";

export default defineComponent({
  name: 'ChannelsPage',
  components: {
    draggable
  },

  setup() {
    return {}
  },
  data() {
    return {
      options: {
        dropzoneSelector: ".q-list",
        draggableSelector: ".q-item"
      },
      listOfChannels: ref(null),

      formVisible: false,
      editIndex: '',
      editedValue: '',
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
  methods: {
    generateNewChannel: function (range, usedValues) {
      for (let i = range[0]; i <= range[1]; i++) {
        if (!usedValues.includes(i)) {
          return i;
        }
      }
      return null;
    },
    updateNumbers: function (myList, index) {
      for (let i = index + 1; i < myList.length; i++) {
        myList[i].number += 1;
      }
    },
    insertNumberIncrement: function (list, newItem) {
      let inserted = false;
      let conflict = false;
      let lastNumber = 0;
      let newList = []
      for (let i = 0; i < list.length; i++) {
        const item = list[i];
        if (item.number < newItem.number) {
          newList.push(item)
        } else if (item.number === newItem.number) {
          conflict = true;
          newList.push(newItem)
          inserted = true
          item.number++
          newList.push(item)
        } else if (item.number === lastNumber) {
          item.number++;
          newList.push(item)
        } else if (item.number > newItem.number && !inserted) {
          newList.push(newItem)
          inserted = true
          newList.push(item)
        } else if (item.number > newItem.number) {
          newList.push(item)
        }
        lastNumber = item.number;
      }
      if (!inserted) {
        newList.push(newItem)
      }
      return newList;
    },
    shiftChannelNumber: function (list, movedItemId) {
      let lastNumber = 999;
      for (let i = 0; i < list.length; i++) {
        const item = list[i];
        if (item.id === movedItemId) {
          item.number = parseInt(lastNumber) + 1
        }
        lastNumber = parseInt(item.number)
      }
    },
    fixNumberIncrement: function (list) {
      let sortedList = list.sort((a, b) => a.number - b.number);
      let lastNumber = 999;
      let newList = []
      for (let i = 0; i < sortedList.length; i++) {
        const item = sortedList[i];
        if (isNaN(item.number)) {
          item.number = (lastNumber + 1);
          newList.push(item)
        } else if (parseInt(item.number) === parseInt(lastNumber)) {
          item.number++;
          newList.push(item)
        } else if (parseInt(item.number) > parseInt(lastNumber)) {
          newList.push(item)
        } else if (parseInt(item.number) < parseInt(lastNumber)) {
          item.number = (lastNumber + 1);
          newList.push(item)
        } else {
          console.error("--- Missed item ---")
          console.error(lastNumber)
          console.error(item.number)
          console.error((item.number === lastNumber))
          console.error("-------------------")
        }
        lastNumber = item.number;
      }
      list = newList
      console.debug(list)
    },
    nextAvailableChannelNumber: function (list) {
      let sortedList = list.sort((a, b) => a.number - b.number);
      let lastNumber = 999;
      for (let i = 0; i < sortedList.length; i++) {
        const item = sortedList[i];
        if (parseInt(item.number) > parseInt(lastNumber + 1)) {
          return lastNumber + 1
        }
        lastNumber = parseInt(item.number);
      }
      return lastNumber + 1
    },
    fetchChannels: function () {
      // Fetch current settings
      axios({
        method: 'GET',
        url: '/tic-api/channels/get'
      }).then((response) => {
        this.listOfChannels = response.data.data.sort((a, b) => a.number - b.number);
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
    openChannelSettings: function (channelId) {
      let newChannelNumber = null
      if (!channelId) {
        channelId = null
        newChannelNumber = this.nextAvailableChannelNumber(this.listOfChannels)
      }
      // Display the dialog
      this.$q.dialog({
        component: ChannelInfoDialog,
        componentProps: {
          channelId: channelId,
          newChannelNumber: newChannelNumber,
        },
      }).onOk((payload) => {
        this.fetchChannels();
      }).onDismiss(() => {
      })
    },
    openChannelsImport: function () {
      this.$q.dialog({
        component: ChannelStreamSelectorDialog,
        componentProps: {
          hideStreams: [],
        },
      }).onOk((payload) => {
        if (typeof payload.selectedStreams !== 'undefined' && payload.selectedStreams !== null) {
          // Add selected stream to list
          this.$q.loading.show()
          // Send changes to backend
          let data = {
            channels: []
          }
          console.log(payload.selectedStreams)
          for (const i in payload.selectedStreams) {
            data.channels.push({
              playlist_id: payload.selectedStreams[i].playlist_id,
              playlist_name: payload.selectedStreams[i].playlist_name,
              stream_id: payload.selectedStreams[i].id,
              stream_name: payload.selectedStreams[i].stream_name,
            });
          }
          axios({
            method: 'POST',
            url: '/tic-api/channels/settings/multiple/add',
            data: data
          }).then((response) => {
            // Reload from backend
            this.fetchChannels();
            this.$q.loading.hide()
          }).catch(() => {
            // Notify failure
            this.$q.notify({
              color: 'negative',
              position: 'top',
              message: "An error was encountered while adding new channels.",
              icon: 'report_problem',
              actions: [{icon: 'close', color: 'white'}]
            })
            this.$q.loading.hide()
          });
        }
      }).onDismiss(() => {
      })
    },
    saveChannel: function () {
      // Send changes to backend
      let data = {
        channels: {}
      }
      for (let i = 0; i < this.listOfChannels.length; i++) {
        const item = this.listOfChannels[i];
        data.channels[item.id] = item
      }
      axios({
        method: 'POST',
        url: '/tic-api/channels/settings/multiple/save',
        data: data
      }).then((response) => {
        // Reload from backend
        this.fetchChannels();
      }).catch(() => {
        // Notify failure
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: "An error was encountered while saving the channel order.",
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
      });
    },
    setChannelOrder: function (event) {
      console.log("setChannelOrder")
      const movedItem = event.moved.element;
      // Shift the channel number of item that was moved
      this.shiftChannelNumber(this.listOfChannels, movedItem.id)
      // Fix the channel numbering so there are no duplicates
      this.fixNumberIncrement(this.listOfChannels)
      // Save new channel layout
      this.saveChannel()
    },
    showChannelNumberMod(index) {
      console.log(index)
      this.formVisible = true
      this.editIndex = index
      this.editedValue = this.listOfChannels[index].number
      this.$nextTick(() => {
        this.$refs.input.select()
      })
    },
    submitChannelNumberChange() {
      // Ensure value is a number
      // Ensure value is above 1000 and less than 10000
      if (isNaN(this.editedValue) || this.editedValue < 1000 || this.editedValue > 9999) {
        // Value already exists
        console.error("Value is less than 1000")
        // Notify failure
        this.$q.notify({
          color: 'negative',
          position: 'top',
          message: "You must enter a number between 1000 and 9999.",
          icon: 'report_problem',
          actions: [{icon: 'close', color: 'white'}]
        })
        return
      }

      if (this.editedValue === this.listOfChannels[this.editIndex].number) {
        // Value already exists
        console.warn("Value already exists")
        this.formVisible = false
        return
      }
      this.listOfChannels[this.editIndex].number = this.editedValue
      this.formVisible = false
      // Shift any conflicting numbers
      //this.shiftNumbers(this.listOfChannels, this.listOfChannels[this.editIndex].id)
      // Fix the channel numbering
      this.fixNumberIncrement(this.listOfChannels)
      // Save new channel layout
      this.saveChannel()
    },
  },
  created() {
    this.fetchChannels();
  }
})
</script>
