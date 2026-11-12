import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { useUserStore } from './stores/user';
import api from './services/api';
import './style.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

// Restore user session before mounting
const userStore = useUserStore();
userStore.restoreSession();

api.setUnauthorizedHandler(() => {
  userStore.expireSession();
  router.push('/login');
});

app.use(router);
app.mount('#app');
