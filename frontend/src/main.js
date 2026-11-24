import { createApp, Fragment, h } from 'vue'
import './style.css'
import App from './App.vue'
import Sprachwahl from './components/Sprachwahl.vue'
import { spracheLaden, uebersetzen } from './i18n/index.js'

spracheLaden()
const anwendung = createApp({
  render: () => h(Fragment, null, [h(App), h(Sprachwahl)]),
})
anwendung.config.globalProperties.$t = uebersetzen
anwendung.mount('#app')
