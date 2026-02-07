/** preload links on mouse down */
function pre(ev) {
  if (
    ev.target.tagName === "A" &&
    ev.target.href &&
    ev.target.href.startsWith(window.location.origin)
  ) {
    fetch(ev.target.href, { method: "GET", mode: "no-cors" });
  }
}
document.addEventListener("mousedown", pre);
document.addEventListener("touchstart", pre);
