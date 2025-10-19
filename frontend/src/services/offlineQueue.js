import CryptoJS from 'crypto-js';
import { hasPassphrase, getPassphrase } from './security';
import * as api from './api';

const HABITS_KEY = 'pendingHabits';
const JOURNALS_KEY = 'pendingJournals';

const encryptList = (list, key) => {
  if (!hasPassphrase()) return null;
  return CryptoJS.AES.encrypt(JSON.stringify(list), getPassphrase()).toString();
};

const decryptList = (cipher) => {
  try {
    const bytes = CryptoJS.AES.decrypt(cipher, getPassphrase() || '');
    const decrypted = bytes.toString(CryptoJS.enc.Utf8);
    return JSON.parse(decrypted);
  } catch {
    return [];
  }
};

export const enqueueHabit = (title, frequency, description = null) => {
  if (!hasPassphrase()) return false;
  const cipher = localStorage.getItem(HABITS_KEY);
  const list = cipher ? decryptList(cipher) : [];
  list.push({ title, frequency, description });
  const newCipher = encryptList(list);
  if (newCipher) localStorage.setItem(HABITS_KEY, newCipher);
  return true;
};

export const enqueueJournal = (content, mood) => {
  if (!hasPassphrase()) return false;
  const cipher = localStorage.getItem(JOURNALS_KEY);
  const list = cipher ? decryptList(cipher) : [];
  list.push({ content, mood });
  const newCipher = encryptList(list);
  if (newCipher) localStorage.setItem(JOURNALS_KEY, newCipher);
  return true;
};

export const drainHabitsQueue = async () => {
  if (!navigator.onLine || !hasPassphrase()) return;
  const cipher = localStorage.getItem(HABITS_KEY);
  const list = cipher ? decryptList(cipher) : [];
  if (!list.length) return;
  const remaining = [];
  for (const h of list) {
    try {
      await api.createHabit(h.title, h.frequency, h.description ?? null);
    } catch (e) {
      remaining.push(h);
    }
  }
  const newCipher = remaining.length ? encryptList(remaining) : null;
  if (newCipher) localStorage.setItem(HABITS_KEY, newCipher); else localStorage.removeItem(HABITS_KEY);
};

export const drainJournalsQueue = async () => {
  if (!navigator.onLine || !hasPassphrase()) return;
  const cipher = localStorage.getItem(JOURNALS_KEY);
  const list = cipher ? decryptList(cipher) : [];
  if (!list.length) return;
  const remaining = [];
  for (const j of list) {
    try {
      await api.createJournal(j.content, j.mood);
    } catch (e) {
      remaining.push(j);
    }
  }
  const newCipher = remaining.length ? encryptList(remaining) : null;
  if (newCipher) localStorage.setItem(JOURNALS_KEY, newCipher); else localStorage.removeItem(JOURNALS_KEY);
};

export const drainAll = async () => {
  await drainHabitsQueue();
  await drainJournalsQueue();
};