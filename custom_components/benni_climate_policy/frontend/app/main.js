const DOMAIN = "benni_climate_policy";

const ENTITIES = {
  systemReady: "binary_sensor.climate_system_ready",
  applyReady: "binary_sensor.climate_policy_apply_ready",
  applyActive: "switch.climate_policy_apply_active",
  effectiveTemp: "sensor.climate_effective_outdoor_temperature",
  applyStatus: "sensor.climate_policy_apply_status",
  lastApply: "sensor.climate_policy_last_apply",
  debugSummary: "sensor.climate_debug_summary",
};

const ZONES = {
  living_room: {
    label: "Wohnzimmer",
    mode: "sensor.living_room_climate_mode",
    target: "sensor.living_room_climate_target_temp",
    planHash: "sensor.living_room_climate_plan_hash",
    pendingHash: "sensor.living_room_climate_pending_plan_hash",
    lastAppliedHash: "sensor.living_room_climate_last_applied_plan_hash",
    applyReason: "sensor.living_room_climate_apply_reason",
    blocked: "binary_sensor.living_room_climate_apply_blocked",
  },
  kitchen: {
    label: "Küche",
    mode: "sensor.kitchen_climate_mode",
    target: "sensor.kitchen_climate_target_temp",
    planHash: "sensor.kitchen_climate_plan_hash",
    pendingHash: "sensor.kitchen_climate_pending_plan_hash",
    lastAppliedHash: "sensor.kitchen_climate_last_applied_plan_hash",
    applyReason: "sensor.kitchen_climate_apply_reason",
    blocked: "binary_sensor.kitchen_climate_apply_blocked",
  },
};

const NAV = [
  ["overview", "Overview", "mdi:view-dashboard-outline"],
  ["context", "Context", "mdi:account-clock-outline"],
  ["zones", "Zones", "mdi:home-thermometer-outline"],
  ["thresholds", "Thresholds", "mdi:tune-vertical-variant"],
  ["effective", "Effective Temp", "mdi:thermometer-lines"],
  ["apply", "Apply", "mdi:play-circle-outline"],
  ["inputs", "Inputs", "mdi:database-search-outline"],
  ["debug", "Debug", "mdi:code-json"],
];

const CSS = `
:host, * { box-sizing: border-box; }
:host {
  --bcp-bg: var(--primary-background-color, #f5f6f8);
  --bcp-surface: var(--card-background-color, #ffffff);
  --bcp-panel: var(--secondary-background-color, #eef1f5);
  --bcp-line: var(--divider-color, #d8dde5);
  --bcp-text: var(--primary-text-color, #111827);
  --bcp-muted: var(--secondary-text-color, #64748b);
  --bcp-accent: var(--primary-color, #2563eb);
  --bcp-ok: #16803c;
  --bcp-warn: #9a6700;
  --bcp-error: #b42318;
  --bcp-info: #0369a1;
  display: block;
  min-height: 100vh;
  color: var(--bcp-text);
  font-family: var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
}
.app { display: grid; grid-template-columns: 238px minmax(0, 1fr); min-height: 100vh; background: var(--bcp-bg); }
.sidebar { border-right: 1px solid var(--bcp-line); background: var(--bcp-panel); padding: 16px 10px; display: flex; flex-direction: column; gap: 14px; }
.brand { display: grid; grid-template-columns: 36px 1fr; gap: 10px; align-items: center; padding: 4px 8px 10px; }
.brand ha-icon { color: var(--bcp-accent); }
.brand b { display: block; font-size: 15px; line-height: 1.2; }
.brand small { color: var(--bcp-muted); font-size: 12px; }
.nav { display: flex; flex-direction: column; gap: 3px; }
.nav button { display: grid; grid-template-columns: 22px 1fr; gap: 9px; align-items: center; width: 100%; min-height: 39px;
  border: 0; border-radius: 8px; padding: 8px 10px; background: transparent; color: var(--bcp-muted); text-align: left; cursor: pointer; font: inherit; }
.nav button:hover { background: color-mix(in srgb, var(--bcp-accent) 8%, transparent); color: var(--bcp-text); }
.nav button.active { background: color-mix(in srgb, var(--bcp-accent) 15%, transparent); color: var(--bcp-accent); font-weight: 650; }
.side-foot { margin-top: auto; border-top: 1px solid var(--bcp-line); padding: 11px 8px 0; color: var(--bcp-muted); font-size: 12px; overflow-wrap: anywhere; }
.main { min-width: 0; padding: 22px 26px 32px; }
.head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 18px; }
.head h1 { margin: 0; font-size: 23px; letter-spacing: 0; }
.head p { margin: 3px 0 0; color: var(--bcp-muted); font-size: 13px; }
.chips { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.grid { display: grid; gap: 12px; }
.cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.section { margin-top: 16px; }
.card { background: var(--bcp-surface); border: 1px solid var(--bcp-line); border-radius: 8px; padding: 14px; min-width: 0; }
.card h2 { margin: 0 0 11px; font-size: 14px; display: flex; gap: 8px; align-items: center; }
.card h2 ha-icon { color: var(--bcp-accent); }
.metric { background: var(--bcp-surface); border: 1px solid var(--bcp-line); border-radius: 8px; padding: 12px 13px; min-height: 78px; }
.metric .label { color: var(--bcp-muted); font-size: 12px; margin-bottom: 6px; }
.metric .value { font-size: 18px; font-weight: 700; overflow-wrap: anywhere; }
.metric .entity { margin-top: 5px; color: var(--bcp-muted); font-size: 11px; font-family: ui-monospace, "Cascadia Code", monospace; overflow-wrap: anywhere; }
.kv { display: grid; grid-template-columns: minmax(130px, .7fr) minmax(0, 1fr); gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--bcp-line); }
.kv:last-child { border-bottom: 0; }
.k { color: var(--bcp-muted); font-size: 13px; }
.v { font-size: 13px; font-weight: 600; min-width: 0; overflow-wrap: anywhere; }
.mono { font-family: ui-monospace, "Cascadia Code", monospace; font-size: 12px; }
.muted { color: var(--bcp-muted); }
.status { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--bcp-line); border-radius: 999px; padding: 3px 9px; font-size: 12px; font-weight: 650; white-space: nowrap; }
.status::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.ok { color: var(--bcp-ok); }
.warn { color: var(--bcp-warn); }
.error { color: var(--bcp-error); }
.info { color: var(--bcp-info); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 9px; border-bottom: 1px solid var(--bcp-line); text-align: left; vertical-align: top; font-size: 13px; }
th { color: var(--bcp-muted); font-size: 12px; font-weight: 650; }
.table-wrap { overflow-x: auto; }
.pre { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--bcp-panel); border: 1px solid var(--bcp-line); border-radius: 8px; padding: 11px; max-height: 440px; overflow: auto; }
.actions { display: flex; flex-wrap: wrap; gap: 9px; }
button.action { display: inline-grid; grid-template-columns: 18px auto; gap: 7px; align-items: center; min-height: 36px; border: 1px solid var(--bcp-line);
  border-radius: 8px; background: var(--bcp-surface); color: var(--bcp-text); padding: 8px 11px; cursor: pointer; font: inherit; }
button.action:hover { border-color: var(--bcp-accent); }
button.action.primary { background: var(--bcp-accent); color: var(--text-primary-color, #fff); border-color: var(--bcp-accent); }
button.action[disabled] { opacity: .55; cursor: not-allowed; }
.notice { border: 1px dashed var(--bcp-line); border-radius: 8px; padding: 13px; color: var(--bcp-muted); background: color-mix(in srgb, var(--bcp-panel) 70%, transparent); }
.toast { position: fixed; left: 50%; bottom: 20px; transform: translateX(-50%); background: var(--bcp-surface); border: 1px solid var(--bcp-line);
  border-radius: 8px; padding: 10px 14px; box-shadow: 0 10px 30px rgba(0,0,0,.22); z-index: 10; }
@media (max-width: 980px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { border-right: 0; border-bottom: 1px solid var(--bcp-line); }
  .nav { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .side-foot { display: none; }
  .main { padding: 18px 14px 26px; }
  .head { display: block; }
  .chips { justify-content: flex-start; margin-top: 12px; }
  .cols-2, .cols-3, .cols-4 { grid-template-columns: 1fr; }
  .kv { grid-template-columns: 1fr; gap: 3px; }
}
`;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function asText(value, missing = "missing") {
  if (value === undefined || value === null || value === "") return missing;
  if (Array.isArray(value)) return value.length ? value.join(", ") : "none";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function stateObj(hass, entityId) {
  return hass && entityId ? hass.states[entityId] : undefined;
}

function stateText(hass, entityId, missing = "missing") {
  const st = stateObj(hass, entityId);
  return st ? st.state : missing;
}

function attr(hass, entityId, name, missing = undefined) {
  const st = stateObj(hass, entityId);
  return st && st.attributes && st.attributes[name] !== undefined ? st.attributes[name] : missing;
}

function debugAttrs(hass) {
  return (stateObj(hass, ENTITIES.debugSummary) || {}).attributes || {};
}

function debugPayload(hass) {
  return debugAttrs(hass).debug || {};
}

function plans(hass) {
  return debugAttrs(hass).plans || {};
}

function contextSnapshot(hass) {
  return debugAttrs(hass).context || {};
}

function effectiveBreakdown(hass) {
  const fromDebug = debugAttrs(hass).effective_outdoor_temperature || {};
  const fromSensor = (stateObj(hass, ENTITIES.effectiveTemp) || {}).attributes || {};
  return { ...fromDebug, ...fromSensor };
}

function effectiveInputs(hass) {
  const fromDebug = debugPayload(hass).effective_inputs || {};
  const fromSensor = attr(hass, ENTITIES.effectiveTemp, "inputs", {}) || {};
  return { ...fromDebug, ...fromSensor };
}

function thresholds(hass) {
  return debugPayload(hass).thresholds || {};
}

function statusKind(value) {
  if (value === true || value === "on" || value === "ok" || value === "applied") return "ok";
  if (value === false || value === "off" || value === "idle" || value === "skipped" || value === "dry_run") return "info";
  if (value === "missing" || value === "unknown" || value === "unavailable" || value === "blocked") return "warn";
  if (value === "error") return "error";
  return "info";
}

function statusChip(value, label = value) {
  return `<span class="status ${statusKind(value)}">${esc(label)}</span>`;
}

function icon(name) {
  return `<ha-icon icon="${esc(name)}"></ha-icon>`;
}

function kv(label, value, cls = "") {
  return `<div class="kv"><div class="k">${esc(label)}</div><div class="v ${cls}">${esc(asText(value))}</div></div>`;
}

function kvSource(label, value, source, cls = "") {
  return `<div class="kv"><div class="k">${esc(label)}<br><span class="muted">${esc(source || "default")}</span></div><div class="v ${cls}">${esc(asText(value))}</div></div>`;
}

function metric(label, value, entityId = "") {
  return `<div class="metric"><div class="label">${esc(label)}</div><div class="value">${esc(asText(value))}</div>${entityId ? `<div class="entity">${esc(entityId)}</div>` : ""}</div>`;
}

function jsonBlock(value) {
  return `<div class="pre mono">${esc(JSON.stringify(value ?? null, null, 2))}</div>`;
}

function serviceAvailable(hass, service) {
  return Boolean(hass && hass.services && hass.services[DOMAIN] && hass.services[DOMAIN][service]);
}

function entityAvailable(hass, entityId) {
  return Boolean(stateObj(hass, entityId));
}

function zonePlan(hass, zone) {
  const plan = plans(hass)[zone] || {};
  const z = ZONES[zone];
  return {
    ...plan,
    profile: plan.profile ?? stateText(hass, z.mode),
    target_temperature: plan.target_temperature ?? stateText(hass, z.target),
    plan_hash: plan.plan_hash ?? stateText(hass, z.planHash),
    pending_plan_hash: stateText(hass, z.pendingHash, plan.plan_hash ?? "missing"),
    last_applied_plan_hash: stateText(hass, z.lastAppliedHash, "never"),
    apply_blocked: stateText(hass, z.blocked, "missing"),
    apply_reason: stateText(hass, z.applyReason, plan.apply_block_reason ?? "missing"),
  };
}

function renderOverview(hass) {
  const living = zonePlan(hass, "living_room");
  const kitchen = zonePlan(hass, "kitchen");
  const loaded = Object.keys(hass?.states || {}).some((id) =>
    id.includes("climate_policy") || id.includes("climate_effective") || id.includes("climate_system_ready"));
  return `
    <div class="grid cols-4">
      ${metric("Integration geladen", loaded ? "ja" : "nein")}
      ${metric("System Ready", stateText(hass, ENTITIES.systemReady), ENTITIES.systemReady)}
      ${metric("Apply Active", stateText(hass, ENTITIES.applyActive), ENTITIES.applyActive)}
      ${metric("Effective Outdoor Temp", stateText(hass, ENTITIES.effectiveTemp), ENTITIES.effectiveTemp)}
      ${metric("Wohnzimmer Mode", living.profile, ZONES.living_room.mode)}
      ${metric("Wohnzimmer Zieltemperatur", living.target_temperature, ZONES.living_room.target)}
      ${metric("Küche Mode", kitchen.profile, ZONES.kitchen.mode)}
      ${metric("Küche Zieltemperatur", kitchen.target_temperature, ZONES.kitchen.target)}
      ${metric("Globaler Apply Status", stateText(hass, ENTITIES.applyStatus), ENTITIES.applyStatus)}
      ${metric("Letzter Apply", stateText(hass, ENTITIES.lastApply), ENTITIES.lastApply)}
    </div>
    <div class="section notice">Bad Policy ist noch nicht implementiert. Bad-Entities im Config Flow sind aktuell Platzhalter für den nächsten PR.</div>
  `;
}

function renderContext(hass) {
  const ctx = contextSnapshot(hass);
  const labels = {
    activity_state: "Activity State",
    bio_state: "Bio State",
    day_context: "Day Context",
    day_state: "Day State",
    presence_band: "Presence Band",
    presence_household: "Presence Household",
    presence_personal: "Presence Personal",
    presence_preheat_active: "Presence Preheat Active",
    presence_transition: "Presence Transition",
    planned_wakeup_time: "Planned Wakeup Time",
  };
  const rows = Object.entries(labels).map(([key, label]) => {
    const item = ctx[key] || {};
    return `<tr>
      <td>${esc(label)}</td>
      <td class="mono">${esc(asText(item.value, "not exposed yet"))}</td>
      <td class="mono">${esc(asText(item.source_entity_id))}</td>
      <td>${statusChip(item.quality || "missing")}</td>
      <td>${esc(asText(item.fallback_used, "false"))}</td>
    </tr>`;
  }).join("");
  return `<div class="card"><h2>${icon("mdi:account-clock-outline")}Context Snapshot</h2><div class="table-wrap">
    <table><thead><tr><th>Wert</th><th>value</th><th>source_entity_id</th><th>quality</th><th>fallback_used</th></tr></thead><tbody>${rows}</tbody></table>
  </div></div>`;
}

function renderZones(hass) {
  const zoneCards = Object.entries(ZONES).map(([zone, meta]) => {
    const plan = zonePlan(hass, zone);
    return `<div class="card">
      <h2>${icon("mdi:home-thermometer-outline")}${esc(meta.label)}</h2>
      ${kv("climate mode", plan.profile)}
      ${kv("target temperature", plan.target_temperature)}
      ${kv("plan hash", plan.plan_hash, "mono")}
      ${kv("pending plan hash", plan.pending_plan_hash, "mono")}
      ${kv("last applied plan hash", plan.last_applied_plan_hash, "mono")}
      ${kv("apply blocked", plan.apply_blocked)}
      ${kv("policy reason", plan.reason ?? "missing")}
      ${kv("apply blocker", plan.apply_block_reason ?? plan.apply_reason)}
      ${kv("blocked_by", plan.blocked_by || [])}
      ${kv("decision_path", plan.decision_path || [])}
      ${kv("profile", plan.profile)}
      ${kv("raw target temperature", plan.raw_target_temperature)}
      ${kv("final target temperature", plan.final_target_temperature ?? plan.target_temperature)}
      ${kv("boost status", plan.is_boost_active ? "active" : "inactive")}
    </div>`;
  }).join("");
  return `<div class="grid cols-2">${zoneCards}</div>
    <div class="section notice">Bad: noch nicht implementiert, geplant für den nächsten PR.</div>`;
}

function renderThresholds(hass) {
  const data = thresholds(hass);
  const th = data.thresholds || {};
  const setpoints = data.setpoints || {};
  const hysteresis = data.hysteresis || {};
  const teffParams = data.effective_temperature_parameters || {};
  const cooldowns = data.apply_cooldowns || {};
  const sources = data.sources || {};
  const bandSources = sources.active_threshold_band || {};
  const setpointSources = sources.setpoints || {};
  const hysteresisSources = sources.hysteresis || {};
  const teffSources = sources.effective_temperature_parameters || {};
  const bands = data.threshold_bands || {};
  const bandRows = Object.entries(bands).map(([key, band]) => `<tr>
    <td class="mono">${esc(key)}</td>
    <td>${esc(asText((band.months || []).join(", ")))}</td>
    <td>${esc(asText(band.off_threshold))}<br><span class="muted">${esc(band.sources?.off_threshold || "default")}</span></td>
    <td>${esc(asText(band.comfort_disabled ? "disabled" : band.comfort_threshold))}<br><span class="muted">${esc(band.sources?.comfort_threshold || band.sources?.comfort_disabled || "default")}</span></td>
    <td>${esc(asText(band.boost_disabled ? "disabled" : band.boost_threshold))}<br><span class="muted">${esc(band.sources?.boost_threshold || band.sources?.boost_disabled || "default")}</span></td>
  </tr>`).join("");
  return `<div class="grid cols-3">
    ${metric("Aktueller Monat", data.month ?? "missing")}
    ${metric("Aktives Monatsband", data.active_month_band ?? "missing")}
    ${metric("Komfort strukturell deaktiviert", data.comfort_structurally_disabled ?? "missing")}
    ${metric("Boost strukturell deaktiviert", data.boost_structurally_disabled ?? "missing")}
  </div>
  <div class="section notice">Editierbar über Integrationsoptionen. Dieses Panel zeigt nur die aktuell aktiven gespeicherten Werte.</div>
  <div class="section grid cols-2">
    <div class="card">
      <h2>${icon("mdi:thermometer-chevron-down")}Schwellenwerte</h2>
      ${kvSource("Off-Grenze", th.off ?? "missing", bandSources.off_threshold)}
      ${kvSource("Komfort-Grenze", th.comfort ?? "disabled", bandSources.comfort_threshold || bandSources.comfort_disabled)}
      ${kvSource("Boost-Grenze", th.boost ?? "disabled", bandSources.boost_threshold || bandSources.boost_disabled)}
    </div>
    <div class="card">
      <h2>${icon("mdi:thermostat")}Setpoints</h2>
      ${kvSource("off", setpoints.off ?? "missing", setpointSources.off)}
      ${kvSource("spar", setpoints.spar ?? "missing", setpointSources.spar)}
      ${kvSource("komfort", setpoints.komfort ?? "missing", setpointSources.komfort)}
      ${kvSource("boost", setpoints.boost ?? "missing", setpointSources.boost)}
    </div>
    <div class="card">
      <h2>${icon("mdi:chart-bell-curve-cumulative")}Hysterese-Parameter</h2>
      ${Object.entries(hysteresis).map(([k, v]) => kvSource(k, v, hysteresisSources[k])).join("") || kv("hysteresis", "missing")}
    </div>
    <div class="card">
      <h2>${icon("mdi:tune")}Effective-Temperature-Parameter</h2>
      ${Object.entries(teffParams).map(([k, v]) => kvSource(k, v, teffSources[k])).join("") || kv("effective temperature parameters", "missing")}
    </div>
    <div class="card">
      <h2>${icon("mdi:timer-sand")}Apply-Cooldowns</h2>
      ${kv("cooldown_seconds", cooldowns.cooldown_seconds ?? "missing")}
      ${kv("startup_block_seconds", cooldowns.startup_block_seconds ?? "missing")}
      ${kv("startup_ready", cooldowns.startup_ready ?? "missing")}
      ${kv("last_apply_at", cooldowns.last_apply_at ?? {})}
    </div>
  </div>
  <div class="section card">
    <h2>${icon("mdi:calendar-range")}Monatsbänder</h2>
    <div class="table-wrap">
      <table><thead><tr><th>Band</th><th>Monate</th><th>Off</th><th>Komfort</th><th>Boost</th></tr></thead><tbody>
        ${bandRows || `<tr><td colspan="5" class="muted">missing</td></tr>`}
      </tbody></table>
    </div>
  </div>`;
}

function renderEffective(hass) {
  const br = effectiveBreakdown(hass);
  const inp = effectiveInputs(hass);
  const sourceEntities = inp.source_entities || {};
  return `<div class="grid cols-2">
    <div class="card">
      <h2>${icon("mdi:database-eye-outline")}Inputs</h2>
      ${kv("reale Außentemperatur", inp.real_temperature ?? br.real_temperature ?? "not exposed yet")}
      ${kv("gefühlte Außentemperatur", inp.feels_like_temperature ?? "not exposed yet")}
      ${kv("Wetterzustand", inp.weather_condition ?? "not exposed yet")}
      ${kv("Forecast +3h", inp.forecast_temperature ?? "not exposed yet")}
      ${kv("Lux", inp.outdoor_lux ?? "not exposed yet")}
      ${kv("Sun Elevation", inp.sun_elevation ?? "not exposed yet")}
    </div>
    <div class="card">
      <h2>${icon("mdi:thermometer-lines")}Breakdown</h2>
      ${kv("Floor Slab Offset", br.floor_slab_offset ?? "missing")}
      ${kv("Feels-Like Offset", br.feels_like_offset ?? "missing")}
      ${kv("Weather Offset", br.weather_offset ?? "missing")}
      ${kv("Forecast Offset", br.forecast_offset ?? "missing")}
      ${kv("Lux Bonus", br.lux_bonus ?? "missing")}
      ${kv("finale effektive Außentemperatur", br.effective_temperature ?? stateText(hass, ENTITIES.effectiveTemp))}
      ${kv("input quality", br.input_quality ?? "missing")}
    </div>
    <div class="card">
      <h2>${icon("mdi:link-variant")}Source Entities</h2>
      ${Object.entries(sourceEntities).map(([k, v]) => kv(k, v)).join("") || kv("sources", "not exposed yet")}
    </div>
  </div>`;
}

function actionButton(id, label, iconName, primary, available) {
  return `<button class="action ${primary ? "primary" : ""}" data-action="${esc(id)}" ${available ? "" : "disabled"} title="${available ? "" : "missing service/button"}">
    ${icon(iconName)}<span>${esc(available ? label : `${label}: missing service/button`)}</span>
  </button>`;
}

function renderApply(hass) {
  const applyNow = serviceAvailable(hass, "apply_now");
  const dryRun = serviceAvailable(hass, "dry_run");
  const payload = debugPayload(hass);
  const lastApply = payload.last_apply_result || attr(hass, ENTITIES.applyStatus, "result", null);
  return `<div class="grid cols-3">
    ${metric("Auto-Apply Toggle Zustand", stateText(hass, ENTITIES.applyActive), ENTITIES.applyActive)}
    ${metric("Auto-Apply Ready", stateText(hass, ENTITIES.applyReady), ENTITIES.applyReady)}
    ${metric("Manual Apply möglich", payload.manual_apply_possible ?? attr(hass, ENTITIES.applyStatus, "manual_apply_possible", "missing"))}
    ${metric("Apply Status", stateText(hass, ENTITIES.applyStatus), ENTITIES.applyStatus)}
    ${metric("Last Apply", stateText(hass, ENTITIES.lastApply), ENTITIES.lastApply)}
    ${metric("Dry Run verfügbar", dryRun ? "ja" : "missing service/button")}
  </div>
  <div class="section card">
    <h2>${icon("mdi:gesture-tap-button")}Actions</h2>
    <div class="actions">
      ${actionButton("dry-run-global", "Global Dry Run", "mdi:flask-outline", false, dryRun)}
      ${actionButton("apply-global", "Global Manual Apply", "mdi:play-outline", true, applyNow)}
      ${actionButton("apply-living_room", "Wohnzimmer Manual Apply", "mdi:sofa-outline", false, applyNow)}
      ${actionButton("apply-kitchen", "Küche Manual Apply", "mdi:silverware-fork-knife", false, applyNow)}
    </div>
  </div>
  <div class="section card">
    <h2>${icon("mdi:clipboard-pulse-outline")}Letzter Apply-Versuch</h2>
    ${jsonBlock(lastApply || "not run yet")}
  </div>
  <div class="section card">
    <h2>${icon("mdi:format-list-checks")}Geplante Dry-Run-Service-Calls</h2>
    ${jsonBlock((lastApply?.dry_run ? lastApply.actions : []).map((a) => ({
      zone: a.zone,
      reason: a.reason,
      target_entity_id: a.target_entity_id,
      service_calls: a.service_calls,
      details: a.details,
    })))}
  </div>`;
}

function renderInputs(hass) {
  const inputs = debugPayload(hass).inputs || attr(hass, ENTITIES.systemReady, "inputs", []) || [];
  const rows = inputs.map((item) => `<tr>
    <td>${esc(item.role || "other")}</td>
    <td class="mono">${esc(item.key || "")}</td>
    <td class="mono">${esc(asText(item.entity_id))}</td>
    <td class="mono">${esc(asText(item.state))}</td>
    <td>${statusChip(item.status || "missing")}</td>
    <td>${esc(item.source || "missing")}</td>
  </tr>`).join("");
  return `<div class="card"><h2>${icon("mdi:database-search-outline")}Configured Inputs</h2><div class="table-wrap">
    <table><thead><tr><th>Rolle</th><th>Key</th><th>Entity ID</th><th>State</th><th>Status</th><th>Quelle</th></tr></thead><tbody>
      ${rows || `<tr><td colspan="6" class="muted">not exposed yet</td></tr>`}
    </tbody></table>
  </div></div>`;
}

function renderDebug(hass) {
  const dbg = debugAttrs(hass);
  const payload = debugPayload(hass);
  const planMap = plans(hass);
  const paths = Object.entries(planMap).map(([zone, plan]) => ({
    zone,
    reason: plan.reason,
    apply_block_reason: plan.apply_block_reason,
    decision_path: plan.decision_path,
  }));
  const skipReason = payload.last_apply_result?.reason
    || attr(hass, ENTITIES.applyStatus, "reason", null)
    || Object.values(planMap).map((p) => p.apply_block_reason).filter(Boolean).join(", ")
    || "none";
  return `<div class="grid cols-2">
    <div class="card"><h2>${icon("mdi:routes")}Letzter Decision Path</h2>${jsonBlock(paths)}</div>
    <div class="card"><h2>${icon("mdi:tune-vertical-variant")}Thresholds</h2>${jsonBlock(thresholds(hass))}</div>
    <div class="card"><h2>${icon("mdi:account-clock-outline")}Letzter Context Snapshot</h2>${jsonBlock(contextSnapshot(hass))}</div>
    <div class="card"><h2>${icon("mdi:file-tree-outline")}Letzter Plan JSON</h2>${jsonBlock(planMap)}</div>
    <div class="card"><h2>${icon("mdi:clipboard-pulse-outline")}Letzter Apply-Versuch</h2>${jsonBlock(payload.last_apply_result || attr(hass, ENTITIES.applyStatus, "result", null))}</div>
    <div class="card"><h2>${icon("mdi:block-helper")}Letzter Skip-/Blockgrund</h2>${kv("reason", skipReason)}</div>
    <div class="card"><h2>${icon("mdi:fingerprint")}Hash-Basis</h2>${jsonBlock(Object.fromEntries(Object.entries(planMap).map(([zone, plan]) => [zone, {
      zone: plan.zone,
      profile: plan.profile,
      target_temperature: plan.target_temperature,
      blocked_by: plan.blocked_by,
      effective_outdoor_temperature: plan.effective_outdoor_temperature,
      plan_hash: plan.plan_hash,
    }])))}</div>
    <div class="card"><h2>${icon("mdi:code-json")}Debug Summary</h2>${jsonBlock(dbg)}</div>
  </div>`;
}

const RENDERERS = {
  overview: renderOverview,
  context: renderContext,
  zones: renderZones,
  thresholds: renderThresholds,
  effective: renderEffective,
  apply: renderApply,
  inputs: renderInputs,
  debug: renderDebug,
};

class BcpApp extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._view = "overview";
    this._timer = null;
  }

  set hass(value) {
    this._hass = value;
    this._scheduleRender();
  }

  get hass() {
    return this._hass;
  }

  connectedCallback() {
    this._render();
  }

  disconnectedCallback() {
    clearTimeout(this._timer);
  }

  _scheduleRender() {
    clearTimeout(this._timer);
    this._timer = setTimeout(() => this._render(), 120);
  }

  _render() {
    const nav = NAV.map(([id, label, iconName]) => `<button data-view="${id}" class="${id === this._view ? "active" : ""}">
      ${icon(iconName)}<span>${esc(label)}</span>
    </button>`).join("");
    const view = NAV.find(([id]) => id === this._view) || NAV[0];
    const renderer = RENDERERS[view[0]] || renderOverview;
    const hass = this._hass;
    const sys = stateText(hass, ENTITIES.systemReady);
    const apply = stateText(hass, ENTITIES.applyActive);
    const effective = stateText(hass, ENTITIES.effectiveTemp);
    let content;
    try {
      content = hass ? renderer(hass) : `<div class="notice">Home Assistant state wird geladen.</div>`;
    } catch (err) {
      content = `<div class="notice">Render-Fehler: ${esc(err.message || err)}</div>`;
    }

    this.shadowRoot.innerHTML = `<style>${CSS}</style>
      <div class="app">
        <aside class="sidebar">
          <div class="brand">${icon("mdi:thermostat")}<div><b>Benni Climate Policy</b><small>Read-only Diagnose</small></div></div>
          <nav class="nav">${nav}</nav>
          <div class="side-foot">Panel: /${esc("benni-climate-policy")}</div>
        </aside>
        <main class="main">
          <header class="head">
            <div><h1>${esc(view[1])}</h1><p>benni_climate_policy</p></div>
            <div class="chips">
              ${statusChip(sys, `Ready ${sys}`)}
              ${statusChip(apply, `Apply ${apply}`)}
              ${statusChip(effective === "missing" ? "missing" : "ok", `Teff ${effective}`)}
            </div>
          </header>
          <div id="content">${content}</div>
        </main>
      </div>`;
    this.shadowRoot.querySelectorAll("[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._view = btn.dataset.view;
        this._render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => this._handleAction(btn.dataset.action));
    });
  }

  async _handleAction(action) {
    if (!this._hass) return;
    try {
      if (action === "dry-run-global") {
        await this._hass.callService(DOMAIN, "dry_run", {});
      } else if (action === "apply-global") {
        await this._hass.callService(DOMAIN, "apply_now", {});
      } else if (action.startsWith("apply-")) {
        await this._hass.callService(DOMAIN, "apply_now", { zone: action.replace("apply-", "") });
      }
      this._toast("Service ausgelöst");
    } catch (err) {
      this._toast(`Fehler: ${err.message || err}`);
    }
  }

  _toast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    this.shadowRoot.appendChild(toast);
    setTimeout(() => toast.remove(), 2400);
  }
}

if (!customElements.get("bcp-app")) {
  customElements.define("bcp-app", BcpApp);
}
