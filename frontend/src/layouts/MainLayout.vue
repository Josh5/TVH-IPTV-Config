<template>
  <q-layout view="lhh LpR lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          TVH IPTV Config
        </q-toolbar-title>

        <div>Quasar v{{ $q.version }}</div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
    >
      <q-list>
        <q-item-label
          header
        >
          <!--          Essential Links-->
        </q-item-label>

        <EssentialLink
          v-for="link in essentialLinks"
          :key="link.title"
          v-bind="link"
        />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view/>
    </q-page-container>
  </q-layout>
</template>

<script>
import {defineComponent, ref} from 'vue'
import EssentialLink from 'components/EssentialLink.vue'

const linksList = [
  {
    title: 'TVheadend',
    caption: 'Connect to TVheadend',
    icon: 'img:https://avatars.githubusercontent.com/u/1908588?s=280&v=4',
    link: '/tvheadend'
  },
  {
    title: 'Playlists',
    caption: 'Configure Playlist Sources',
    icon: 'playlist_play',
    link: '/playlists'
  },
  {
    title: 'EPGs',
    caption: 'Configure a list of EPG sources',
    icon: 'calendar_month',
    link: '/epgs'
  },
  {
    title: 'Channels',
    caption: 'Configure Channels',
    icon: 'queue_play_next',
    link: '/channels'
  }
]

export default defineComponent({
  name: 'MainLayout',

  components: {
    EssentialLink
  },

  setup() {
    const leftDrawerOpen = ref(false)

    return {
      essentialLinks: linksList,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value
      }
    }
  }
})
</script>
