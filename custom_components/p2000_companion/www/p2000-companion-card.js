const CARD_VERSION = "3.0.0";

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

const parseDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};

const formatDate = (value) => {
  const date = parseDate(value);
  if (!date) return value ? String(value) : "Onbekend tijdstip";
  return new Intl.DateTimeFormat("nl-NL", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(date).replace(",", " •");
};

const formatRelative = (value) => {
  const date = parseDate(value);
  if (!date) return "Onbekend";
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const abs = Math.abs(seconds);
  const formatter = new Intl.RelativeTimeFormat("nl-NL", { numeric: "auto" });
  if (abs < 60) return formatter.format(seconds, "second");
  if (abs < 3600) return formatter.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return formatter.format(Math.round(seconds / 3600), "hour");
  return formatter.format(Math.round(seconds / 86400), "day");
};

const serviceMeta = (service) => SERVICE_META[String(service || "").toLowerCase()] || {
  label: service || "P2000",
  icon: "mdi:alarm-light",
  className: "unknown",
};

const entityCandidates = (hass) => Object.keys(hass?.states || {})
  .filter((id) => id.startsWith("sensor.") && hass.states[id].attributes?.monitor_event)
  .sort();

const commonStyles = `
  :host {
    display: block;
    --p2-radius: 18px;
    --p2-border: color-mix(in srgb, var(--divider-color) 74%, transparent);
    --p2-surface: color-mix(in srgb, var(--card-background-color) 94%, transparent);
    --p2-soft: color-mix(in srgb, var(--secondary-background-color) 72%, transparent);
  }
  * { box-sizing: border-box; }
  ha-card {
    position: relative;
    overflow: hidden;
    border-radius: var(--p2-radius);
    border: 1px solid var(--p2-border);
    background:
      radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--service-color, var(--primary-color)) 10%, transparent), transparent 40%),
      var(--p2-surface);
    box-shadow: 0 10px 28px rgba(0, 0, 0, .10);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }
  ha-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 34px rgba(0, 0, 0, .14);
    border-color: color-mix(in srgb, var(--service-color, var(--primary-color)) 35%, var(--p2-border));
  }
  ha-icon { vertical-align: middle; }
  .missing, .empty-state { padding: 22px; color: var(--secondary-text-color); }
  .service-ambulance { --service-color: #2583e8; --service-rgb: 37, 131, 232; }
  .service-fire { --service-color: #ef4b42; --service-rgb: 239, 75, 66; }
  .service-police { --service-color: #e4b400; --service-rgb: 228, 180, 0; }
  .service-mmt { --service-color: #9b65df; --service-rgb: 155, 101, 223; }
  .service-lifeboat { --service-color: #f28a2e; --service-rgb: 242, 138, 46; }
  .service-unknown { --service-color: var(--primary-color); --service-rgb: 3, 169, 244; }
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
      show_relative_time: true,
      ...config,
    };
    this.render();
  }

  set hass(hass) { this._hass = hass; this.render(); }
  getCardSize() { return this.config?.compact ? 3 : 5; }

  static getStubConfig(hass) {
    const entity = entityCandidates(hass)[0];
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
    const service = serviceMeta(a.service);
    const hasAlert = Boolean(a.summary || a.message || (stateObj.state && stateObj.state !== "unknown"));
    const priority = a.priority || "—";
    const summary = a.summary || a.message || stateObj.state || "Geen melding";
    const published = a.published || a.timestamp || a.last_updated || stateObj.last_updated;
    const city = a.city || a.place || a.location || "Onbekende plaats";
    const raw = this.config.show_raw && a.raw_text
      ? `<details><summary><ha-icon icon="mdi:code-tags"></ha-icon> Ruwe melding</summary><div class="raw">${escapeHtml(a.raw_text)}</div></details>` : "";
    const link = this.config.show_link && a.link
      ? `<a class="action primary" href="${escapeHtml(a.link)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon><span>Open volledige melding</span></a>` : "";
    const stats = this.config.show_statistics && !this.config.compact ? `
      <div class="stats">
        <div class="stat"><span class="stat-icon"><ha-icon icon="mdi:rss"></ha-icon></span><strong>${escapeHtml(a.alerts_in_feed ?? "—")}</strong><small>Feeditems</small></div>
        <div class="stat"><span class="stat-icon"><ha-icon icon="mdi:bell-plus-outline"></ha-icon></span><strong>${escapeHtml(a.new_alerts_last_update ?? "—")}</strong><small>Nieuw</small></div>
        <div class="stat"><span class="stat-icon"><ha-icon icon="mdi:filter-check-outline"></ha-icon></span><strong>${escapeHtml(a.filtered_alerts_last_update ?? "—")}</strong><small>Gefilterd</small></div>
      </div>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${commonStyles}
        .accent { position:absolute; inset:0 auto 0 0; width:5px; background:linear-gradient(180deg,var(--service-color),color-mix(in srgb,var(--service-color) 55%,transparent)); }
        .content { padding:20px 20px 20px 25px; }
        .topline { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; }
        .identity { display:flex; align-items:center; gap:13px; min-width:0; }
        .icon-shell { flex:0 0 50px; width:50px; height:50px; display:grid; place-items:center; border-radius:50%; color:var(--service-color); background:rgba(var(--service-rgb),.14); border:1px solid rgba(var(--service-rgb),.32); box-shadow:inset 0 0 18px rgba(var(--service-rgb),.10); }
        .icon-shell ha-icon { --mdc-icon-size:28px; }
        .title { font-size:1.12rem; font-weight:700; line-height:1.25; overflow-wrap:anywhere; }
        .monitor { color:var(--secondary-text-color); font-size:.85rem; margin-top:3px; overflow-wrap:anywhere; }
        .priority { flex:0 0 auto; min-width:42px; text-align:center; color:#fff; background:linear-gradient(180deg,color-mix(in srgb,var(--service-color) 88%,white),var(--service-color)); padding:7px 11px; border-radius:11px; font-weight:800; box-shadow:0 5px 14px rgba(var(--service-rgb),.25); }
        .service-chip { display:inline-flex; align-items:center; margin-top:19px; padding:5px 9px; border-radius:8px; background:rgba(var(--service-rgb),.13); color:var(--service-color); text-transform:uppercase; letter-spacing:.07em; font-size:.72rem; font-weight:800; }
        .summary { margin-top:10px; font-size:1.25rem; line-height:1.42; font-weight:700; white-space:normal; overflow-wrap:anywhere; word-break:normal; }
        .meta { display:flex; align-items:center; flex-wrap:wrap; gap:10px 18px; margin-top:16px; color:var(--secondary-text-color); font-size:.88rem; }
        .meta span { display:inline-flex; align-items:center; gap:6px; min-width:0; }
        .meta ha-icon { --mdc-icon-size:18px; color:var(--service-color); }
        .relative { margin-left:auto; color:var(--primary-text-color); font-weight:600; }
        .relative-dot { width:9px; height:9px; border-radius:50%; background:#45bd62; box-shadow:0 0 0 4px rgba(69,189,98,.12); }
        .stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:20px; }
        .stat { min-width:0; border:1px solid var(--p2-border); border-radius:13px; padding:12px; background:var(--p2-soft); }
        .stat-icon { display:grid; place-items:center; width:29px; height:29px; border-radius:8px; color:var(--service-color); background:rgba(var(--service-rgb),.10); }
        .stat-icon ha-icon { --mdc-icon-size:18px; }
        .stat strong { display:block; margin-top:10px; font-size:1.25rem; }
        .stat small { display:block; margin-top:2px; color:var(--secondary-text-color); font-size:.73rem; }
        .actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; padding-top:16px; border-top:1px solid var(--p2-border); }
        .action { display:inline-flex; align-items:center; gap:7px; min-height:36px; padding:8px 11px; border-radius:10px; text-decoration:none; font-weight:650; }
        .action.primary { color:var(--service-color); background:rgba(var(--service-rgb),.10); }
        .action ha-icon { --mdc-icon-size:18px; }
        details { margin-top:16px; color:var(--secondary-text-color); }
        details summary { display:flex; align-items:center; gap:7px; cursor:pointer; font-weight:550; }
        details summary ha-icon { --mdc-icon-size:18px; }
        .raw { margin-top:10px; padding:12px; border-radius:11px; background:var(--p2-soft); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.8rem; line-height:1.45; white-space:pre-wrap; overflow-wrap:anywhere; }
        .empty-state { display:flex; align-items:center; gap:10px; margin-top:15px; padding:15px; border-radius:12px; background:var(--p2-soft); }
        .compact .content { padding-top:16px; padding-bottom:16px; }
        .compact .icon-shell { width:42px; height:42px; flex-basis:42px; }
        .compact .summary { font-size:1.05rem; }
        .compact .service-chip { margin-top:14px; }
        @media (max-width:520px) {
          .content { padding:17px 16px 17px 21px; }
          .stats { grid-template-columns:repeat(3,minmax(82px,1fr)); overflow-x:auto; padding-bottom:3px; }
          .relative { margin-left:0; width:100%; }
          .summary { font-size:1.12rem; }
          .icon-shell { width:44px; height:44px; flex-basis:44px; }
        }
      </style>
      <ha-card class="service-${escapeHtml(service.className)} ${this.config.compact ? "compact" : ""}">
        <div class="accent"></div>
        <div class="content">
          <div class="topline">
            <div class="identity">
              <div class="icon-shell"><ha-icon icon="${escapeHtml(service.icon)}"></ha-icon></div>
              <div><div class="title">${escapeHtml(this.config.title)}</div><div class="monitor">${escapeHtml(a.monitor_name || "P2000-monitor")}</div></div>
            </div>
            <div class="priority">${escapeHtml(priority)}</div>
          </div>
          ${hasAlert ? `
            <div class="service-chip">${escapeHtml(service.label)}</div>
            <div class="summary">${escapeHtml(summary)}</div>
            <div class="meta">
              <span><ha-icon icon="mdi:map-marker"></ha-icon>${escapeHtml(city)}</span>
              <span><ha-icon icon="mdi:clock-outline"></ha-icon>${escapeHtml(formatDate(published))}</span>
              ${this.config.show_relative_time ? `<span class="relative"><i class="relative-dot"></i>${escapeHtml(formatRelative(published))}</span>` : ""}
            </div>
            ${stats}${raw}<div class="actions">${link}</div>
          ` : `<div class="empty-state"><ha-icon icon="mdi:information-outline"></ha-icon><span>Nog geen passende melding ontvangen.</span></div>`}
        </div>
      </ha-card>`;
  }
}

class P2000CompanionCardEditor extends HTMLElement {
  setConfig(config) { this._config = { title:"P2000 Companion", compact:false, show_link:true, show_raw:false, show_statistics:true, show_relative_time:true, ...config }; this.render(); }
  set hass(hass) { this._hass = hass; this.render(); }

  render() {
    if (!this._config || !this._hass) return;
    const entities = entityCandidates(this._hass);
    const toggles = {
      compact: "Compacte weergave",
      show_link: "Link naar melding tonen",
      show_raw: "Ruwe melding tonen",
      show_statistics: "Statistieken tonen",
      show_relative_time: "Relatieve tijd tonen",
    };
    this.innerHTML = `
      <div class="editor">
        <label>Entiteit<select id="entity">${entities.map((id) => `<option value="${escapeHtml(id)}" ${id === this._config.entity ? "selected" : ""}>${escapeHtml(id)}</option>`).join("")}</select></label>
        <label>Titel<input id="title" type="text" value="${escapeHtml(this._config.title || "")}"></label>
        ${Object.entries(toggles).map(([id,label]) => `<label class="check"><input id="${id}" type="checkbox" ${this._config[id] ? "checked" : ""}>${label}</label>`).join("")}
      </div>
      <style>.editor{display:grid;gap:14px;padding:8px 0}label{display:grid;gap:6px}input[type=text],select{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}.check{display:flex;align-items:center;gap:8px}</style>`;
    ["entity","title",...Object.keys(toggles)].forEach((id) => {
      const element = this.querySelector(`#${id}`);
      element?.addEventListener(id === "title" ? "input" : "change", () => this.changed());
    });
  }

  changed() {
    const config = { ...this._config };
    ["entity","title"].forEach((id) => { config[id] = this.querySelector(`#${id}`)?.value; });
    ["compact","show_link","show_raw","show_statistics","show_relative_time"].forEach((id) => { config[id] = this.querySelector(`#${id}`)?.checked; });
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail:{ config }, bubbles:true, composed:true }));
  }
}

class P2000CompanionMonitorsCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode:"open" }); }
  setConfig(config) { this.config = { title:"P2000-monitoren", entities:[], show_empty:true, show_relative_time:true, ...config }; this.render(); }
  set hass(hass) { this._hass = hass; this.render(); }
  getCardSize() { return Math.max(2, (this.config?.entities?.length || 2) + 1); }
  static getStubConfig(hass) { return { title:"P2000-monitoren", entities:entityCandidates(hass).slice(0,6) }; }
  static async getConfigElement() { return document.createElement("p2000-companion-monitors-card-editor"); }

  render() {
    if (!this.config || !this._hass) return;
    let entityIds = Array.isArray(this.config.entities) ? this.config.entities : [];
    if (!entityIds.length) entityIds = entityCandidates(this._hass);
    const rows = entityIds
      .map((id) => ({ id, state: this._hass.states[id] }))
      .filter(({ state }) => state)
      .filter(({ state }) => this.config.show_empty || state.attributes?.summary || state.attributes?.message);

    this.shadowRoot.innerHTML = `
      <style>
        ${commonStyles}
        .wrap { padding:17px; }
        .header { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:1px 1px 13px; border-bottom:1px solid var(--p2-border); }
        .header-title { font-size:1.08rem; font-weight:750; overflow-wrap:anywhere; }
        .counter { flex:0 0 auto; padding:5px 9px; border-radius:9px; background:var(--p2-soft); color:var(--secondary-text-color); font-size:.75rem; font-weight:650; }
        .list { display:grid; gap:10px; margin-top:12px; }
        .row { position:relative; display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:13px; align-items:center; min-width:0; padding:13px; border:1px solid var(--p2-border); border-radius:14px; background:color-mix(in srgb,var(--card-background-color) 72%,transparent); overflow:hidden; }
        .row::before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--service-color); }
        .icon { width:44px; height:44px; border-radius:50%; display:grid; place-items:center; background:rgba(var(--service-rgb),.14); border:1px solid rgba(var(--service-rgb),.28); color:var(--service-color); }
        .icon ha-icon { --mdc-icon-size:25px; }
        .body { min-width:0; }
        .name-line { display:flex; align-items:center; flex-wrap:wrap; gap:7px; }
        .name { font-weight:750; line-height:1.2; overflow-wrap:anywhere; }
        .prio { display:inline-flex; align-items:center; min-height:23px; padding:3px 7px; border-radius:7px; color:#fff; background:var(--service-color); font-size:.72rem; font-weight:800; }
        .summary { margin-top:5px; color:var(--primary-text-color); font-size:.91rem; line-height:1.38; white-space:normal; overflow:visible; text-overflow:clip; overflow-wrap:anywhere; }
        .submeta { display:flex; align-items:center; flex-wrap:wrap; gap:5px 10px; margin-top:6px; color:var(--secondary-text-color); font-size:.76rem; }
        .submeta span { display:inline-flex; align-items:center; gap:4px; }
        .submeta ha-icon { --mdc-icon-size:14px; color:var(--service-color); }
        .right { align-self:center; min-width:62px; text-align:right; color:var(--secondary-text-color); font-size:.74rem; line-height:1.25; }
        .chevron { margin-top:5px; color:var(--service-color); }
        .chevron ha-icon { --mdc-icon-size:19px; }
        .empty { padding:12px 3px; color:var(--secondary-text-color); }
        @media (max-width:520px) {
          .wrap { padding:13px; }
          .row { grid-template-columns:auto minmax(0,1fr); }
          .right { grid-column:2; text-align:left; display:flex; align-items:center; gap:7px; min-width:0; }
          .chevron { margin-top:0; }
        }
      </style>
      <ha-card class="service-unknown">
        <div class="wrap">
          <div class="header"><div class="header-title">${escapeHtml(this.config.title)}</div><div class="counter">${rows.length} ${rows.length === 1 ? "monitor" : "monitoren"}</div></div>
          ${rows.length ? `<div class="list">${rows.map(({ id, state }) => {
            const a = state.attributes || {};
            const meta = serviceMeta(a.service);
            const published = a.published || a.timestamp || a.last_updated || state.last_updated;
            const summary = a.summary || a.message || state.state || "Geen melding";
            const location = a.city || a.place || a.location || "";
            return `<div class="row service-${escapeHtml(meta.className)}" title="${escapeHtml(id)}">
              <div class="icon"><ha-icon icon="${escapeHtml(meta.icon)}"></ha-icon></div>
              <div class="body">
                <div class="name-line"><span class="name">${escapeHtml(meta.label)}</span><span class="prio">${escapeHtml(a.priority || "—")}</span></div>
                <div class="summary">${escapeHtml(summary)}</div>
                <div class="submeta">
                  ${location ? `<span><ha-icon icon="mdi:map-marker"></ha-icon>${escapeHtml(location)}</span>` : ""}
                  <span><ha-icon icon="mdi:clock-outline"></ha-icon>${escapeHtml(formatDate(published))}</span>
                </div>
              </div>
              <div class="right">${this.config.show_relative_time ? `<div>${escapeHtml(formatRelative(published))}</div>` : ""}<div class="chevron"><ha-icon icon="mdi:chevron-right"></ha-icon></div></div>
            </div>`;
          }).join("")}</div>` : `<div class="empty">Geen monitoren of meldingen gevonden.</div>`}
        </div>
      </ha-card>`;
  }
}

class P2000CompanionMonitorsCardEditor extends HTMLElement {
  setConfig(config) { this._config={title:"P2000-monitoren",entities:[],show_empty:true,show_relative_time:true,...config}; this.render(); }
  set hass(hass) { this._hass=hass; this.render(); }
  render() {
    if (!this._config || !this._hass) return;
    const all = entityCandidates(this._hass);
    this.innerHTML=`<div class="editor"><label>Titel<input id="title" type="text" value="${escapeHtml(this._config.title||"")}"></label><fieldset><legend>Monitoren</legend>${all.map((id)=>`<label class="check"><input type="checkbox" data-entity="${escapeHtml(id)}" ${(this._config.entities||[]).includes(id)?"checked":""}>${escapeHtml(id)}</label>`).join("")}</fieldset><label class="check"><input id="show_empty" type="checkbox" ${this._config.show_empty!==false?"checked":""}>Monitoren zonder melding tonen</label><label class="check"><input id="show_relative_time" type="checkbox" ${this._config.show_relative_time!==false?"checked":""}>Relatieve tijd tonen</label></div><style>.editor{display:grid;gap:14px;padding:8px 0}label{display:grid;gap:6px}input[type=text]{width:100%;box-sizing:border-box;padding:10px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}fieldset{border:1px solid var(--divider-color);border-radius:8px;display:grid;gap:8px}.check{display:flex;align-items:center;gap:8px}</style>`;
    this.querySelector("#title")?.addEventListener("input",()=>this.changed());
    this.querySelector("#show_empty")?.addEventListener("change",()=>this.changed());
    this.querySelector("#show_relative_time")?.addEventListener("change",()=>this.changed());
    this.querySelectorAll("[data-entity]").forEach((el)=>el.addEventListener("change",()=>this.changed()));
  }
  changed(){
    const entities=[...this.querySelectorAll("[data-entity]:checked")].map((el)=>el.dataset.entity);
    const config={...this._config,title:this.querySelector("#title")?.value,show_empty:this.querySelector("#show_empty")?.checked,show_relative_time:this.querySelector("#show_relative_time")?.checked,entities};
    this._config=config;
    this.dispatchEvent(new CustomEvent("config-changed",{detail:{config},bubbles:true,composed:true}));
  }
}

if (!customElements.get("p2000-companion-card")) customElements.define("p2000-companion-card", P2000CompanionCard);
if (!customElements.get("p2000-companion-card-editor")) customElements.define("p2000-companion-card-editor", P2000CompanionCardEditor);
if (!customElements.get("p2000-companion-monitors-card")) customElements.define("p2000-companion-monitors-card", P2000CompanionMonitorsCard);
if (!customElements.get("p2000-companion-monitors-card-editor")) customElements.define("p2000-companion-monitors-card-editor", P2000CompanionMonitorsCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "p2000-companion-card")) window.customCards.push({ type:"p2000-companion-card", name:"P2000 Incident Card", description:"Moderne weergave van de laatste melding van één P2000-monitor.", preview:true, documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion" });
if (!window.customCards.some((card) => card.type === "p2000-companion-monitors-card")) window.customCards.push({ type:"p2000-companion-monitors-card", name:"P2000 Monitorenkaart", description:"Modern en volledig leesbaar overzicht van meerdere P2000-monitorprofielen.", preview:true, documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion" });
console.info(`%c P2000 COMPANION CARDS %c v${CARD_VERSION} `,"color:white;background:#17365d;font-weight:bold;","color:#17365d;background:white;");
