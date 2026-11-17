(() => {
  const form = document.getElementById("new-filters");
  const panel = document.getElementById("filter-panel");
  const toggle = document.getElementById("ns-filters-toggle");
  const close = document.getElementById("ns-filters-close");
  const program = document.getElementById("ns-program");
  const section = document.getElementById("ns-section");
  const sort = document.getElementById("ns-sort");
  const order = document.getElementById("ns-order");
  if (!form || !panel || !toggle) return;

  function setOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle.title = open ? "Hide filters" : "Show filters";
    document.body.classList.toggle("ns-filters-open", open);
    if (open) {
      requestAnimationFrame(() => program?.focus());
    }
  }

  toggle.addEventListener("click", () => {
    setOpen(panel.hidden);
  });

  close?.addEventListener("click", () => {
    setOpen(false);
    toggle.focus();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || panel.hidden) return;
    setOpen(false);
    toggle.focus();
  });

  // The programme select determines which subsections the server renders.
  program?.addEventListener("change", () => {
    if (section) section.value = "0";
    if (!panel.hidden) {
      try {
        sessionStorage.setItem("ns-reopen-filters", "1");
      } catch {}
    }
    form.requestSubmit();
  });

  const orderDefaults = {
    title: "asc",
    number: "asc",
    credits: "desc",
    latest: "desc",
    coursereview: "desc",
  };
  sort?.addEventListener("change", () => {
    if (order) order.value = orderDefaults[sort.value] ?? "asc";
    form.requestSubmit();
  });

  document.querySelectorAll("[data-autosubmit]").forEach((select) => {
    if (select === program || select === sort) return;
    select.addEventListener("change", () => {
      form.requestSubmit();
    });
  });

  try {
    if (sessionStorage.getItem("ns-reopen-filters") === "1") {
      sessionStorage.removeItem("ns-reopen-filters");
      setOpen(true);
    }
  } catch {}
})();
