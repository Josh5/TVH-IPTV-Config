const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {path: '', component: () => import('pages/TvheadendPage.vue')}
    ],
  },
  {
    name: 'tvheadend',
    path: '/tvheadend',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {path: '', component: () => import('pages/TvheadendPage.vue')}
    ]
  },
  {
    name: 'playlists',
    path: '/playlists',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {path: '', component: () => import('pages/PlaylistsPage.vue')}
    ]
  },
  {
    name: 'epgs',
    path: '/epgs',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {path: '', component: () => import('pages/EpgsPage.vue')}
    ]
  },
  {
    name: 'channels',
    path: '/channels',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {path: '', component: () => import('pages/ChannelsPage.vue')}
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
