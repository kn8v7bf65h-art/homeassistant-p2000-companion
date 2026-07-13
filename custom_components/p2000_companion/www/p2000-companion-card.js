const CARD_VERSION = "1.3.0";

const SERVICE_META = {
  ambulance: { label: "Ambulance", icon: "mdi:ambulance", className: "ambulance" },
  fire: { label: "Brandweer", icon: "mdi:fire-truck", className: "fire" },
  police: { label: "Politie", icon: "mdi:police-badge", className: "police" },
  mmt: { label: "MMT / Lifeliner", icon: "mdi:helicopter", className: "mmt" },
  lifeboat: { label: "KNRM", icon: "mdi:lifebuoy", className: "lifeboat" },
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));

const formatDate = (value) => {
  if (!value) return "Onbekend tijdstip";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat("nl-NL", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(parsed);
};

const commonStyles = `
  :host { display: block; }
  ha-card { position: relative; overflow: hidden; }
  ha-icon { vertical-align: middle; }
  .missing { padding: 20px; color: var(--secondary-text-color); }
  .service-ambulance { --service-color: #1672d4; }
  .service-fire { --service-color: #d83a2e; }
  .service-police { --service-color: #d5a900; }
  .service-mmt { --service-color: #1b9b59; }
  .service-lifeboat { --service-color: #e47c18; }
  .service-unknown { --service-color: var(--primary-color); }
`;

class P2000CompanionCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config?.entity) throw new Error("Kies een P2000 Companion-entiteit");
    this.config = {
      title: "P2000 Companion",
      compact: false,
      show_link: true,
      show_raw: false,
      show_statistics: true,
      ...config,
    };
    this.render();
  }

  set hass(hass) { this._hass = hass; this.render(); }
  getCardSize() { return this.config?.compact ? 2 : 4; }

  static getStubConfig(hass) {
    const entity = Object.keys(hass?.states || {}).find((id) =>
      id.startsWith("sensor.") && hass.states[id].attributes?.monitor_event
    );
    return { entity: entity || "sensor.p2000_last_filtered_alert", title: "P2000 Companion" };
  }

  static async getConfigElement() {
    return document.createElement("p2000-companion-card-editor");
  }

  render() {
    if (!this.config || !this._hass) return;
    const stateObj = this._hass.states[this.config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<style>${commonStyles}</style><ha-card><div class="missing">Entiteit ${escapeHtml(this.config.entity)} niet gevonden.</div></ha-card>`;
      return;
    }

    const a = stateObj.attributes || {};
    const service = SERVICE_META[a.service] || { label: a.service || "P2000", icon: "mdi:alarm-light", className: "unknown" };
    const hasAlert = Boolean(a.summary || a.message);
    const priority = a.priority || "—";
    const raw = this.config.show_raw && a.raw_text
      ? `<details><summary>Ruwe melding</summary><div class="raw">${escapeHtml(a.raw_text)}</div></details>` : "";
    const link = this.config.show_link && a.link
      ? `<a class="action" href="${escapeHtml(a.link)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon>Open melding</a>` : "";
    const stats = this.config.show_statistics && !this.config.compact ? `
      <div class="stats">
        <div><span>Feeditems</span><strong>${escapeHtml(a.alerts_in_feed ?? "—")}</strong></div>
        <div><span>Nieuw</span><strong>${escapeHtml(a.new_alerts_last_update ?? "—")}</strong></div>
        <div><span>Gefilterd</span><strong>${escapeHtml(a.filtered_alerts_last_update ?? "—")}</strong></div>
      </div>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${commonStyles}
        .accent { position:absolute; inset:0 auto 0 0; width:6px; background:var(--service-color); }
        .content { padding:18px 18px 18px 24px; }
        .topline,.identity,.meta,.stats { display:flex; align-items:center; }
        .topline { justify-content:space-between; gap:12px; }
        .identity { gap:12px; min-width:0; }
        .identity ha-icon { --mdc-icon-size:32px; color:var(--service-color); }
        .title { font-size:1.1rem; font-weight:600; }
        .monitor { color:var(--secondary-text-color); font-size:.86rem; margin-top:2px; }
        .priority { background:var(--service-color); color:#fff; padding:5px 10px; border-radius:999px; font-weight:700; }
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
        .raw { margin-top:8px; padding:10px; border-radius:8px; background:var(--secondary-background-color); font-family:monospace; font-size:.82rem; overflow-wrap:anywhere; }
        .empty { display:flex; align-items:center; gap:8px; margin-top:14px; color:var(--secondary-text-color); }
        .compact .content { padding-top:14px; padding-bottom:14px; }
        .compact .summary { font-size:1rem; }
        .compact .service { margin-top:12px; }
        @media (max-width:480px) { .stats { flex-wrap:wrap; } .meta { gap:10px; } }
      </style>
      <ha-card class="${this.config.compact ? "compact" : ""}">
        <div class="accent service-${escapeHtml(service.className)}"></div>
        <div class="content service-${escapeHtml(service.className)}">
          <div class="topline">
            <div class="identity">
              <ha-icon icon="${escapeHtml(service.icon)}"></ha-icon>
              <div><div class="title">${escapeHtml(this.config.title)}</div><div class="monitor">${escapeHtml(a.monitor_name || "P2000-monitor")}</div></div>
            </div>
            <div class="priority">${escapeHtml(priority)}</div>
          </div>
          ${hasAlert ? `
            <div class="service">${escapeHtml(service.label)}</div>
            <div class="summary">${escapeHtml(a.summary || stateObj.state || "Geen melding")}</div>
            <div class="meta">
              <span><ha-icon icon="mdi:map-marker"></ha-icon>${escapeHtml(a.city || "Onbekende plaats")}</span>
              <span><ha-icon icon="mdi:clock-outline"></ha-icon>${escapeHtml(formatDate(a.published))}</span>
            </div>
            ${stats}${raw}${link}
          ` : `<div class="empty"><ha-icon icon="mdi:information-outline"></ha-icon>Nog geen passende melding ontvangen.</div>`}
        </div>
      </ha-card>`;
  }
}

class P2000CompanionCardEditor extends HTMLElement {
  setConfig(config) { this._config = { title:"P2000 Companion", compact:false, show_link:true, show_raw:false, show_statistics:true, ...config }; this.render(); }
  set hass(hass) { this._hass = hass; this.render(); }

  render() {
    if (!this._config || !this._hass) return;
    const entities = Object.keys(this._hass.states).filter((id) => id.startsWith("sensor.") && this._hass.states[id].attributes?.monitor_event).sort();
    this.innerHTML = `
      <div class="editor">
        <label>Entiteit<select id="entity">${entities.map((id) => `<option value="${escapeHtml(id)}" ${id === this._config.entity ? "selected" : ""}>${escapeHtml(id)}</option>`).join("")}</select></label>
        <label>Titel<input id="title" type="text" value="${escapeHtml(this._config.title || "")}"></label>
        ${["compact","show_link","show_raw","show_statistics"].map((id) => `<label class="check"><input id="${id}" type="checkbox" ${this._config[id] ? "checked" : ""}>${({compact:"Compacte weergave",show_link:"Link naar melding tonen",show_raw:"Ruwe melding tonen",show_statistics:"Statistieken tonen"})[id]}</label>`).join("")}
      </div>
      <style>.editor{display:grid;gap:14px;padding:8px 0}label{display:grid;gap:6px}input[type=text],select{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}.check{display:flex;align-items:center;gap:8px}</style>`;
    ["entity","title","compact","show_link","show_raw","show_statistics"].forEach((id) => {
      const element = this.querySelector(`#${id}`);
      element?.addEventListener(id === "title" ? "input" : "change", () => this.changed());
    });
  }

  changed() {
    const config = { ...this._config };
    ["entity","title"].forEach((id) => { config[id] = this.querySelector(`#${id}`)?.value; });
    ["compact","show_link","show_raw","show_statistics"].forEach((id) => { config[id] = this.querySelector(`#${id}`)?.checked; });
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail:{ config }, bubbles:true, composed:true }));
  }
}

class P2000CompanionMonitorsCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode:"open" }); }
  setConfig(config) { this.config = { title:"P2000-monitoren", entities:[], show_empty:true, ...config }; this.render(); }
  set hass(hass) { this._hass = hass; this.render(); }
  getCardSize() { return Math.max(2, (this.config?.entities?.length || 2) + 1); }
  static getStubConfig(hass) {
    const entities = Object.keys(hass?.states || {}).filter((id) => id.startsWith("sensor.") && hass.states[id].attributes?.monitor_event && id.includes("filtered")).slice(0,6);
    return { title:"P2000-monitoren", entities };
  }
  static async getConfigElement() { return document.createElement("p2000-companion-monitors-card-editor"); }

  render() {
    if (!this.config || !this._hass) return;
    let entityIds = Array.isArray(this.config.entities) ? this.config.entities : [];
    if (!entityIds.length) entityIds = Object.keys(this._hass.states).filter((id) => id.startsWith("sensor.") && this._hass.states[id].attributes?.monitor_event && id.includes("filtered")).sort();
    const rows = entityIds.map((id) => ({ id, state: this._hass.states[id] })).filter(({state}) => state).filter(({state}) => this.config.show_empty || state.attributes?.summary);
    this.shadowRoot.innerHTML = `
      <style>
        ${commonStyles}
        .wrap{padding:16px}.header{font-size:1.08rem;font-weight:600;margin-bottom:10px}.row{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;padding:12px 0;border-top:1px solid var(--divider-color)}.row:first-of-type{border-top:0}.icon{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:color-mix(in srgb,var(--service-color) 16%,transparent);color:var(--service-color)}.name{font-weight:600}.summary{font-size:.9rem;color:var(--secondary-text-color);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.right{text-align:right}.prio{font-weight:700;color:var(--service-color)}.city{font-size:.8rem;color:var(--secondary-text-color);margin-top:3px}.empty{padding:8px 0;color:var(--secondary-text-color)}
      </style>
      <ha-card><div class="wrap"><div class="header">${escapeHtml(this.config.title)}</div>
        ${rows.length ? rows.map(({id,state}) => { const a=state.attributes||{}; const meta=SERVICE_META[a.service]||{label:a.service||"P2000",icon:"mdi:alarm-light",className:"unknown"}; return `<div class="row service-${escapeHtml(meta.className)}" title="${escapeHtml(id)}"><div class="icon"><ha-icon icon="${escapeHtml(meta.icon)}"></ha-icon></div><div><div class="name">${escapeHtml(a.monitor_name||id)}</div><div class="summary">${escapeHtml(a.summary||state.state||"Geen melding")}</div></div><div class="right"><div class="prio">${escapeHtml(a.priority||"—")}</div><div class="city">${escapeHtml(a.city||"")}</div></div></div>`; }).join("") : `<div class="empty">Geen monitoren of meldingen gevonden.</div>`}
      </div></ha-card>`;
  }
}

class P2000CompanionMonitorsCardEditor extends HTMLElement {
  setConfig(config) { this._config={title:"P2000-monitoren",entities:[],show_empty:true,...config}; this.render(); }
  set hass(hass) { this._hass=hass; this.render(); }
  render() {
    if (!this._config || !this._hass) return;
    const all = Object.keys(this._hass.states).filter((id) => id.startsWith("sensor.") && this._hass.states[id].attributes?.monitor_event && id.includes("filtered")).sort();
    this.innerHTML=`<div class="editor"><label>Titel<input id="title" type="text" value="${escapeHtml(this._config.title||"")}"></label><fieldset><legend>Monitoren</legend>${all.map((id)=>`<label class="check"><input type="checkbox" data-entity="${escapeHtml(id)}" ${(this._config.entities||[]).includes(id)?"checked":""}>${escapeHtml(id)}</label>`).join("")}</fieldset><label class="check"><input id="show_empty" type="checkbox" ${this._config.show_empty!==false?"checked":""}>Monitoren zonder melding tonen</label></div><style>.editor{display:grid;gap:14px;padding:8px 0}label{display:grid;gap:6px}input[type=text]{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}fieldset{border:1px solid var(--divider-color);border-radius:8px;display:grid;gap:8px}.check{display:flex;align-items:center;gap:8px}</style>`;
    this.querySelector("#title")?.addEventListener("input",()=>this.changed());
    this.querySelector("#show_empty")?.addEventListener("change",()=>this.changed());
    this.querySelectorAll("[data-entity]").forEach((el)=>el.addEventListener("change",()=>this.changed()));
  }
  changed(){ const entities=[...this.querySelectorAll("[data-entity]:checked")].map((el)=>el.dataset.entity); const config={...this._config,title:this.querySelector("#title")?.value,show_empty:this.querySelector("#show_empty")?.checked,entities}; this._config=config; this.dispatchEvent(new CustomEvent("config-changed",{detail:{config},bubbles:true,composed:true})); }
}

if (!customElements.get("p2000-companion-card")) customElements.define("p2000-companion-card", P2000CompanionCard);
if (!customElements.get("p2000-companion-card-editor")) customElements.define("p2000-companion-card-editor", P2000CompanionCardEditor);
if (!customElements.get("p2000-companion-monitors-card")) customElements.define("p2000-companion-monitors-card", P2000CompanionMonitorsCard);
if (!customElements.get("p2000-companion-monitors-card-editor")) customElements.define("p2000-companion-monitors-card-editor", P2000CompanionMonitorsCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "p2000-companion-card")) window.customCards.push({ type:"p2000-companion-card", name:"P2000 Incident Card", description:"Toont de laatste melding van één P2000-monitor.", preview:true, documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion" });
if (!window.customCards.some((card) => card.type === "p2000-companion-monitors-card")) window.customCards.push({ type:"p2000-companion-monitors-card", name:"P2000 Monitorenkaart", description:"Compact overzicht van meerdere P2000-monitorprofielen.", preview:true, documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion" });
console.info(`%c P2000 COMPANION CARDS %c v${CARD_VERSION} `,"color:white;background:#17365d;font-weight:bold;","color:#17365d;background:white;");
