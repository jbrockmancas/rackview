<script setup>
import { computed, ref } from 'vue'
import { deviceStatuses, deviceTypes, getDeviceIcon, getDeviceTypeLabel, getPoeShort, getStatusLabel, getWarrantyInfo, WARRANTY_WARNING_DAYS } from '../lib/deviceMeta.js'
import { ipSortValue } from '../lib/network.js'
import { sprache, uebersetzen } from '../i18n/index.js'

const props = defineProps({
  devices: { type: Array, default: () => [] },
  racks: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] },
})
const emit = defineEmits(['select-device', 'add'])
const filter = ref('')
const typFilter = ref('all')
const statusFilter = ref('all')
const rackFilter = ref('all')
const sortKey = ref('name')
const sortAsc = ref(true)
function rackVon(device) {
  return props.racks.find((rack) => Number(rack.id) === Number(device.rack_id)) || null
}
function ortVon(device) {
  return props.locations.find((ort) => Number(ort.id) === Number(device.location_id)) || null
}
function standort(device) {
  if (!device.rack_id) return ortVon(device)?.name || uebersetzen('inventar.ohneRack')
  const rack = rackVon(device)
  const start = Number(device.start_unit)
  const hoehe = Number(device.height_units) || 1
  const einheiten = start ? uebersetzen(hoehe > 1 ? 'inventar.einheiten' : 'inventar.einheit', { start, ende: start + hoehe - 1 }) : ''
  return [rack?.name, einheiten].filter(Boolean).join(' · ') || '–'
}
function portText(device) {
  const anzahl = Number(device.network_ports)
  if (!anzahl) return '–'
  const poe = Number(device.poe_ports)
  return poe ? `${anzahl} · ${poe} ${getPoeShort(device.poe_type) || 'PoE'}` : String(anzahl)
}
function garantie(device) { return getWarrantyInfo(device) }
const SORTIERUNG = {
  name: (device) => String(device.name || '').toLowerCase(),
  typ: (device) => getDeviceTypeLabel(device.device_type),
  // Rackname, dann von oben nach unten; Standorte danach.
  standort: (device) => device.rack_id
    ? `1${rackVon(device)?.name || '~'}|${String(1000 - (Number(device.start_unit) || 0)).padStart(4, '0')}`
    : `2${ortVon(device)?.name || '~'}|${String(device.name || '')}`,
  ip: (device) => ipSortValue(device.ip_address),
  status: (device) => getStatusLabel(device.status),
  garantie: (device) => device.warranty_until || '9999-12-31',
}
function sortiereNach(key) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else { sortKey.value = key; sortAsc.value = true }
}
function sortPfeil(key) {
  if (sortKey.value !== key) return ''
  return sortAsc.value ? '▲' : '▼'
}
const gefiltert = computed(() => {
  const suche = filter.value.trim().toLowerCase()
  const wert = SORTIERUNG[sortKey.value]
  const richtung = sortAsc.value ? 1 : -1
  return props.devices
    .filter((device) => typFilter.value === 'all' || device.device_type === typFilter.value)
    .filter((device) => statusFilter.value === 'all' || (device.status || 'active') === statusFilter.value)
    .filter((device) => {
      const wahl = String(rackFilter.value)
      if (wahl === 'all') return true
      if (wahl === 'ohne-rack') return !device.rack_id
      if (wahl.startsWith('ort:')) return Number(device.location_id) === Number(wahl.slice(4))
      return Number(device.rack_id) === Number(rackFilter.value)
    })
    .filter((device) => !suche || [device.name, device.manufacturer, device.model, device.ip_address, device.mac_address, device.serial_number, device.vlan].some((feld) => String(feld || '').toLowerCase().includes(suche)))
    .sort((a, b) => {
      const x = wert(a)
      const y = wert(b)
      if (typeof x === 'number' && typeof y === 'number') return (x - y) * richtung
      return String(x).localeCompare(String(y), sprache.value, { numeric: true }) * richtung
    })
})
const kennzahlen = computed(() => {
  const status = (wert) => props.devices.filter((device) => (device.status || 'active') === wert).length
  return {
    gesamt: props.devices.length,
    aktiv: status('active'),
    wartung: status('maintenance') + status('planned'),
    racks: new Set(props.devices.filter((device) => device.rack_id).map((device) => Number(device.rack_id))).size,
    garantie: props.devices.filter((device) => ['bald', 'abgelaufen'].includes(garantie(device).zustand)).length,
  }
})
const filterAktiv = computed(() => Boolean(filter.value.trim()) || typFilter.value !== 'all' || statusFilter.value !== 'all' || rackFilter.value !== 'all')
function filterZuruecksetzen() {
  filter.value = ''
  typFilter.value = 'all'
  statusFilter.value = 'all'
  rackFilter.value = 'all'
}
</script>

<template>
  <section class="panel view-panel">
    <div class="view-stats">
      <div class="view-stat"><span>{{ uebersetzen('inventar.geraete') }}</span><strong>{{ kennzahlen.gesamt }}</strong></div>
      <div class="view-stat"><span>{{ uebersetzen('inventar.aktiv') }}</span><strong>{{ kennzahlen.aktiv }}</strong></div>
      <div class="view-stat"><span>{{ uebersetzen('inventar.wartung') }}</span><strong>{{ kennzahlen.wartung }}</strong></div>
      <div class="view-stat"><span>{{ uebersetzen('inventar.inRacks') }}</span><strong>{{ kennzahlen.racks }}</strong></div>
      <div v-if="kennzahlen.garantie" class="view-stat view-stat-warnung" :title="uebersetzen('inventar.garantieHinweis', { tage: WARRANTY_WARNING_DAYS })"><span>{{ uebersetzen('inventar.garantieBeachten') }}</span><strong>{{ kennzahlen.garantie }}</strong></div>
    </div>
    <div class="view-toolbar">
      <input v-model="filter" type="text" :placeholder="uebersetzen('inventar.suche')" :aria-label="uebersetzen('inventar.filter')" spellcheck="false" />
      <select v-model="typFilter" :aria-label="uebersetzen('inventar.typFilter')">
        <option value="all">{{ uebersetzen('inventar.alleTypen') }}</option>
        <option v-for="typ in deviceTypes" :key="typ.value" :value="typ.value">{{ typ.label }}</option>
      </select>
      <select v-model="statusFilter" :aria-label="uebersetzen('inventar.statusFilter')">
        <option value="all">{{ uebersetzen('inventar.alleStatus') }}</option>
        <option v-for="status in deviceStatuses" :key="status.value" :value="status.value">{{ status.label }}</option>
      </select>
      <select v-model="rackFilter" :aria-label="uebersetzen('inventar.ortFilter')">
        <option value="all">{{ uebersetzen('inventar.ueberall') }}</option>
        <option value="ohne-rack">{{ uebersetzen('inventar.ohneRack') }}</option>
        <optgroup v-if="racks.length" :label="uebersetzen('inventar.racks')"><option v-for="rack in racks" :key="rack.id" :value="rack.id">{{ rack.name }}</option></optgroup>
        <optgroup v-if="locations.length" :label="uebersetzen('inventar.standorte')"><option v-for="ort in locations" :key="`o${ort.id}`" :value="`ort:${ort.id}`">{{ ort.name }}</option></optgroup>
      </select>
      <button v-if="filterAktiv" type="button" class="view-reset" @click="filterZuruecksetzen">{{ uebersetzen('inventar.zuruecksetzen') }}</button>
      <span class="view-count">{{ uebersetzen('inventar.anzahl', { anzahl: gefiltert.length, gesamt: devices.length }) }}</span>
      <button type="button" class="view-add" :disabled="!racks.length" :title="uebersetzen(racks.length ? 'inventar.neu' : 'inventar.rackZuerst')" @click="emit('add')">{{ uebersetzen('inventar.hinzufuegen') }}</button>
    </div>
    <div v-if="gefiltert.length" class="view-table-wrap">
      <table class="view-table">
        <thead><tr>
          <th><button type="button" @click="sortiereNach('name')">{{ uebersetzen('inventar.geraet') }}<i>{{ sortPfeil('name') }}</i></button></th>
          <th><button type="button" @click="sortiereNach('typ')">{{ uebersetzen('inventar.typ') }}<i>{{ sortPfeil('typ') }}</i></button></th>
          <th><button type="button" @click="sortiereNach('standort')">{{ uebersetzen('inventar.standort') }}<i>{{ sortPfeil('standort') }}</i></button></th>
          <th><button type="button" @click="sortiereNach('ip')">{{ uebersetzen('inventar.ip') }}<i>{{ sortPfeil('ip') }}</i></button></th>
          <th class="plain">{{ uebersetzen('inventar.ports') }}</th>
          <th><button type="button" @click="sortiereNach('garantie')">{{ uebersetzen('inventar.garantie') }}<i>{{ sortPfeil('garantie') }}</i></button></th>
          <th><button type="button" @click="sortiereNach('status')">{{ uebersetzen('inventar.status') }}<i>{{ sortPfeil('status') }}</i></button></th>
        </tr></thead>
        <tbody><tr v-for="device in gefiltert" :key="device.id">
          <td>
            <button type="button" class="view-link" @click="emit('select-device', device)">
              <img v-if="device.image_url" class="view-vorschau" :src="device.image_url" :alt="uebersetzen('inventar.foto', { name: device.name })" loading="lazy" decoding="async" />
              <span v-else class="view-icon">{{ getDeviceIcon(device.device_type) }}</span>{{ device.name }}
            </button>
            <small v-if="device.manufacturer || device.model" class="sub">{{ [device.manufacturer, device.model].filter(Boolean).join(' ') }}</small>
          </td>
          <td>{{ getDeviceTypeLabel(device.device_type) }}</td><td>{{ standort(device) }}</td><td class="mono">{{ device.ip_address || '–' }}</td><td>{{ portText(device) }}</td>
          <td><span v-if="garantie(device).zustand !== 'keine'" class="garantie-badge" :class="`garantie-${garantie(device).zustand}`" :title="garantie(device).text">{{ garantie(device).kurz }}</span><template v-else>–</template></td>
          <td><span class="status-badge" :class="`status-${device.status || 'active'}`">{{ getStatusLabel(device.status) }}</span></td>
        </tr></tbody>
      </table>
    </div>
    <p v-else class="view-empty">{{ uebersetzen(devices.length ? 'inventar.keineTreffer' : 'inventar.leer') }}</p>
  </section>
</template>

<style scoped>
.view-panel { display: flex; flex-direction: column; gap: 18px; padding: 22px 24px 26px; }
.view-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.view-stat-warnung strong { color: var(--t-amber-37); }
.garantie-badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 750; white-space: nowrap; }
.garantie-badge.garantie-aktiv { color: var(--t-ton-54); background: var(--f-ton-96-2); }
.garantie-badge.garantie-bald { color: var(--t-amber-37); background: var(--f-amber-89); }
.garantie-badge.garantie-abgelaufen { color: var(--t-rot-42); background: var(--f-rot-89); }
.view-stat { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border: 1px solid var(--f-ton-95); border-radius: 12px; background: var(--f-grau-99-2); }
.view-stat span { color: var(--t-ton-54); font-size: 11px; font-weight: 600; }
.view-stat strong { color: var(--t-ton-11); font-size: 22px; font-weight: 800; }
.view-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.view-toolbar input, .view-toolbar select { padding: 10px 12px; border: 1px solid var(--f-ton-91); border-radius: 10px; color: var(--t-ton-23); background: var(--f-grau-100); font: inherit; font-size: 12px; }
.view-toolbar input { width: min(100%, 280px); }
.view-toolbar input:focus, .view-toolbar select:focus { border-color: var(--f-blau-86-2); outline: none; box-shadow: 0 0 0 3px var(--f-blau-60); }
.view-reset { padding: 9px 11px; border: 0; border-radius: 9px; color: var(--t-blau-53); background: var(--f-ton-97); font: inherit; font-size: 12px; font-weight: 700; cursor: pointer; }
.view-add { padding: 10px 14px; border: 0; border-radius: 10px; color: var(--t-grau-100); background: linear-gradient(135deg, var(--f-blau-61), var(--f-blau-53)); font: inherit; font-size: 12px; font-weight: 750; cursor: pointer; }
.view-add:disabled { opacity: 0.5; cursor: default; }
.view-count { margin-left: auto; color: var(--t-ton-61-2); font-size: 12px; }
.view-table-wrap { overflow-x: auto; border: 1px solid var(--f-ton-95); border-radius: 10px; }
.view-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.view-table th { padding: 0; border-bottom: 1px solid var(--f-ton-95); background: var(--f-grau-99-2); text-align: left; white-space: nowrap; }
.view-table th button, .view-table th.plain { padding: 9px 12px; color: var(--t-ton-54); font-size: 11px; font-weight: 700; }
.view-table th button { display: flex; align-items: center; gap: 5px; width: 100%; border: 0; background: transparent; font-family: inherit; text-align: left; cursor: pointer; }
.view-table th button:hover { color: var(--t-ton-23); }
.view-table th i { font-size: 8px; font-style: normal; }
.view-table td { padding: 9px 12px; border-bottom: 1px solid var(--f-ton-96-5); color: var(--t-ton-23); white-space: nowrap; }
.view-table tbody tr:last-child td { border-bottom: 0; }
.view-table tbody tr:hover td { background: var(--f-grau-99-3); }
.sub { display: block; margin-top: 2px; color: var(--t-ton-61-2); font-size: 11px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px; }
.status-badge { display: inline-block; padding: 3px 9px; border-radius: 999px; color: var(--t-gruen-30); background: var(--f-ton-92-2); font-size: 11px; font-weight: 750; }
.status-badge.status-planned { color: var(--t-amber-33); background: var(--f-amber-89); }
.status-badge.status-maintenance { color: var(--t-blau-50); background: var(--f-ton-95-4); }
.status-badge.status-retired { color: var(--t-ton-47-3); background: var(--f-ton-95-2); }
.view-link { display: inline-flex; align-items: center; gap: 6px; padding: 0; border: 0; color: var(--t-blau-48-2); background: transparent; font: inherit; font-weight: 700; cursor: pointer; }
.view-link:hover { text-decoration: underline; }
.view-icon { color: var(--t-ton-54); }
.view-vorschau { width: 40px; height: 22px; flex-shrink: 0; object-fit: cover; border: 1px solid var(--f-ton-91-3); border-radius: 5px; background: var(--f-ton-96); }
.view-empty { margin: 0; padding: 28px 12px; border: 1px dashed var(--f-ton-91-3); border-radius: 12px; color: var(--t-ton-61-2); font-size: 13px; text-align: center; }
@media (max-width: 900px) { .view-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
