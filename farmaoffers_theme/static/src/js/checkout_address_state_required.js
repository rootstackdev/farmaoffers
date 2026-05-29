odoo.define("farmaoffers_theme.checkout_address_state_required", [], function () {
  "use strict";

  const syncStateRequired = () => {
    const select = document.querySelector("select[name='state_id']");
    if (!select) return;

    const wrapper = select.closest("#div_state");
    const hasStateOptions = select.options.length > 1;
    const isVisible = !wrapper || wrapper.offsetParent !== null;
    const shouldRequire = hasStateOptions && isVisible;

    select.required = shouldRequire;

    const label = document.querySelector("label[for='o_state_id'], label[for='state_id']");
    if (label) {
      label.classList.toggle("label-optional", !shouldRequire);
    }
  };

  const scheduleSync = () => window.setTimeout(syncStateRequired, 150);

  const observeStateField = () => {
    const select = document.querySelector("select[name='state_id']");
    if (!select || !window.MutationObserver) return;

    const observer = new MutationObserver(syncStateRequired);
    observer.observe(select, { attributes: true, childList: true });

    const wrapper = select.closest("#div_state");
    if (wrapper) {
      observer.observe(wrapper, { attributes: true, attributeFilter: ["class", "style"] });
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      syncStateRequired();
      observeStateField();
    });
  } else {
    syncStateRequired();
    observeStateField();
  }

  document.addEventListener("change", (event) => {
    if (event.target && event.target.name === "country_id") {
      scheduleSync();
    }
  });
});
