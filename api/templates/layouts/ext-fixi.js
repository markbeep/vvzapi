document.addEventListener("fx:config", (evt) => {
  evt.detail.cfg.transition = false;
});
document.addEventListener("fx:after", (evt) => {
  // add working history if element contains `ext-fx-push` attr
  if (evt.target.hasAttribute("ext-fx-push")) {
    history.replaceState({ fixi: true, url: location.href }, "", location.href);
    history.pushState(
      { fixi: true, url: evt.detail.cfg.response.url },
      "",
      evt.detail.cfg.response.url,
    );
  }
});
window.addEventListener("popstate", async (evt) => {
  if (evt.state.fixi) {
    let historyResp = await fetch(evt.state.url);
    document.documentElement.innerHTML = await historyResp.text();
    document.dispatchEvent(new CustomEvent("fx:process"));
    initJS();
  }
});
