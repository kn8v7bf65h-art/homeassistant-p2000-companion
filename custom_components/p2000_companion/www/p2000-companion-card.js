const CARD_VERSION = "1.2.0";

const SERVICE_META = {
  ambulance: { label: "Ambulance", icon: "mdi:ambulance" },
  fire: { label: "Brandweer", icon: "mdi:fire-truck" },
  police: { label: "Politie", icon: "mdi:police-badge" },
  mmt: { label: "MMT / Lifeliner", icon: "mdi:helicopter" },
  lifeboat: { label: "KNRM", icon: "mdi:lifebuoy" },
};

class P2000CompanionCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Kies een P2000 Companion-entiteit");
    this.config = {
      title: "P2000 Companion",
      compact: false,
      show_link: true,
      show_raw: false,
      ...config,
    };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return this.config?.compact ? 2 : 4;
  }

  static getStubConfig() {
    return { entity: "sensor.p2000_last_filtered_alert", title: "P2000 Companion" };
  }

  static async getConfigElement() {
    return document.createElement("p2000-companion-card-editor");
  }

  formatDate(value) {
    if (!value) return "Onbekend tijdstip";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat("nl-NL", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    }).format(parsed);
  }

  render() {
    if (!this.config || !this._hass) return;
    const stateObj = this._hass.states[this.config.entity];
    if (!stateObj) {
      this.innerHTML = `<ha-card><div class="missing">Entiteit ${this.config.entity} niet gevonden.</div></ha-card>`;
      return;
    }

    const a = stateObj.attributes || {};
    const service = SERVICE_META[a.service] || { label: a.service || "P2000", icon: "mdi:alarm-light" };
    const priority = a.priority || "—";
    const summary = a.summary || stateObj.state || "Geen melding";
    const city = a.city || "Onbekende plaats";
    const monitor = a.monitor_name || "P2000-monitor";
    const published = this.formatDate(a.published);
    const hasAlert = Boolean(a.summary || a.message);
    const compactClass = this.config.compact ? " compact" : "";
    const raw = this.config.show_raw && a.raw_text
      ? `<details><summary>Ruwe melding</summary><div class="raw">${this.escape(a.raw_text)}</div></details>` : "";
    const link = this.config.show_link && a.link
      ? `<a class="action" href="${this.escapeAttr(a.link)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon> Open melding</a>` : "";

    this.innerHTML = `
      <ha-card class="p2000-card${compactClass}">
        <div class="accent service-${this.escapeAttr(a.service || "unknown")}"></div>
        <div class="content">
          <div class="topline">
            <div class="identity">
              <ha-icon icon="${service.icon}"></ha-icon>
              <div>
                <div class="title">${this.escape(this.config.title)}</div>
                <div class="monitor">${this.escape(monitor)}</div>
              </div>
            </div>
            <div class="priority">${this.escape(priority)}</div>
          </div>
          ${hasAlert ? `
            <div class="service">${this.escape(service.label)}</div>
            <div class="summary">${this.escape(summary)}</div>
            <div class="meta">
              <span><ha-icon icon="mdi:map-marker"></ha-icon>${this.escape(city)}</span>
              <span><ha-icon icon="mdi:clock-outline"></ha-icon>${this.escape(published)}</span>
            </div>
            ${this.config.compact ? "" : `
              <div class="stats">
                <div><span>Feeditems</span><strong>${a.alerts_in_feed ?? "—"}</strong></div>
                <div><span>Nieuw</span><strong>${a.new_alerts_last_update ?? "—"}</strong></div>
                <div><span>Gefilterd</span><strong>${a.filtered_alerts_last_update ?? "—"}</strong></div>
              </div>
              ${raw}
              ${link}
            `}
          ` : `<div class="empty"><ha-icon icon="mdi:information-outline"></ha-icon> Nog geen passende melding ontvangen.</div>`}
        </div>
      </ha-card>
      <style>
        .p2000-card { position: relative; overflow: hidden; }
        .accent { position:absolute; inset:0 auto 0 0; width:6px; background:var(--primary-color); }
        .service-ambulance { background:#1667d9; }
        .service-fire { background:#d52b1e; }
        .service-police { background:#e4b500; }
        .service-mmt { background:#18a558; }
        .service-lifeboat { background:#ef7d00; }
        .content { padding:18px 18px 18px 24px; }
        .topline, .identity, .meta, .stats { display:flex; align-items:center; }
        .topline { justify-content:space-between; gap:12px; }
        .identity { gap:12px; min-width:0; }
        .identity ha-icon { --mdc-icon-size:32px; color:var(--primary-color); }
        .title { font-size:1.1rem; font-weight:600; }
        .monitor { color:var(--secondary-text-color); font-size:.86rem; margin-top:2px; }
        .priority { background:var(--primary-color); color:var(--text-primary-color, #fff); padding:5px 10px; border-radius:999px; font-weight:700; }
        .service { margin-top:18px; text-transform:uppercase; letter-spacing:.06em; font-size:.78rem; color:var(--secondary-text-color); font-weight:600; }
        .summary { margin-top:6px; font-size:1.15rem; line-height:1.42; font-weight:500; }
        .meta { margin-top:14px; gap:18px; flex-wrap:wrap; color:var(--secondary-text-color); font-size:.9rem; }
        .meta span { display:flex; align-items:center; gap:5px; }
        .meta ha-icon { --mdc-icon-size:18px; }
        .stats { margin-top:18px; gap:10px; }
        .stats div { flex:1; min-width:70px; border:1px solid var(--divider-color); border-radius:10px; padding:10px; }
        .stats span { display:block; color:var(--secondary-text-color); font-size:.76rem; }
        .stats strong { display:block; margin-top:3px; font-size:1.1rem; }
        .action { margin-top:16px; display:inline-flex; align-items:center; gap:6px; color:var(--primary-color); text-decoration:none; font-weight:500; }
        .action ha-icon { --mdc-icon-size:18px; }
        details { margin-top:14px; color:var(--secondary-text-color); }
        .raw { margin-top:8px; padding:10px; border-radius:8px; background:var(--secondary-background-color); font-family:monospace; font-size:.82rem; }
        .empty, .missing { padding:20px; color:var(--secondary-text-color); }
        .empty { display:flex; align-items:center; gap:8px; margin-top:14px; padding:10px 0 0; }
        .compact .content { padding-top:14px; padding-bottom:14px; }
        .compact .summary { font-size:1rem; }
        .compact .service { margin-top:12px; }
        @media (max-width: 480px) {
          .content { padding-right:14px; }
          .stats { flex-wrap:wrap; }
          .meta { gap:10px; }
        }
      </style>`;
  }

  escape(value) {
    return String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
  }

  escapeAttr(value) { return this.escape(value); }
}

class P2000CompanionCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { title: "P2000 Companion", compact: false, show_link: true, show_raw: false, ...config };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._config || !this._hass) return;
    const entities = Object.keys(this._hass.states)
      .filter(id => id.startsWith("sensor.") && (id.includes("p2000") || this._hass.states[id].attributes?.monitor_event))
      .sort();
    this.innerHTML = `
      <div class="editor">
        <label>Entiteit<select id="entity">${entities.map(id => `<option value="${id}" ${id === this._config.entity ? "selected" : ""}>${id}</option>`).join("")}</select></label>
        <label>Titel<input id="title" type="text" value="${this.escapeAttr(this._config.title || "")}"></label>
        <label class="check"><input id="compact" type="checkbox" ${this._config.compact ? "checked" : ""}> Compacte weergave</label>
        <label class="check"><input id="show_link" type="checkbox" ${this._config.show_link !== false ? "checked" : ""}> Link naar melding tonen</label>
        <label class="check"><input id="show_raw" type="checkbox" ${this._config.show_raw ? "checked" : ""}> Ruwe melding tonen</label>
      </div>
      <style>
        .editor { display:grid; gap:14px; padding:8px 0; }
        label { display:grid; gap:6px; color:var(--primary-text-color); }
        input[type=text], select { width:100%; box-sizing:border-box; padding:10px; border:1px solid var(--divider-color); border-radius:8px; background:var(--card-background-color); color:var(--primary-text-color); }
        .check { display:flex; align-items:center; gap:8px; }
      </style>`;
    ["entity", "title", "compact", "show_link", "show_raw"].forEach(id => {
      this.querySelector(`#${id}`)?.addEventListener("change", () => this.changed());
      if (id === "title") this.querySelector(`#${id}`)?.addEventListener("input", () => this.changed());
    });
  }

  changed() {
    const config = {
      ...this._config,
      entity: this.querySelector("#entity")?.value,
      title: this.querySelector("#title")?.value,
      compact: this.querySelector("#compact")?.checked,
      show_link: this.querySelector("#show_link")?.checked,
      show_raw: this.querySelector("#show_raw")?.checked,
    };
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  escapeAttr(value) {
    return String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
  }
}

customElements.define("p2000-companion-card", P2000CompanionCard);
customElements.define("p2000-companion-card-editor", P2000CompanionCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "p2000-companion-card",
  name: "P2000 Companion Incident Card",
  description: "Toont de laatste P2000-melding van een monitorprofiel.",
  preview: true,
  documentationURL: "https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion",
});
console.info(`%c P2000 COMPANION CARD %c v${CARD_VERSION} `, "color:white;background:#17365d;font-weight:bold;", "color:#17365d;background:white;");
