const isSupported =
  typeof navigator !== "undefined" && typeof navigator.vibrate === "function";
window.vibrate = () => {
  if (isSupported) {
    navigator.vibrate(200);
  } else {
    document.getElementById("haptic-label").click();
  }
};
