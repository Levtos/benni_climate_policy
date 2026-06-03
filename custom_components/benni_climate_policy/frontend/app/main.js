const DOMAIN = "benni_climate_policy";

const ENTITIES = {
  systemReady: "binary_sensor.climate_system_ready",
  applyReady: "binary_sensor.climate_policy_apply_ready",
  applyActive: "switch.climate_policy_apply_active",
  effectiveTemp: "sensor.climate_effective_outdoor_temperature",
  forecastTemp3h: "sensor.climate_forecast_temperature_3h",
  outdoorFeelsLike: "sensor.climate_outdoor_feels_like_temperature",
  applyStatus: "sensor.climate_policy_apply_status",
  lastApply: "sensor.climate_policy_last_apply",
  debugSummary: "sensor.climate_debug_summary",
  bathroomFanMode: "sensor.bathroom_fan_mode",
  bathroomFanPlanHash: "sensor.bathroom_fan_plan_hash",
  bathroomFanBlocked: "binary_sensor.bathroom_fan_apply_blocked",
};
const DEBUG_API_PATH = `${DOMAIN}/debug`;
const DEBUG_REFRESH_MS = 60000;
const DEBUG_VIEWS = new Set(["context", "bathroom", "thresholds", "apply", "inputs", "debug"]);
const JSON_CACHE = new WeakMap();

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
  bathroom: {
    label: "Bad",
    mode: "sensor.bathroom_climate_mode",
    target: "sensor.bathroom_climate_target_temp",
    planHash: "sensor.bathroom_climate_plan_hash",
    pendingHash: "sensor.bathroom_climate_pending_plan_hash",
    lastAppliedHash: "sensor.bathroom_climate_last_applied_plan_hash",
    applyReason: "sensor.bathroom_climate_apply_reason",
    blocked: "binary_sensor.bathroom_climate_apply_blocked",
  },
};

const NAV = [
  ["overview", "Overview", "mdi:view-dashboard-outline"],
  ["context", "Context", "mdi:account-clock-outline"],
  ["zones", "Zones", "mdi:home-thermometer-outline"],
  ["bathroom", "Bathroom", "mdi:shower-head"],
  ["thresholds", "Tuning", "mdi:tune-vertical-variant"],
  ["effective", "Effective Temp", "mdi:thermometer-lines"],
  ["apply", "Apply", "mdi:play-circle-outline"],
  ["inputs", "Inputs", "mdi:database-search-outline"],
  ["debug", "Debug", "mdi:code-json"],
];

const THRESHOLD_BANDS = [
  ["winter", "Tiefwinter", "Dez-Jan-Feb"],
  ["late_winter", "Spätwinter", "März"],
  ["spring", "Frühling", "April"],
  ["late_spring", "Spätfrühling", "Mai"],
  ["summer", "Sommer", "Jun-Jul-Aug"],
  ["early_autumn", "Frühherbst", "September"],
  ["autumn", "Herbst", "Oktober"],
  ["late_autumn", "Spätherbst", "November"],
];

const TUNING_GROUPS = [
  ["setpoints", "Setpoints", "mdi:thermostat", [
    ["setpoint_off", "Off"],
    ["setpoint_spar", "Spar"],
    ["setpoint_komfort", "Komfort"],
    ["setpoint_boost", "Boost"],
  ]],
  ["effective", "Effektive Außentemperatur", "mdi:thermometer-lines", [
    ["floor_slab_tau", "Bodenplatten-Tau"],
    ["lux_bonus_max", "Maximaler Lux-Bonus"],
    ["lux_reference", "Lux-Referenz"],
    ["feels_like_damping", "Dämpfung gefühlte Temperatur"],
    ["forecast_weight", "Forecast-Gewichtung"],
  ]],
  ["boost", "Boost", "mdi:rocket-launch-outline", [
    ["boost_delta", "Boost-Delta"],
    ["boost_activation_delta", "Aktivierungsdelta zum Raum"],
  ]],
  ["apply", "Apply", "mdi:timer-sand", [
    ["apply_cooldown_seconds", "Apply-Cooldown"],
    ["startup_block_seconds", "Startup-Ruhezeit"],
  ]],
  ["bath", "Bad", "mdi:shower-head", [
    ["bath_setpoint_protection", "Schutz-Setpoint"],
    ["bath_setpoint_ground", "Grundwärme-Setpoint"],
    ["bath_setpoint_comfort", "Komfort-Setpoint"],
    ["bath_comfort_suppression_teff", "Komfort bis Teff"],
    ["bath_humidity_acute_threshold", "Akut-Luftfeuchte"],
    ["bath_humidity_end_threshold", "End-Luftfeuchte"],
    ["bath_dewpoint_acute_threshold", "Akut-Taupunkt"],
    ["bath_ah_delta_afterrun_on", "Nachlauf ab AH-Delta"],
    ["bath_ah_delta_afterrun_off", "Nachlauf Ende AH-Delta"],
    ["bath_ah_delta_stoss", "Stoßlüftung AH-Delta"],
    ["bath_fan_heat_coordination_delta", "Heiz-/Lüfter-Delta"],
    ["bath_fan_acute_max_minutes", "Akut max. Minuten"],
    ["bath_fan_afterrun_max_minutes", "Nachlauf max. Minuten"],
    ["bath_fan_stoss_interval_hours", "Stoßlüftung Intervall"],
    ["bath_fan_stoss_duration_minutes", "Stoßlüftung Dauer"],
  ]],
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
.pre { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--bcp-panel); border: 1px solid var(--bcp-line); border-radius: 8px; padding: 11px; max-height: 360px; min-height: 96px; overflow: auto; scrollbar-gutter: stable; contain: content; }
.json-details summary { cursor: pointer; color: var(--bcp-muted); font-size: 13px; margin-bottom: 8px; }
.apply-summary { min-width: 760px; }
.apply-summary td, .apply-summary th { vertical-align: middle; }
.actions { display: flex; flex-wrap: wrap; gap: 9px; }
button.action { display: inline-grid; grid-template-columns: 18px auto; gap: 7px; align-items: center; min-height: 36px; border: 1px solid var(--bcp-line);
  border-radius: 8px; background: var(--bcp-surface); color: var(--bcp-text); padding: 8px 11px; cursor: pointer; font: inherit; }
button.action:hover { border-color: var(--bcp-accent); }
button.action.primary { background: var(--bcp-accent); color: var(--text-primary-color, #fff); border-color: var(--bcp-accent); }
button.action[disabled] { opacity: .55; cursor: not-allowed; }
.tuning-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.matrix { min-width: 900px; }
.matrix input[type="number"] { width: 92px; }
.matrix td, .matrix th { vertical-align: middle; }
.field-row { display: grid; grid-template-columns: minmax(150px, 1fr) 132px 86px; gap: 9px; align-items: center; padding: 7px 0; border-bottom: 1px solid var(--bcp-line); }
.field-row:last-child { border-bottom: 0; }
.field-row.dirty, tr.dirty { background: color-mix(in srgb, var(--bcp-warn) 9%, transparent); }
.field-row input, .matrix input { min-height: 32px; border: 1px solid var(--bcp-line); border-radius: 6px; padding: 5px 7px; background: var(--bcp-surface); color: var(--bcp-text); font: inherit; }
.field-row input:disabled, .matrix input:disabled { opacity: .55; background: var(--bcp-panel); }
.source-pill { display: inline-flex; align-items: center; border: 1px solid var(--bcp-line); border-radius: 999px; padding: 2px 7px; font-size: 11px; color: var(--bcp-muted); white-space: nowrap; }
.source-pill.user { color: var(--bcp-info); border-color: color-mix(in srgb, var(--bcp-info) 35%, var(--bcp-line)); }
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.error-box { border: 1px solid color-mix(in srgb, var(--bcp-error) 45%, var(--bcp-line)); background: color-mix(in srgb, var(--bcp-error) 9%, var(--bcp-surface)); color: var(--bcp-error); border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
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
  .cols-2, .cols-3, .cols-4, .tuning-grid { grid-template-columns: 1fr; }
  .kv { grid-template-columns: 1fr; gap: 3px; }
  .field-row { grid-template-columns: 1fr; }
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

function endpointDebug(app) {
  return app?._debugPayload || {};
}

function debugPayload(hass, app) {
  return endpointDebug(app).debug || {};
}

function plans(hass, app) {
  return endpointDebug(app).plans || {};
}

function contextSnapshot(hass, app) {
  return endpointDebug(app).context || {};
}

function effectiveBreakdown(hass, app) {
  const fromDebug = endpointDebug(app).effective_outdoor_temperature || {};
  const fromSensor = (stateObj(hass, ENTITIES.effectiveTemp) || {}).attributes || {};
  return { ...fromDebug, ...fromSensor };
}

function effectiveInputs(hass, app) {
  const fromDebug = endpointDebug(app).effective_inputs || debugPayload(hass, app).effective_inputs || {};
  const fromSensor = attr(hass, ENTITIES.effectiveTemp, "inputs", {}) || {};
  return { ...fromDebug, ...fromSensor };
}

function thresholds(hass, app) {
  return endpointDebug(app).thresholds || debugPayload(hass, app).thresholds || {};
}

function tuningOptions(hass, app) {
  return endpointDebug(app).tuning_options || debugPayload(hass, app).tuning_options || {};
}

function bathroomDebug(hass, app) {
  return endpointDebug(app).bathroom || debugPayload(hass, app).bathroom || {};
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
  const normalized = value ?? null;
  if (normalized && typeof normalized === "object") {
    const cached = JSON_CACHE.get(normalized);
    if (cached !== undefined) return `<div class="pre mono">${cached}</div>`;
    const text = esc(JSON.stringify(normalized, null, 2));
    JSON_CACHE.set(normalized, text);
    return `<div class="pre mono">${text}</div>`;
  }
  return `<div class="pre mono">${esc(JSON.stringify(normalized, null, 2))}</div>`;
}

function jsonDetails(summary, value) {
  return `<details class="json-details"><summary>${esc(summary)}</summary>${jsonBlock(value)}</details>`;
}

function plannedFromCalls(action, key) {
  const calls = Array.isArray(action?.service_calls) ? action.service_calls : [];
  for (const call of calls) {
    const data = call.service_data || {};
    if (key === "planned_hvac_mode" && call.service === "set_hvac_mode") return data.hvac_mode;
    if (key === "planned_temperature" && call.service === "set_temperature") return data.temperature;
  }
  return action?.details?.[key] ?? null;
}

function startupBlockNotice(actions) {
  return actions.some((action) => action?.details?.gate_reason === "startup_quiet_period")
    ? `<div class="notice">Blockiert durch Start-Ruhephase</div>`
    : "";
}

function renderApplySummary(lastApply) {
  const actions = Array.isArray(lastApply?.actions) ? lastApply.actions : [];
  if (!actions.length) return `<div class="notice">Noch kein Apply- oder Dry-Run-Ergebnis vorhanden.</div>`;
  const rows = actions.map((action) => {
    const gateReason = action.details?.gate_reason || action.details?.gate_status || "none";
    return `<tr>
      <td class="mono">${esc(action.zone)}</td>
      <td>${statusChip(action.status)}</td>
      <td class="mono">${esc(action.reason || "missing")}</td>
      <td class="mono">${esc(gateReason)}</td>
      <td class="mono">${esc(action.target_entity_id || "missing")}</td>
      <td class="mono">${esc(asText(plannedFromCalls(action, "planned_hvac_mode"), "none"))}</td>
      <td class="mono">${esc(asText(plannedFromCalls(action, "planned_temperature"), "none"))}</td>
    </tr>`;
  }).join("");
  return `${startupBlockNotice(actions)}<div class="table-wrap"><table class="apply-summary">
    <thead><tr><th>Zone</th><th>Status</th><th>Reason</th><th>Gate</th><th>Target Entity</th><th>HVAC Mode</th><th>Temperatur</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function debugEndpointNotice(app) {
  const message = app?._debugError
    ? `Debug-Endpunkt nicht erreichbar: ${app._debugError}`
    : "Debug-Daten werden geladen oder sind noch nicht verfügbar.";
  return `<div class="notice">${esc(message)}</div>`;
}

function serviceAvailable(hass, service) {
  return Boolean(hass && hass.services && hass.services[DOMAIN] && hass.services[DOMAIN][service]);
}

function entityAvailable(hass, entityId) {
  return Boolean(stateObj(hass, entityId));
}

function zonePlan(hass, zone, app) {
  const plan = plans(hass, app)[zone] || {};
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

function renderOverview(hass, app) {
  const living = zonePlan(hass, "living_room", app);
  const kitchen = zonePlan(hass, "kitchen", app);
  const bathroom = zonePlan(hass, "bathroom", app);
  const bath = bathroomDebug(hass, app);
  const fan = bath.fan_plan || {};
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
      ${metric("Bad Mode", bathroom.profile, ZONES.bathroom.mode)}
      ${metric("Bad Zieltemperatur", bathroom.target_temperature, ZONES.bathroom.target)}
      ${metric("Bad Lüfter Mode", fan.mode ?? stateText(hass, ENTITIES.bathroomFanMode), ENTITIES.bathroomFanMode)}
      ${metric("Globaler Apply Status", stateText(hass, ENTITIES.applyStatus), ENTITIES.applyStatus)}
      ${metric("Letzter Apply", stateText(hass, ENTITIES.lastApply), ENTITIES.lastApply)}
    </div>
  `;
}

function renderContext(hass, app) {
  const ctx = contextSnapshot(hass, app);
  if (!Object.keys(ctx).length) {
    return debugEndpointNotice(app);
  }
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

function renderZones(hass, app) {
  const zoneCards = Object.entries(ZONES).map(([zone, meta]) => {
    const plan = zonePlan(hass, zone, app);
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
  return `<div class="grid cols-2">${zoneCards}</div>`;
}

function renderBathroom(hass, app) {
  const bath = bathroomDebug(hass, app);
  const climate = bath.climate_plan || zonePlan(hass, "bathroom", app);
  const fan = bath.fan_plan || {};
  const diag = fan.diagnostics || {};
  const tuning = bath.tuning || {};
  return `<div class="grid cols-4">
    ${metric("Bad Climate Mode", climate.profile ?? "missing", ZONES.bathroom.mode)}
    ${metric("Bad Zieltemperatur", climate.target_temperature ?? "missing", ZONES.bathroom.target)}
    ${metric("Bad Lüfter Mode", fan.mode ?? stateText(hass, ENTITIES.bathroomFanMode), ENTITIES.bathroomFanMode)}
    ${metric("Bad Lüfter Zielzustand", fan.target_switch_state ?? "missing")}
    ${metric("Taupunkt Bad", diag.dewpoint ?? "missing")}
    ${metric("AH Bad", diag.absolute_humidity_bathroom ?? "missing")}
    ${metric("AH Wohnzimmer", diag.absolute_humidity_living ?? "missing")}
    ${metric("AH Delta", diag.ah_delta ?? "missing")}
  </div>
  <div class="section grid cols-2">
    <div class="card">
      <h2>${icon("mdi:radiator")}Bad Heizung</h2>
      ${kv("policy reason", climate.reason ?? "missing")}
      ${kv("apply blocker", climate.apply_block_reason ?? "missing")}
      ${kv("blocked_by", climate.blocked_by || [])}
      ${kv("effective outdoor temperature", climate.effective_outdoor_temperature ?? "missing")}
      ${kv("plan hash", climate.plan_hash ?? "missing", "mono")}
      ${kv("policy config hash", climate.policy_config_hash ?? "missing", "mono")}
      ${kv("decision path", climate.decision_path || [])}
    </div>
    <div class="card">
      <h2>${icon("mdi:fan")}Bad Lüfter</h2>
      ${kv("fan reason", fan.fan_reason ?? fan.reason ?? "missing")}
      ${kv("fan blocker", fan.fan_blocker ?? fan.apply_block_reason ?? "missing")}
      ${kv("apply blocker", fan.apply_block_reason ?? "missing")}
      ${kv("heating fan coordination", diag.heating_fan_coordination_state ?? "missing")}
      ${kv("max durations", diag.max_duration_minutes ?? {})}
      ${kv("last fan active at", diag.last_fan_active_at ?? "not_available")}
      ${kv("plan hash", fan.plan_hash ?? stateText(hass, ENTITIES.bathroomFanPlanHash), "mono")}
    </div>
    <div class="card">
      <h2>${icon("mdi:water-percent")}Feuchte-Diagnose</h2>
      ${kv("bathroom humidity", diag.bathroom_humidity ?? "see input sensor")}
      ${kv("dewpoint", diag.dewpoint ?? "missing")}
      ${kv("absolute_humidity_bathroom", diag.absolute_humidity_bathroom ?? "missing")}
      ${kv("absolute_humidity_living", diag.absolute_humidity_living ?? "missing")}
      ${kv("ah_delta", diag.ah_delta ?? "missing")}
      ${kv("input quality", diag.input_quality ?? "missing")}
    </div>
    <div class="card">
      <h2>${icon("mdi:tune")}Aktive Bad-Parameter</h2>
      ${Object.entries(tuning).filter(([k]) => k !== "sources").map(([k, v]) => kvSource(k, v, tuning.sources?.[`bath_${k}`] || tuning.sources?.[k])).join("") || kv("tuning", "missing")}
    </div>
  </div>`;
}

function sourcePill(source) {
  const cls = source === "user option" ? "source-pill user" : "source-pill";
  return `<span class="${cls}">${esc(source || "default")}</span>`;
}

function tuningDraftValue(app, data, key) {
  if (app && app._tuningDraft && Object.prototype.hasOwnProperty.call(app._tuningDraft, key)) {
    return app._tuningDraft[key];
  }
  return data.values?.[key];
}

function isDirty(app, data, key) {
  if (!app || !app._tuningDraft || !Object.prototype.hasOwnProperty.call(app._tuningDraft, key)) return false;
  return String(app._tuningDraft[key] ?? "") !== String(data.values?.[key] ?? "");
}

function numberInput(app, data, key, disabled = false) {
  const value = tuningDraftValue(app, data, key);
  return `<input type="number" step="0.1" data-tuning-key="${esc(key)}" value="${esc(value ?? "")}" ${disabled ? "disabled" : ""}>`;
}

function boolInput(app, data, key) {
  const checked = tuningDraftValue(app, data, key) === true || tuningDraftValue(app, data, key) === "true";
  return `<input type="checkbox" data-tuning-key="${esc(key)}" ${checked ? "checked" : ""}>`;
}

function fieldRows(app, data, fields) {
  return fields.map(([key, label]) => {
    const dirty = isDirty(app, data, key);
    return `<div class="field-row ${dirty ? "dirty" : ""}">
      <div><b>${esc(label)}</b><br><span class="mono muted">${esc(key)}</span></div>
      ${numberInput(app, data, key)}
      ${sourcePill(data.sources?.[key])}
    </div>`;
  }).join("");
}

function renderThresholds(hass, app) {
  const data = tuningOptions(hass, app);
  const current = thresholds(hass, app);
  if (!data.values) {
    return debugEndpointNotice(app);
  }
  app?._ensureTuningDraft(data);
  const updateAvailable = serviceAvailable(hass, "update_options");
  const resetAvailable = serviceAvailable(hass, "reset_options");
  const dirtyKeys = app?._dirtyTuningKeys(data) || [];
  const error = app?._tuningError || "";
  const matrixRows = THRESHOLD_BANDS.map(([band, label, months]) => {
    const bandData = data.threshold_bands?.[band] || {};
    const keys = bandData.keys || {};
    const comfortDisabled = tuningDraftValue(app, data, keys.comfort_disabled) === true || tuningDraftValue(app, data, keys.comfort_disabled) === "true";
    const boostDisabled = tuningDraftValue(app, data, keys.boost_disabled) === true || tuningDraftValue(app, data, keys.boost_disabled) === "true";
    const rowDirty = Object.values(keys).some((key) => isDirty(app, data, key));
    return `<tr class="${rowDirty ? "dirty" : ""}">
      <td><b>${esc(label)}</b><br><span class="mono muted">${esc(band)}</span></td>
      <td>${esc(months)}</td>
      <td>${numberInput(app, data, keys.off_threshold)}<br>${sourcePill(data.sources?.[keys.off_threshold])}</td>
      <td>${numberInput(app, data, keys.comfort_threshold, comfortDisabled)}<br>${sourcePill(data.sources?.[keys.comfort_threshold])}</td>
      <td>${numberInput(app, data, keys.boost_threshold, boostDisabled)}<br>${sourcePill(data.sources?.[keys.boost_threshold])}</td>
      <td>${boolInput(app, data, keys.comfort_disabled)}<br>${sourcePill(data.sources?.[keys.comfort_disabled])}</td>
      <td>${boolInput(app, data, keys.boost_disabled)}<br>${sourcePill(data.sources?.[keys.boost_disabled])}</td>
      <td><button class="action" data-action="tuning-reset-band-${esc(band)}" ${resetAvailable ? "" : "disabled"}>${icon("mdi:restore")}<span>Zurücksetzen</span></button></td>
    </tr>`;
  }).join("");
  const cards = TUNING_GROUPS.map(([section, title, iconName, fields]) => `<div class="card">
    <div class="toolbar">
      <h2>${icon(iconName)}${esc(title)}</h2>
      <button class="action" data-action="tuning-reset-section-${esc(section)}" ${resetAvailable ? "" : "disabled"}>${icon("mdi:restore")}<span>Zurücksetzen</span></button>
    </div>
    ${fieldRows(app, data, fields)}
  </div>`).join("");
  return `${error ? `<div class="error-box">${esc(error)}</div>` : ""}
  <div class="toolbar">
    <div>
      <b>Klima-Tuning</b><br>
      <span class="muted">Gespeichert wird in den Integrationsoptionen. Ungespeicherte Änderungen sind markiert.</span>
    </div>
    <div class="actions">
      ${actionButton("tuning-reset-all", "Alles zurücksetzen", "mdi:restore", false, resetAvailable)}
      <button class="action primary" data-action="tuning-save" ${updateAvailable && dirtyKeys.length > 0 ? "" : "disabled"}>${icon("mdi:content-save-outline")}<span>${esc(dirtyKeys.length ? `Speichern (${dirtyKeys.length})` : "Speichern")}</span></button>
    </div>
  </div>
  <div class="grid cols-4">
    ${metric("Aktueller Monat", current.month ?? "missing")}
    ${metric("Aktives Monatsband", current.active_month_band ?? "missing")}
    ${metric("Komfort deaktiviert", current.comfort_structurally_disabled ?? "missing")}
    ${metric("Boost deaktiviert", current.boost_structurally_disabled ?? "missing")}
  </div>
  <div class="section card">
    <h2>${icon("mdi:calendar-range")}Monats-/Saison-Matrix</h2>
    <div class="table-wrap">
      <table class="matrix"><thead><tr><th>Band</th><th>Monate</th><th>off_threshold</th><th>comfort_threshold</th><th>boost_threshold</th><th>comfort_disabled</th><th>boost_disabled</th><th>Reset</th></tr></thead><tbody>
        ${matrixRows}
      </tbody></table>
    </div>
  </div>
  <div class="section tuning-grid">${cards}</div>`;
}

function renderEffective(hass, app) {
  const br = effectiveBreakdown(hass, app);
  const inp = effectiveInputs(hass, app);
  const sourceEntities = inp.source_entities || {};
  const weatherResolution = inp.weather_resolution || {};
  const forecastResolution = inp.forecast_resolution || weatherResolution.forecast || {};
  const feelsLikeResolution = inp.feels_like_resolution || weatherResolution.feels_like || {};
  return `<div class="grid cols-2">
    <div class="card">
      <h2>${icon("mdi:database-eye-outline")}Inputs</h2>
      ${kv("reale Außentemperatur", inp.real_temperature ?? br.real_temperature ?? "not exposed yet")}
      ${metric("gefühlte Außentemperatur", stateText(hass, ENTITIES.outdoorFeelsLike), ENTITIES.outdoorFeelsLike)}
      ${kv("Wetterzustand", inp.weather_condition ?? "not exposed yet")}
      ${metric("Forecast +3h", stateText(hass, ENTITIES.forecastTemp3h), ENTITIES.forecastTemp3h)}
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
    <div class="card">
      <h2>${icon("mdi:weather-partly-cloudy")}Weather Resolver</h2>
      ${kv("Forecast +3h Wert", forecastResolution.value ?? inp.forecast_temperature ?? "missing")}
      ${kv("Forecast Quelle", forecastResolution.source ?? "missing")}
      ${kv("Forecast Qualität", forecastResolution.quality ?? "missing")}
      ${kv("Weather Entity", forecastResolution.weather_entity ?? sourceEntities.weather_entity ?? "missing")}
      ${kv("Zielzeit now +3h", forecastResolution.target_time ?? "missing")}
      ${kv("Forecast Zeitpunkt", forecastResolution.forecast_datetime ?? "missing")}
      ${kv("Forecast Reason", forecastResolution.reason ?? "missing")}
      ${kv("Forecast Fallback", forecastResolution.fallback_used ?? false)}
      ${kv("Feels-like Wert", feelsLikeResolution.value ?? inp.feels_like_temperature ?? "missing")}
      ${kv("Feels-like Quelle", feelsLikeResolution.source ?? "missing")}
      ${kv("Feels-like Qualität", feelsLikeResolution.quality ?? "missing")}
      ${kv("Feels-like Reason", feelsLikeResolution.reason ?? "missing")}
      ${kv("Feels-like Fallback", feelsLikeResolution.fallback_used ?? false)}
    </div>
  </div>`;
}

function actionButton(id, label, iconName, primary, available) {
  return `<button class="action ${primary ? "primary" : ""}" data-action="${esc(id)}" ${available ? "" : "disabled"} title="${available ? "" : "missing service/button"}">
    ${icon(iconName)}<span>${esc(available ? label : `${label}: missing service/button`)}</span>
  </button>`;
}

function renderApply(hass, app) {
  const applyNow = serviceAvailable(hass, "apply_now");
  const dryRun = serviceAvailable(hass, "dry_run");
  const payload = debugPayload(hass, app);
  const lastApply = endpointDebug(app).last_apply_result || payload.last_apply_result || null;
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
      ${actionButton("dry-run-bathroom", "Bad Dry Run", "mdi:flask-outline", false, dryRun)}
      ${actionButton("apply-bathroom", "Bad Manual Apply", "mdi:shower-head", false, applyNow)}
      ${actionButton("dry-run-bathroom_fan", "Bad Lüfter Dry Run", "mdi:fan-alert", false, dryRun)}
      ${actionButton("apply-bathroom_fan", "Bad Lüfter Apply", "mdi:fan", false, applyNow)}
    </div>
  </div>
  <div class="section card">
    <h2>${icon("mdi:clipboard-pulse-outline")}Letzter Apply-Versuch</h2>
    ${renderApplySummary(lastApply)}
    ${lastApply ? jsonDetails("Details als JSON anzeigen", lastApply) : ""}
  </div>
  <div class="section card">
    <h2>${icon("mdi:format-list-checks")}Geplante Dry-Run-Service-Calls</h2>
    ${lastApply?.dry_run ? renderApplySummary(lastApply) : `<div class="notice">Kein Dry Run aktiv oder noch nicht ausgefuehrt.</div>`}
    ${lastApply?.dry_run ? jsonDetails("Dry-Run-Service-Calls als JSON anzeigen", lastApply.actions.map((a) => ({
      zone: a.zone,
      reason: a.reason,
      target_entity_id: a.target_entity_id,
      service_calls: a.service_calls,
      details: a.details,
    }))) : ""}
  </div>`;
}

function renderInputs(hass, app) {
  const inputs = endpointDebug(app).inputs || debugPayload(hass, app).inputs || [];
  if (!inputs.length) {
    return debugEndpointNotice(app);
  }
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

function renderDebug(hass, app) {
  const dbg = debugAttrs(hass);
  const payload = debugPayload(hass, app);
  const full = endpointDebug(app);
  const planMap = plans(hass, app);
  if (!Object.keys(full).length) {
    return debugEndpointNotice(app);
  }
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
    <div class="card"><h2>${icon("mdi:speedometer")}Performance</h2>
      ${Object.entries(full.performance || payload.performance || {}).map(([k, v]) => kv(k, v, "mono")).join("") || kv("performance", "not exposed yet")}
      ${kv("debug_endpoint_last_fetch", app?._debugLastFetch ? new Date(app._debugLastFetch).toISOString() : "never", "mono")}
    </div>
    <div class="card"><h2>${icon("mdi:routes")}Letzter Decision Path</h2>${jsonDetails("Decision Path als JSON anzeigen", paths)}</div>
    <div class="card"><h2>${icon("mdi:tune-vertical-variant")}Thresholds</h2>${jsonDetails("Thresholds als JSON anzeigen", thresholds(hass, app))}</div>
    <div class="card"><h2>${icon("mdi:account-clock-outline")}Letzter Context Snapshot</h2>${jsonDetails("Context als JSON anzeigen", contextSnapshot(hass, app))}</div>
    <div class="card"><h2>${icon("mdi:file-tree-outline")}Letzter Plan JSON</h2>${jsonDetails("Plaene als JSON anzeigen", planMap)}</div>
    <div class="card"><h2>${icon("mdi:clipboard-pulse-outline")}Letzter Apply-Versuch</h2>${renderApplySummary(payload.last_apply_result)}${jsonDetails("Apply-Versuch als JSON anzeigen", payload.last_apply_result || attr(hass, ENTITIES.applyStatus, "result", null))}</div>
    <div class="card"><h2>${icon("mdi:block-helper")}Letzter Skip-/Blockgrund</h2>${kv("reason", skipReason)}</div>
    <div class="card"><h2>${icon("mdi:fingerprint")}Hash-Basis</h2>${jsonDetails("Hash-Basis als JSON anzeigen", Object.fromEntries(Object.entries(planMap).map(([zone, plan]) => [zone, {
      zone: plan.zone,
      profile: plan.profile,
      target_temperature: plan.target_temperature,
      blocked_by: plan.blocked_by,
      effective_outdoor_temperature: plan.effective_outdoor_temperature,
      plan_hash: plan.plan_hash,
    }])))}</div>
    <div class="card"><h2>${icon("mdi:code-json")}Debug Summary</h2>${jsonDetails("Recorder-sichere Attribute anzeigen", dbg)}</div>
  </div>`;
}

const RENDERERS = {
  overview: renderOverview,
  context: renderContext,
  zones: renderZones,
  bathroom: renderBathroom,
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
    this._tuningDraft = null;
    this._tuningBase = null;
    this._tuningError = "";
    this._debugPayload = null;
    this._debugError = "";
    this._debugFetchInFlight = false;
    this._debugLastFetch = 0;
    this._lastHtml = "";
  }

  set hass(value) {
    this._hass = value;
    this._ensureDebugFetch();
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

  _ensureDebugFetch(force = false) {
    if (!this._hass || !this._hass.callApi || this._debugFetchInFlight) return;
    if (!force && !this._viewNeedsDebug()) return;
    const now = Date.now();
    if (!force && this._debugLastFetch && now - this._debugLastFetch < DEBUG_REFRESH_MS) return;
    this._fetchDebugPayload(force);
  }

  async _fetchDebugPayload(force = false) {
    if (!this._hass || !this._hass.callApi || this._debugFetchInFlight) return;
    if (!force && !this._viewNeedsDebug()) return;
    const now = Date.now();
    if (!force && this._debugLastFetch && now - this._debugLastFetch < DEBUG_REFRESH_MS) return;
    this._debugFetchInFlight = true;
    this._debugLastFetch = now;
    try {
      this._debugPayload = await this._hass.callApi("GET", DEBUG_API_PATH);
      this._debugError = "";
    } catch (err) {
      this._debugError = err.message || String(err);
    } finally {
      this._debugFetchInFlight = false;
      this._scheduleRender();
    }
  }

  _render() {
    const nav = NAV.map(([id, label, iconName]) => `<button data-view="${id}" class="${id === this._view ? "active" : ""}">
      ${icon(iconName)}<span>${esc(label)}</span>
    </button>`).join("");
    const view = NAV.find(([id]) => id === this._view) || NAV[0];
    const renderer = RENDERERS[view[0]] || renderOverview;
    const hass = this._hass;
    if (hass && this._viewNeedsDebug() && !this._debugPayload && !this._debugFetchInFlight) {
      this._ensureDebugFetch();
    }
    const sys = stateText(hass, ENTITIES.systemReady);
    const apply = stateText(hass, ENTITIES.applyActive);
    const effective = stateText(hass, ENTITIES.effectiveTemp);
    let content;
    try {
      content = hass ? renderer(hass, this) : `<div class="notice">Home Assistant state wird geladen.</div>`;
    } catch (err) {
      content = `<div class="notice">Render-Fehler: ${esc(err.message || err)}</div>`;
    }

    const html = `<style>${CSS}</style>
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
    if (this._lastHtml === html) return;
    this._lastHtml = html;
    this.shadowRoot.innerHTML = html;
    this.shadowRoot.querySelectorAll("[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._view = btn.dataset.view;
        this._ensureDebugFetch();
        this._render();
      });
    });
    this.shadowRoot.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => this._handleAction(btn.dataset.action));
    });
    this.shadowRoot.querySelectorAll("[data-tuning-key]").forEach((input) => {
      input.addEventListener("input", () => this._handleTuningInput(input));
      input.addEventListener("change", () => this._handleTuningInput(input));
    });
  }

  _viewNeedsDebug() {
    return DEBUG_VIEWS.has(this._view);
  }

  _ensureTuningDraft(data) {
    const values = data.values || {};
    const signature = JSON.stringify(values);
    if (!this._tuningDraft || this._tuningBaseSignature !== signature) {
      this._tuningDraft = { ...values };
      this._tuningBase = { ...values };
      this._tuningBaseSignature = signature;
      this._tuningError = "";
    }
  }

  _dirtyTuningKeys(data) {
    const values = data.values || {};
    const draft = this._tuningDraft || values;
    return Object.keys(draft).filter((key) => String(draft[key] ?? "") !== String(values[key] ?? ""));
  }

  _handleTuningInput(input) {
    if (!this._tuningDraft) return;
    const key = input.dataset.tuningKey;
    this._tuningDraft[key] = input.type === "checkbox" ? input.checked : input.value;
    this._tuningError = "";
    this._scheduleRender();
  }

  _thresholdKey(band, field) {
    return `threshold_${band}_${field}`;
  }

  _validateNumber(key, value, { min = null, max = null, integer = false } = {}) {
    if (value === "" || value === null || value === undefined) {
      throw new Error(`${key} darf nicht leer sein`);
    }
    const number = Number(value);
    if (!Number.isFinite(number)) throw new Error(`${key} muss eine Zahl sein`);
    if (integer && !Number.isInteger(number)) throw new Error(`${key} muss eine ganze Zahl sein`);
    if (min !== null && number < min) throw new Error(`${key} muss >= ${min} sein`);
    if (max !== null && number > max) throw new Error(`${key} muss <= ${max} sein`);
    return integer ? Math.trunc(number) : number;
  }

  _validateTuningDraft(data) {
    const draft = this._tuningDraft || {};
    const payload = {};
    const dirty = this._dirtyTuningKeys(data);
    const intKeys = new Set([
      "apply_cooldown_seconds",
      "startup_block_seconds",
      "bath_fan_acute_max_minutes",
      "bath_fan_afterrun_max_minutes",
      "bath_fan_stoss_interval_hours",
      "bath_fan_stoss_duration_minutes",
    ]);
    const weightKeys = new Set(["feels_like_damping", "forecast_weight"]);
    dirty.forEach((key) => {
      if (key.endsWith("_disabled")) {
        payload[key] = draft[key] === true || draft[key] === "true";
      } else if (key === "lux_reference") {
        payload[key] = this._validateNumber(key, draft[key], { min: 1 });
      } else if (weightKeys.has(key)) {
        payload[key] = this._validateNumber(key, draft[key], { min: 0, max: 1 });
      } else if (intKeys.has(key)) {
        payload[key] = this._validateNumber(key, draft[key], { min: 1, integer: true });
      } else if (key.endsWith("_threshold") || key.startsWith("setpoint_") || key.startsWith("bath_setpoint_")) {
        payload[key] = this._validateNumber(key, draft[key], { min: 0, max: 35 });
      } else {
        payload[key] = this._validateNumber(key, draft[key]);
      }
    });
    THRESHOLD_BANDS.forEach(([band]) => {
      const off = this._validateNumber(this._thresholdKey(band, "off_threshold"), draft[this._thresholdKey(band, "off_threshold")], { min: 0, max: 35 });
      const comfortDisabled = draft[this._thresholdKey(band, "comfort_disabled")] === true || draft[this._thresholdKey(band, "comfort_disabled")] === "true";
      const boostDisabled = draft[this._thresholdKey(band, "boost_disabled")] === true || draft[this._thresholdKey(band, "boost_disabled")] === "true";
      const comfortRaw = draft[this._thresholdKey(band, "comfort_threshold")];
      const boostRaw = draft[this._thresholdKey(band, "boost_threshold")];
      const comfort = comfortDisabled && comfortRaw === "" ? null : this._validateNumber(this._thresholdKey(band, "comfort_threshold"), comfortRaw, { min: 0, max: 35 });
      const boost = boostDisabled && boostRaw === "" ? null : this._validateNumber(this._thresholdKey(band, "boost_threshold"), boostRaw, { min: 0, max: 35 });
      if (!comfortDisabled && comfort > off) throw new Error(`${band}: comfort_threshold darf nicht über off_threshold liegen`);
      if (!boostDisabled && comfortDisabled) throw new Error(`${band}: boost_threshold kann nicht aktiv sein, wenn comfort deaktiviert ist`);
      if (!boostDisabled && boost > comfort) throw new Error(`${band}: boost_threshold darf nicht über comfort_threshold liegen`);
    });
    return payload;
  }

  async _handleAction(action) {
    if (!this._hass) return;
    try {
      if (action === "dry-run-global") {
        await this._hass.callService(DOMAIN, "dry_run", {});
        await this._fetchDebugPayload(true);
      } else if (action === "apply-global") {
        await this._hass.callService(DOMAIN, "apply_now", {});
        await this._fetchDebugPayload(true);
      } else if (action === "tuning-save") {
        const payload = this._validateTuningDraft(tuningOptions(this._hass, this));
        if (!Object.keys(payload).length) {
          this._toast("Keine Änderungen");
          return;
        }
        await this._hass.callService(DOMAIN, "update_options", { options: payload });
        await this._fetchDebugPayload(true);
        this._tuningDraft = null;
        this._tuningBase = null;
        this._toast("Tuning gespeichert");
      } else if (action === "tuning-reset-all") {
        const data = tuningOptions(this._hass, this);
        const keys = Object.values(data.sections || {}).flat();
        await this._hass.callService(DOMAIN, "reset_options", { keys });
        await this._fetchDebugPayload(true);
        this._tuningDraft = null;
        this._tuningBase = null;
        this._toast("Tuning zurückgesetzt");
      } else if (action.startsWith("tuning-reset-section-")) {
        const section = action.replace("tuning-reset-section-", "");
        const keys = (tuningOptions(this._hass, this).sections || {})[section] || [];
        await this._hass.callService(DOMAIN, "reset_options", { keys });
        await this._fetchDebugPayload(true);
        this._tuningDraft = null;
        this._tuningBase = null;
        this._toast("Abschnitt zurückgesetzt");
      } else if (action.startsWith("tuning-reset-band-")) {
        const band = action.replace("tuning-reset-band-", "");
        const bandData = (tuningOptions(this._hass, this).threshold_bands || {})[band] || {};
        const keys = Object.values(bandData.keys || {});
        await this._hass.callService(DOMAIN, "reset_options", { keys });
        await this._fetchDebugPayload(true);
        this._tuningDraft = null;
        this._tuningBase = null;
        this._toast("Band zurückgesetzt");
      } else if (action.startsWith("dry-run-")) {
        await this._hass.callService(DOMAIN, "dry_run", { zone: action.replace("dry-run-", "") });
        await this._fetchDebugPayload(true);
      } else if (action.startsWith("apply-")) {
        await this._hass.callService(DOMAIN, "apply_now", { zone: action.replace("apply-", "") });
        await this._fetchDebugPayload(true);
      }
      if (!action.startsWith("tuning-")) this._toast("Service ausgelöst");
    } catch (err) {
      this._tuningError = err.message || String(err);
      this._scheduleRender();
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
