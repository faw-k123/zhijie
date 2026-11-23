import './assets/main.css'
import './assets/premium.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { loadAllMessages } from './i18n/messages'
import { installDomTranslation } from './i18n/domTranslation'

loadAllMessages()

const app = createApp(App)

app.use(router)

app.mount('#app')
installDomTranslation(router)
