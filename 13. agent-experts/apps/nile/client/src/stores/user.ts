// User store
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Session } from '../types';
import api from '../services/api';

const STORAGE_KEY = 'nile_session';

export const useUserStore = defineStore('user', () => {
  const session = ref<Session | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const user = computed(() => session.value?.user ?? null);
  const isLoggedIn = computed(() => !!session.value);
  const userId = computed(() => session.value?.user.id ?? null);

  function setSession(next: Session | null) {
    session.value = next;
    api.setToken(next?.token ?? null);
    if (next) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  async function login(name: string) {
    loading.value = true;
    error.value = null;
    try {
      const next = await api.login(name);
      setSession(next);
      return next.user;
    } catch (e: any) {
      error.value = e.message || 'Login failed';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    if (session.value) {
      api.logout(session.value.token).catch(() => {});
    }
    setSession(null);
  }

  // Drop the session locally without calling the server (its token is already invalid)
  function expireSession() {
    setSession(null);
  }

  function restoreSession() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as Session;
      if (parsed?.token && parsed.user) {
        setSession(parsed);
      } else {
        setSession(null);
      }
    } catch {
      setSession(null);
    }
  }

  return {
    session,
    user,
    loading,
    error,
    isLoggedIn,
    userId,
    login,
    logout,
    expireSession,
    restoreSession
  };
});
