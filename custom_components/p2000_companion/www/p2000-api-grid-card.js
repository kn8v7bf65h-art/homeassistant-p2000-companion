const P2000_API_GRID_VERSION = "3.2.0";

const GRID_META = {
  ambulance: { label: "Ambulance", icon: "🚑", color: "#F59E0B" },
  fire: { label: "Brandweer", icon: "🚒", color: "#EF4444" },
  police: { label: "Politie", icon: "🚓", color: "#EAB308" },
  mmt: { label: "MMT / Lifeliner", icon: "🚁", color: "#8B5CF6" },
  lifeboat: { label: "KNRM", icon: "🛟", color: "#F97316" },
};

const esc = (v) => String(v ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));

class P2000ApiServicesGridCard extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:"open"}); }
  set hass(hass){ this._hass=hass; this.render(); }
  setConfig(config){ this.config={title:"P2000 Haaglanden",show_relative_time:true,...config}; this.render(); }
  getCardSize(){ return 4; }
  static getStubConfig(){ return {title:"P2000 Haaglanden",show_relative_time:true}; }

  render(){
    if(!this._hass||!this.config) return;
    const states=Object.entries(this._hass.states||{})
      .filter(([id,s])=>id.startsWith("sensor.")&&s.attributes?.provider==="api"&&s.attributes?.service_filter)
      .map(([id,state])=>({id,state}));

    const order=["ambulance","fire","police","mmt","lifeboat"];
    states.sort((a,b)=>order.indexOf(a.state.attributes.service_filter)-order.indexOf(b.state.attributes.service_filter));

    this.shadowRoot.innerHTML=`
      <style>
        :host{display:block}*{box-sizing:border-box}
        ha-card{border-radius:18px;overflow:hidden;border:1px solid color-mix(in srgb,var(--divider-color) 72%,transparent);background:var(--card-background-color);box-shadow:0 10px 28px rgba(0,0,0,.10)}
        .wrap{padding:16px}.head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.title{font-size:1.08rem;font-weight:760}.count{padding:5px 9px;border-radius:9px;background:var(--secondary-background-color);color:var(--secondary-text-color);font-size:.75rem;font-weight:700}
        .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.tile{--service:#03A9F4;position:relative;min-width:0;padding:14px;border-radius:16px;border:1px solid color-mix(in srgb,var(--service) 24%,var(--divider-color));background:linear-gradient(145deg,color-mix(in srgb,var(--service) 10%,var(--card-background-color)),var(--card-background-color));overflow:hidden;cursor:pointer;transition:transform .16s ease,border-color .16s ease}.tile:hover{transform:translateY(-1px);border-color:color-mix(in srgb,var(--service) 46%,var(--divider-color))}.tile::after{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:var(--service)}
        .top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.identity{display:flex;gap:10px;align-items:center;min-width:0}.emoji{width:42px;height:42px;display:grid;place-items:center;border-radius:13px;font-size:23px;background:color-mix(in srgb,var(--service) 14%,transparent)}.service{font-weight:800;line-height:1.15}.prio{padding:4px 7px;border-radius:7px;background:var(--service);color:#fff;font-size:.7rem;font-weight:850;white-space:nowrap}
        .message{margin-top:11px;font-size:.9rem;font-weight:650;line-height:1.38;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.meta{display:grid;gap:5px;margin-top:10px;color:var(--secondary-text-color);font-size:.74rem}.meta div{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.relative{margin-top:9px;font-size:.74rem;font-weight:700;color:var(--service)}
        .empty{padding:12px 2px;color:var(--secondary-text-color)}
        @media(max-width:600px){.grid{grid-template-columns:1fr}.wrap{padding:13px}}
      </style>
      <ha-card><div class="wrap"><div class="head"><div class="title">${esc(this.config.title)}</div><div class="count">${states.length} diensten</div></div>
      ${states.length?`<div class="grid">${states.map(({id,state})=>{const a=state.attributes||{};const svc=String(a.service_filter||a.service||"").toLowerCase();const m=GRID_META[svc]||{label:a.service_label||svc||"P2000",icon:a.service_icon||"🚨",color:a.service_color||"#03A9F4"};const location=a.location_full||a.city||"Onbekende locatie";const rel=a.time_relative||"";const link=a.link||a.url||"";return `<div class="tile" data-url="${esc(link)}" style="--service:${esc(a.service_color||m.color)}" title="${esc(id)}"><div class="top"><div class="identity"><div class="emoji">${esc(a.service_icon||m.icon)}</div><div class="service">${esc(a.service_label||m.label)}</div></div><div class="prio">${esc(a.priority_label||a.priority||"—")}</div></div><div class="message">${esc(a.summary||a.message||state.state||"Geen melding")}</div><div class="meta"><div>📍 ${esc(location)}</div><div>🕒 ${esc(a.time_formatted||a.published||"")}</div></div>${this.config.show_relative_time&&rel?`<div class="relative">${esc(rel)}</div>`:""}</div>`;}).join("")}</div>`:`<div class="empty">Geen API-hulpdienstsensoren gevonden.</div>`}</div></ha-card>`;
    this.shadowRoot.querySelectorAll("[data-url]").forEach(el=>el.addEventListener("click",()=>{if(el.dataset.url) window.open(el.dataset.url,"_blank","noopener");}));
  }
}

if(!customElements.get("p2000-api-services-grid-card")) customElements.define("p2000-api-services-grid-card",P2000ApiServicesGridCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==="p2000-api-services-grid-card")) window.customCards.push({type:"p2000-api-services-grid-card",name:"P2000 API Hulpdiensten Grid",description:"API-only tegeloverzicht van de laatste melding per hulpdienst.",preview:true,documentationURL:"https://github.com/kn8v7bf65h-art/homeassistant-p2000-companion"});
console.info(`%c P2000 API GRID %c v${P2000_API_GRID_VERSION} `,"color:white;background:#17365d;font-weight:bold;","color:#17365d;background:white;");
