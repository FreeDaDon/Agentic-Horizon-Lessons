/**
 * Interactive File Tree Application Entry Point
 * Initializes the Vue 3 application with Pinia store
 */

import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';

// Import global styles
import './styles/fileTree.css';

// Create the Vue application
const app = createApp(App);

// Initialize Pinia store
const pinia = createPinia();
app.use(pinia);

// Mount the application
app.mount('#app');
