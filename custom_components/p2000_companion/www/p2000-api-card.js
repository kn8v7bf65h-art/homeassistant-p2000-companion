const P2000_API_CARD_VERSION = "3.2.0";

const API_SERVICE_FALLBACK = {
  ambulance: { label: "Ambulance", mdi: "mdi:ambulance", emoji: "🚑", color: "#F59E0B" },
  fire: { label: "Brandweer", mdi: "mdi:fire-truck", emoji: "🚒", color: "#EF4444" },
  police: { label: "Politie", mdi: "mdi:police-badge", emoji: "🚓", color: "#EAB308" },
  mmt: { label: "MMT / Lifeliner", mdi: "mdi:helicopter", emoji: "🚁", color: "#8B5CF6" },
  lifeboat: { label: "KNRM", mdi: "mdi:lifebuoy", emoji: "🛟", color: "#F97316" },
};

const apiEscape = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));

const apiEntities = (hass) => Object.keys(hass?.states || {})
  .filter((id) => id.startsWith("sensor.") && hass.states[id].attributes?.provider === "api")
  .sort();

const apiServiceEntities = (hass) => apiEntities(hass)
  .filter((id) => hass.states[id].attributes?.service_filter);

const apiMeta = (a = {}) => {
  const service = String(a.service || a.service_filter || a.service_type || "").toLowerCase();
  const fallback = API_SERVICE_FALLBACK[service] || {
    label: a.service_label || "P2000",
    mdi: a.icon || "mdi:alarm-light",
    emoji: a.service_icon || "🚨",
    color: a.service_color || "#03A9F4",
  };
  return {
    service,
    label: a.service_label || fallback.label,
    mdi: a.icon || fallback.mdi,
    emoji: a.service_icon || fallback.emoji,
    color: a.service_color || fallback.color,
  };
};

const apiPublished = (a, state) => a.time_formatted || a.published || state?.last_updated || "";
const apiRelative = (a) => a.time_relative || "";
const apiLocation = (a) => a.location_full || [a.location_street, a.location_city].filter(Boolean).join(", ") || a.city || "Onbekende locatie";
const apiPriority = (a) => a.priority_label || a.priority || "—";

const apiCommonStyles = `
  :host { display:block; --api-radius:18px; --api-border:color-mix(in srgb,var(--divider-color) 72%,transparent); }
  * { box-sizing:border-box; }
  ha-card { overflow:hidden; border-radius:var(--api-radius); border:1px solid var(--api-border); background:var(--card-background-color); box-shadow:0 10px 28px rgba(0,0,0,.10); }
  ha-icon { vertical-align:middle; }
  .empty { padding:20px; color:var(--secondary-text-color); }
`;

class P2000ApiIncidentCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode:"open" }); }
  set hass(hass) { this._hass = hass; this.render(); }
  setConfig(config) {
    if (!config?.entity) throw new Error("Kies een P2000 API-entiteit");
    this.config = { title:"P2000 API", show_link:true, show_capcodes:false, show_source_status:true, ...config };
    this.render();
  }
  getCardSize() { return 5; }
  static getStubConfig(hass) { return { entity:apiEntities(hass)[0] || "sensor.p2000_api_laatste_gefilterde_melding", title:"P2000 API" }; }
  static async getConfigElement() { return document.createElement("p2000-api-incident-card-editor"); }

  render() {
    if (!this.config || !this._hass) return;
    const state = this._hass.states[this.config.entity];
    if (!state) {
      this.shadowRoot.innerHTML = `<style>${apiCommonStyles}</style><ha-card><div class="empty">Entiteit ${apiEscape(this.config.entity)} niet gevonden.</div></ha-card>`;
      return;
    }
    const a = state.attributes || {};
    if (a.provider !== "api") {
      this.shadowRoot.innerHTML = `<style>${apiCommonStyles}</style><ha-card><div class="empty">Deze kaart accepteert alleen P2000-entiteiten met provider: api.</div></ha-card>`;
      return;
    }
    const meta = apiMeta(a);
    const summary = a.summary || a.message || state.state || "Geen melding";
    const location = apiLocation(a);
    const priority = apiPriority(a);
    const relative = apiRelative(a);
    const link = a.link || a.url;
    const capcodes = Array.isArray(a.capcodes) ? a.capcodes.map((c)=>String(c).trim()).filter(Boolean) : [];
    const corrected = a.service_corrected || a.location_corrected;
    const status = this.config.show_source_status ? `<span class="source ${corrected ? "corrected" : ""}"><ha-icon icon="${corrected ? "mdi:auto-fix" : "mdi:api"}"></ha-icon>${corrected ? "Lokaal gecorrigeerd" : "API-data"}</span>` : "";
    const capcodeBlock = this.config.show_capcodes && capcodes.length ? `<div class="capcodes"><span>Capcodes</span>${capcodes.map((c)=>`<code>${apiEscape(c)}</code>`).join("")}</div>` : "";
    const openLink = this.config.show_link && link ? `<a class="open" href="${apiEscape(link)}" target="_blank" rel="noopener noreferrer"><ha-icon icon="mdi:open-in-new"></ha-icon>Open melding</a>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${apiCommonStyles}
        ha-card { --service:${apiEscape(meta.color)}; background:radial-gradient(circle at 100% 0%,color-mix(in srgb,var(--service) 12%,transparent),transparent 42%),var(--card-background-color); }
        .accent { height:5px; background:var(--service); }
        .wrap { padding:18px; }
        .head { display:flex; justify-content:space-between; gap:14px; align-items:flex-start; }
        .identity { display:flex; gap:12px; align-items:center; min-width:0; }
        .emoji { width:50px; height:50px; display:grid; place-items:center; border-radius:50%; font-size:27px; background:color-mix(in srgb,var(--service) 14%,transparent); border:1px solid color-mix(in srgb,var(--service) 34%,transparent); }
        .title { font-size:1.08rem; font-weight:750; }
        .service { margin-top:3px; color:var(--secondary-text-color); font-size:.84rem; }
        .prio { flex:0 0 auto; padding:7px 11px; border-radius:10px; background:var(--service); color:#fff; font-weight:850; }
        .message { margin-top:18px; font-size:1.18rem; line-height:1.42; font-weight:700; overflow-wrap:anywhere; }
        .meta { display:grid; gap:9px; margin-top:15px; color:var(--secondary-text-color); font-size:.86rem; }
        .meta-line { display:flex; align-items:flex-start; gap:7px; }
        .meta-line ha-icon { --mdc-icon-size:18px; color:var(--service); }
        .footer { display:flex; gap:9px; flex-wrap:wrap; align-items:center; margin-top:17px; padding-top:14px; border-top:1px solid var(--api-border); }
        .source,.open { display:inline-flex; align-items:center; gap:6px; min-height:34px; padding:7px 10px; border-radius:9px; background:color-mix(in srgb,var(--service) 10%,transparent); color:var(--service); font-size:.78rem; font-weight:700; text-decoration:none; }
        .source.corrected { background:color-mix(in srgb,#8B5CF6 12%,transparent); color:#8B5CF6; }
        .source ha-icon,.open ha-icon { --mdc-icon-size:17px; }
        .relative { margin-left:auto; color:var(--primary-text-color); font-size:.8rem; font-weight:650; }
        .capcodes { display:flex; gap:7px; align-items:center; flex-wrap:wrap; margin-top:14px; color:var(--secondary-text-color); font-size:.76rem; }
        .capcodes code { padding:4px 7px; border-radius:7px; background:var(--secondary-background-color); color:var(--primary-text-color); }
        @media(max-width:520px){ .wrap{padding:15px}.emoji{width:44px;height:44px;font-size:24px}.message{font-size:1.06rem}.relative{margin-left:0;width:100%} }
      </style>
      <ha-card>
        <div class="accent"></div><div class="wrap">
          <div class="head"><div class="identity"><div class="emoji">${apiEscape(meta.emoji)}</div><div><div class="title">${apiEscape(this.config.title)}</div><div class="service">${apiEscape(meta.label)} · ${apiEscape(a.monitor_name || "P2000 API")}</div></div></div><div class="prio">${apiEscape(priority)}</div></div>
          <div class="message">${apiEscape(summary)}</div>
          <div class="meta"><div class="meta-line"><ha-icon icon="mdi:map-marker"></ha-icon><span>${apiEscape(location)}</span></div><div class="meta-line"><ha-icon icon="mdi:clock-outline"></ha-icon><span>${apiEscape(apiPublished(a,state))}</span></div></div>
          ${capcodeBlock}
          <div class="footer">${status}${openLink}${relative ? `<span class="relative">${apiEscape(relative)}</span>` : ""}</div>
        </div>
      </ha-card>`;
  }
}

class P2000ApiServicesCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode:"open" }); }
  set hass(hass) { this._hass = hass; this.render(); }
  setConfig(config) { this.config = { title:"P2000 API · Hulpdiensten", entities:[], show_relative_time:true, ...config }; this.render(); }
  getCardSize() { return Math.max(3,(this.config?.entities?.length || 4)+1); }
  static getStubConfig(hass) { return { title:"P2000 API · Hulpdiensten", entities:apiServiceEntities(hass) }; }
  static async getConfigElement() { return document.createElement("p2000-api-services-card-editor"); }

  render() {
    if (!this.config || !this._hass) return;
    let ids = Array.isArray(this.config.entities) ? this.config.entities : [];
    if (!ids.length) ids = apiServiceEntities(this._hass);
    const rows = ids.map((id)=>({id,state:this._hass.states[id]})).filter(({state})=>state?.attributes?.provider === "api");
    this.shadowRoot.innerHTML = `
      <style>
        ${apiCommonStyles}
        .wrap{padding:16px}.head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:1px 1px 13px;border-bottom:1px solid var(--api-border)}
        .title{font-size:1.08rem;font-weight:750}.badge{padding:5px 9px;border-radius:9px;background:var(--secondary-background-color);color:var(--secondary-text-color);font-size:.75rem;font-weight:700}
        .list{display:grid;gap:10px;margin-top:12px}.row{--service:#03A9F4;position:relative;display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;padding:13px;border:1px solid var(--api-border);border-radius:14px;background:color-mix(in srgb,var(--card-background-color) 72%,transparent);overflow:hidden}
        .row::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:var(--service)}.emoji{width:44px;height:44px;display:grid;place-items:center;border-radius:50%;font-size:23px;background:color-mix(in srgb,var(--service) 14%,transparent);border:1px solid color-mix(in srgb,var(--service) 30%,transparent)}
        .body{min-width:0}.name{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-weight:780}.prio{padding:3px 7px;border-radius:7px;background:var(--service);color:#fff;font-size:.7rem;font-weight:850}.message{margin-top:5px;font-size:.9rem;line-height:1.36;overflow-wrap:anywhere}.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;color:var(--secondary-text-color);font-size:.75rem}.meta span{display:inline-flex;align-items:center;gap:4px}.meta ha-icon{--mdc-icon-size:14px;color:var(--service)}
        .right{text-align:right;color:var(--secondary-text-color);font-size:.75rem;min-width:72px}.open{margin-top:5px;color:var(--service)}.open ha-icon{--mdc-icon-size:18px}.empty{padding:14px 2px;color:var(--secondary-text-color)}
        @media(max-width:520px){.wrap{padding:13px}.row{grid-template-columns:auto minmax(0,1fr)}.right{grid-column:2;text-align:left;min-width:0}}
      </style>
      <ha-card><div class="wrap"><div class="head"><div class="title">${apiEscape(this.config.title)}</div><div class="badge">${rows.length} diensten</div></div>
      ${rows.length ? `<div class="list">${rows.map(({id,state})=>{const a=state.attributes||{};const m=apiMeta(a);const link=a.link||a.url;return `<div class="row" style="--service:${apiEscape(m.color)}" title="${apiEscape(id)}"><div class="emoji">${apiEscape(m.emoji)}</div><div class="body"><div class="name"><span>${apiEscape(m.label)}</span><span class="prio">${apiEscape(apiPriority(a))}</span></div><div class="message">${apiEscape(a.summary||a.message||state.state||"Geen melding")}</div><div class="meta"><span><ha-icon icon="mdi:map-marker"></ha-icon>${apiEscape(apiLocation(a))}</span><span><ha-icon icon="mdi:clock-outline"></ha-icon>${apiEscape(apiPublished(a,state))}</span></div></div><div class="right">${this.config.show_relative_time && apiRelative(a)?`<div>${apiEscape(apiRelative(a))}</div>`:""}${link?`<div class="open" data-url="${apiEscape(link)}"><ha-icon icon="mdi:open-in-new"></ha-icon></div>`:""}</div></div>`;}).join("")}</div>` : `<div class="empty">Geen API-hulpdienstsensoren gevonden.</div>`}</div></ha-card>`;
    this.shadowRoot.querySelectorAll("[data-url]").forEach((el)=>el.addEventListener("click",()=>window.open(el.dataset.url,"_blank","noopener")));
  }
}

class P2000ApiIncidentCardEditor extends HTMLElement {
  set hass(hass){this._hass=hass;this.render()} setConfig(config){this._config={title:"P2000 API",show_link:true,show_capcodes:false,show_source_status:true,...config};this.render()}
  render(){if(!this._hass||!this._config)return;const entities=apiEntities(this._hass);this.innerHTML=`<div class="ed"><label>Entiteit<select id="entity">${entities.map((id)=>`<option value="${apiEscape(id)}" ${id===this._config.entity?"selected":""}>${apiEscape(id)}</option>`).join("")}</select></label><label>Titel<input id="title" value="${apiEscape(this._config.title||"")}"></label><label class="c"><input id="show_link" type="checkbox" ${this._config.show_link!==false?"checked":""}>Link tonen</label><label class="c"><input id="show_capcodes" type="checkbox" ${this._config.show_capcodes?"checked":""}>Capcodes tonen</label><label class="c"><input id="show_source_status" type="checkbox" ${this._config.show_source_status!==false?"checked":""}>API/correctiestatus tonen</label></div><style>.ed{display:grid;gap:12px}label{display:grid;gap:6px}.c{display:flex;gap:8px;align-items:center}select,input{padding:9px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style>`;this.querySelectorAll("input,select").forEach((el)=>el.addEventListener("change",()=>this.changed()));this.querySelector("#title")?.addEventListener("input",()=>this.changed())}
  changed(){const config={...this._config,entity:this.querySelector("#entity")?.value,title:this.querySelector("#title")?.value,show_link:this.querySelector("#show_link")?.checked,show_capcodes:this.querySelector("#show_capcodes")?.checked,show_source_status:this.querySelector("#show_source_status")?.checked};this._config=config;this.dispatchEvent(new CustomEvent("config-changed",{detail:{config},bubbles:true,composed:true}))}
}

class P2000ApiServicesCardEditor extends HTMLElement {
  set hass(hass){this._hass=hass;this.render()} setConfig(config){this._config={title:"P2000 API · Hulpdiensten",entities:[],show_relative_time:true,...config};this.render()}
  render(){if(!this._hass||!this._config)return;const all=apiServiceEntities(this._hass);this.innerHTML=`<div class="ed"><label>Titel<input id="title" value="${apiEscape(this._config.title||"")}"></label><fieldset><legend>API-hulpdiensten</legend>${all.map((id)=>`<label class="c"><input type="checkbox" data-entity="${apiEscape(id)}" ${!(this._config.entities||[]).length||(this._config.entities||[]).includes(id)?"checked":""}>${apiEscape(id)}</label>`).join("")}</fieldset><label class="c"><input id="relative" type="checkbox" ${this._config.show_relative_time!==false?"checked":""}>Relatieve tijd tonen</label></div><style>.ed{display:grid;gap:12px}label{display:grid;gap:6px}.c{display:flex;gap:8px;align-items:center}fieldset{border:1px solid var(--divider-color);border-radius:8px;display:grid;gap:7px}input{padding:9px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style>`;this.querySelectorAll("input").forEach((el)=>el.addEventListener("change",()=>this.changed()));this.querySelector("#title")?.addEventListener("input",()=>this.changed())}
  changed(){const entities=[...this.querySelectorAll("[data-entity]:checked")].map((el)=>el.dataset.entity);const config={...this._config,title:this.querySelector("#title")?.value,entities,show_relative_time:this.querySelector("#relative")?.checked};this._config=config;this.dispatchEvent(new CustomEvent("config-changed",{detail:{config},bubbles:true,composed:true}))}
}

if(!customElements.get("p2000-api-incident-card"))customElements.define("p2000-api-incident-card",P2000ApiIncidentCard);
if(!customElements.get("p2000-api-services-card"))customElements.define("p2000-api-services-card",P2000ApiServicesCard);
if(!customElements.get("p2000-api-incident-card-editor"))customElements.define("p2000-api-incident-card-editor",P2000ApiIncidentCardEditor);
if(!customElements.get("p2000-api-services-card-editor"))customElements.define("p2000-api-services-card-editor",P2000ApiServicesCardEditor);

window.customCards=window.customCards||[];
if(!window.customCards.some((c)=>c.type==="p2000-api-incident-card"))window.customCards.push({type:"p2000-api-incident-card",name:"P2000 API Incident Card",description:"API-only kaart voor één P2000 Haaglanden-melding.",preview:true,documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion"});
if(!window.customCards.some((c)=>c.type==="p2000-api-services-card"))window.customCards.push({type:"p2000-api-services-card",name:"P2000 API Hulpdiensten",description:"API-only overzicht van de laatste melding per hulpdienst.",preview:true,documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion"});
console.info(`%c P2000 API CARDS %c v${P2000_API_CARD_VERSION} `,"color:white;background:#152238;font-weight:bold;","color:#152238;background:white;");
