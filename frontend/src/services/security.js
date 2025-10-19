// Ephemeral passphrase holder for local-only encryption
let passphrase = null;

export const setPassphrase = (p) => {
  passphrase = typeof p === 'string' && p.trim().length ? p.trim() : null;
};

export const getPassphrase = () => passphrase;

export const hasPassphrase = () => !!passphrase && passphrase.length > 0;