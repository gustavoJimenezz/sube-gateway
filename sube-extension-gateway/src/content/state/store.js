let appAbierta = false;

export function getAppState() {
  return appAbierta;
}

// Save in chrome.storage
// export function setAppState(estado) {
//   appAbierta = estado;
//   chrome.storage.local.set({ appAbierta: estado });
// }

export function loadInitialState() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['appAbierta'], (result) => {
      appAbierta = result.appAbierta || false;
      resolve(appAbierta);
    });
  });
}