from pathlib import Path
import hashlib, re, json
p = Path('frontend/src/App.vue')
raw = p.read_bytes()
assert hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() == '58d161b9e782ab2f26b427d2f1c6911fffb7b7dd', 'App.vue changed; refusing to overwrite it'
s = raw.decode()
out = s.replace("import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'", "import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'\nimport { uebersetzen } from './i18n/index.js'\nimport Sprachwahl from './components/Sprachwahl.vue'", 1)
de = {}; en = {}
def text(key, german, english):
    de[key] = german; en[key] = english
    return "uebersetzen('dashboard." + key + "')"
def once(old, new):
    global out
    assert out.count(old) == 1, old
    out = out.replace(old, new, 1)
start = out.index('const VIEWS = {'); end = out.index('\nconst currentView =', start)
nav = out[start:end]
titles = {'dashboard':'Dashboard','ip':'IP management','vlans':'VLANs','racks':'Racks','locations':'Locations','devices':'Devices','ports':'Ports','connections':'Connections','network':'Network map','export':'Export & Import','labels':'Labels','settings':'Settings'}
subtitles = {'dashboard':'','ip':'All addresses sorted by network, with duplicate assignments highlighted.','vlans':'Devices grouped by VLAN, showing the network in use.','racks':'All racks at a glance.','locations':'Devices outside racks — access points, modems and cameras.','devices':'All devices, in racks and at locations.','ports':'Port assignments for a device selected from any rack.','connections':'All documented port connections.','network':'Topology from port connections across all racks.','export':'Download data as CSV, JSON or PDF, or restore a backup.','labels':'Print QR labels for devices on A4 sheets or a label printer.','settings':'Your profile, password and RackView accounts.'}
def entry(m):
    key, title, subtitle = m.groups()
    return f"  {key}: {{ title: {text('titel_'+key,title,titles[key])}, subtitle: {text('untertitel_'+key,subtitle,subtitles[key])} }},"
nav = re.sub(r"  (\w+): \{ title: '([^']*)', subtitle: '([^']*)' \},", entry, nav)
nav = nav.replace('const VIEWS = {','const VIEWS = computed(() => ({',1).replace('\n}\n\nconst navGroups = [','\n}))\n\nconst navGroups = computed(() => [',1)
nav = nav.rstrip(); assert nav.endswith(']'); nav = nav[:-1] + '])\n\n'
for key in titles:
    nav = re.sub(r"(\{ key: '"+key+r"', icon: '[^']+', label: )'[^']+'", lambda m:m[1]+"uebersetzen('dashboard.titel_"+key+"')", nav)
nav = nav.replace("label: 'Arbeitsbereich'", 'label: '+text('arbeitsbereich','Arbeitsbereich','Workspace')).replace("label: 'Verwaltung'", 'label: '+text('verwaltung','Verwaltung','Administration'))
out = out[:start] + nav + out[end:]
out = out.replace('VIEWS[currentView.value]','VIEWS.value[currentView.value]').replace('if (VIEWS[key])','if (VIEWS.value[key])')
once("label: 'Keine Geräte'", 'label: '+text('keineGeraete','Keine Geräte','No devices'))
once("label: 'Alle Geräte aktiv'", 'label: '+text('alleAktiv','Alle Geräte aktiv','All devices active'))
text('nichtAktiv','{anzahl} von {gesamt} nicht aktiv','{anzahl} of {gesamt} inactive')
once('label: `${nichtAktiv.length} von ${liste.length} nicht aktiv`', "label: uebersetzen('dashboard.nichtAktiv', { anzahl: nichtAktiv.length, gesamt: liste.length })")
once("return 'Deine Infrastruktur übersichtlich dokumentiert.'", 'return '+text('infrastrukturText','Deine Infrastruktur übersichtlich dokumentiert.','Your infrastructure, clearly documented.'))
text('rackHoehe','{anzahl} Höheneinheiten','{anzahl} rack units'); text('belegtWert','{anzahl} HE belegt','{anzahl} U used'); text('einheiten','{anzahl} HE','{anzahl} U')
once('const teile = [`${getRackHeight(selectedRack.value)} Höheneinheiten`]', "const teile = [uebersetzen('dashboard.rackHoehe', { anzahl: getRackHeight(selectedRack.value) })]")
once('teile.push(`${usedUnits.value} HE belegt`)', "teile.push(uebersetzen('dashboard.belegtWert', { anzahl: usedUnits.value }))")
text('aktuellesRack','{name} (aktuell)','{name} (current)')
once('`${rack.name} (aktuell)`', "uebersetzen('dashboard.aktuellesRack', { name: rack.name })")
text('frei','Frei','Free')
once("platz?.connected_device?.name || platz?.external_label || 'frei'", "platz?.connected_device?.name || platz?.external_label || uebersetzen('dashboard.frei')")
text('heEinheit','HE {start}','U {start}'); text('heBereich','HE {start}–{ende}','U {start}–{ende}')
once('return hoehe > 1 ? `HE ${start}–${start + hoehe - 1}` : `HE ${start}`', "return uebersetzen(hoehe > 1 ? 'dashboard.heBereich' : 'dashboard.heEinheit', { start, ende: start + hoehe - 1 })")
text('keinPlatz','Kein Platz für {hoehe} HE in „{name}\"','No room for {hoehe} U in “{name}”')
once('`Kein Platz für ${hoehe} HE in „${drag.zielRack.name}\"`', "uebersetzen('dashboard.keinPlatz', { hoehe, name: drag.zielRack.name })")
once("return 'Loslassen bricht ab'", 'return '+text('dragAbbruch','Loslassen bricht ab','Release to cancel'))
text('blockiert','Belegt durch „{name}\"','Occupied by “{name}”')
once('return `Belegt durch „${drag.blockiert.name}\"`', "return uebersetzen('dashboard.blockiert', { name: drag.blockiert.name })")
a = out.index('<template>'); b = out.index('    <div v-if="showRackForm"', a)
tpl = out[a:b]
static = [
('laden','RackView wird geladen …','Loading RackView …'),('rackBearbeiten','✎ Rack bearbeiten','✎ Edit rack'),('pdf','⎙ Als PDF drucken','⎙ Print to PDF'),('rackHinzufuegen','+ Rack hinzufügen','+ Add rack'),('neuesRack','Neues Rack anlegen','Create a new rack'),('rackLoeschen','Rack löschen …','Delete rack …'),('infrastruktur','Infrastruktur','Infrastructure'),('rackAnsicht','Rack-Ansicht','Rack view'),('vorneTitel','Vorderseite','Front'),('hintenTitel','Rückseite','Rear'),('frei','Frei','Free'),('keineRackGeraete','Noch keine Geräte in diesem Rack.','No devices in this rack yet.'),('aktiv','Aktiv','Active'),('geplantWartung','Geplant / Wartung','Planned / Maintenance'),('ausgemustert','Ausgemustert','Retired'),('dragHinweis','Geräte zum Verschieben ziehen, auch auf ein anderes Rack','Drag devices to move them, including to another rack'),('geraete','Geräte','Devices'),('belegt','Belegt','Used'),('keinRack','Noch kein Rack vorhanden','No rack yet'),('erstesRackText','Lege dein erstes Rack an, um Geräte und Ports zu verwalten.','Create your first rack to manage devices and ports.'),('rackAnlegen','Rack anlegen','Create a rack'),('rackAnlegenText','Name und Höhe in HE','Name and height in rack units'),('geraeteEinsetzen','Geräte einsetzen','Add devices'),('geraeteEinsetzenText','in die freien Höheneinheiten des Racks','to the available rack units'),('portsVerbinden','Ports verbinden','Connect ports'),('portsVerbindenText','der Netzwerkplan zeichnet sich selbst','the network map is generated automatically'),('erstesRack','Erstes Rack erstellen','Create your first rack'),('auswahl','Auswahl','Selection'),('geraetedetails','Gerätedetails','Device details'),('verwalten','Verwalten','Manage'),('etikett','⌗ Etikett','⌗ Label'),('bearbeiten','✎ Bearbeiten','✎ Edit'),('keinGeraet','Kein Gerät ausgewählt','No device selected'),('geraetWaehlen','Wähle ein Gerät in der Rack-Ansicht aus.','Select a device in the rack view.'),('anschluesseLaden','Anschlüsse werden geladen …','Loading connections …'),('netzwerkports','Netzwerkports','Network ports'),('steckplaetze','Steckplätze','Outlets'),('nichtsErfasst','Nichts erfasst','Nothing documented'),('rackLeer','In diesem Rack sind noch keine Geräte.','No devices in this rack yet.'),('geraetOeffnen','Gerät öffnen','Open device'),('anschluss','Anschluss','Connection'),('typ','Typ','Type'),('geschwindigkeit','Geschwindigkeit','Speed'),('verbundenMit','Verbunden mit','Connected to'),('notizen','Notizen','Notes'),('angeschlossen','Angeschlossen','Connected device'),('stehtIn','Steht in','Located in'),('beschriftung','Beschriftung','Label'),('steckplaetzeBearbeiten','Steckplätze bearbeiten','Edit outlets'),('topologie','Topologie','Topology'),('netzwerkplan','Netzwerkplan','Network map'),('keineSuchgeraete','Keine Geräte gefunden.','No devices found.')]
for key, german, english in static:
    expr = text(key,german,english)
    tpl = re.sub(r'(?<=>)(\s*)'+re.escape(german)+r'(\s*)(?=<)', lambda m:m[1]+'{{ '+expr+' }}'+m[2], tpl)
attrs = [('aria-label','Hauptnavigation','hauptnavigation','Main navigation'),('title','Profil und Einstellungen','profil','Profile and settings'),('title','Abmelden','abmelden','Sign out'),('aria-label','Abmelden','abmelden','Sign out'),('aria-label','Pfad','pfad','Breadcrumb'),('placeholder','Suche nach Geräten, IPs, MAC …','suche','Search devices, IPs, MAC …'),('aria-label','Geräte durchsuchen','geraeteSuchen','Search devices'),('aria-label','Suchergebnisse','suchergebnisse','Search results'),('aria-label','Weitere Aktionen','weitereAktionen','More actions'),('title','Rack bearbeiten','rackBearbeitenTitel','Edit rack'),('aria-label','Rackansicht','rackAnsichtLabel','Rack view'),('title','QR-Etikett für dieses Gerät drucken','etikettDrucken','Print a QR label for this device'),('aria-label','Gerät für die Anschlussübersicht','anschlussGeraet','Device for connection overview')]
for attr, german, key, english in attrs:
    old = attr+'="'+german+'"'; assert old in tpl, old
    tpl = tpl.replace(old, ':'+attr+'="'+text(key,german,english)+'"')
expressions = [
('Menü schließen','menueSchliessen','Close menu'),('Ohne Standort','ohneStandort','No location'),('Ohne Rack','ohneRack','No rack'),('Rack-Dokumentation','rackDokumentation','Rack documentation'),('Kein Standort hinterlegt','keinStandort','No location specified'),('Nur vorne eingebaut','nurVorne','Front-mounted only'),('Nur hinten eingebaut','nurHinten','Rear-mounted only'),('vorne','vorne','front'),('hinten','hinten','rear'),('Stromversorgung','stromversorgung','Power supply'),('Verbindungen','verbindungen','Connections'),('Port-Übersicht','portUebersicht','Port overview'),('Steckplätze','steckplaetze','Outlets'),('Platz-Details','platzDetails','Outlet details'),('Port-Details','portDetails','Port details'),('Kein PoE','keinPoe','No PoE'),('Belegt','belegt','Used'),('Frei','frei','Free'),('frei','frei','Free'),('Kein Platz ausgewählt','keinPlatzAuswahl','No outlet selected'),('Kein Port ausgewählt','keinPortAuswahl','No port selected'),('Wähle einen Steckplatz aus der Übersicht.','platzWaehlen','Select an outlet from the overview.'),('Wähle einen Port aus der Übersicht.','portWaehlen','Select a port from the overview.'),('Verbindung','verbindung','Connection'),('Zur hellen Ansicht wechseln','hell','Switch to light mode'),('Zur dunklen Ansicht wechseln','dunkel','Switch to dark mode')]
for german,key,english in expressions:
    tpl = tpl.replace("'"+german+"'",text(key,german,english))
tpl = tpl.replace('RackView <span>/</span> Übersicht', 'RackView <span>/</span> {{ '+text('uebersicht','Übersicht','Overview')+' }}')
tpl = tpl.replace('· HE {{ treffer.device.start_unit }}', "· {{ uebersetzen('dashboard.heEinheit', { start: treffer.device.start_unit }) }}")
for expr in ['rack.height_units','getRackHeight(selectedRack)','getDeviceHeight(device)','getUsedRackUnits(selectedRack)','getRackHeight(selectedRack) - getUsedRackUnits(selectedRack)']:
    tpl = tpl.replace('{{ '+expr+' }} HE', "{{ uebersetzen('dashboard.einheiten', { anzahl: "+expr+" }) }}")
text('verschieben','{name} – zum Verschieben ziehen','{name} — drag to move')
tpl = tpl.replace('`${row.device.name} – zum Verschieben ziehen`', "uebersetzen('dashboard.verschieben', { name: row.device.name })")
text('belegtGesamt','{belegt} von {gesamt} HE belegt','{belegt} of {gesamt} U used')
tpl = tpl.replace('{{ getUsedRackUnits(selectedRack) }} von\n            {{ getRackHeight(selectedRack) }} HE belegt', "{{ uebersetzen('dashboard.belegtGesamt', { belegt: getUsedRackUnits(selectedRack), gesamt: getRackHeight(selectedRack) }) }}")
tpl = tpl.replace("{{ getUsedRackUnits(selectedRack) }} von\n            {{ uebersetzen('dashboard.einheiten', { anzahl: getRackHeight(selectedRack) }) }} belegt", "{{ uebersetzen('dashboard.belegtGesamt', { belegt: getUsedRackUnits(selectedRack), gesamt: getRackHeight(selectedRack) }) }}")
text('platz','Platz {position}','Outlet {position}')
tpl = tpl.replace("`Platz ${platz.position} – ${outletBelegt(platz) ? outletName(platz) : uebersetzen('dashboard.frei')}`", "`${uebersetzen('dashboard.platz', { position: platz.position })} – ${outletBelegt(platz) ? outletName(platz) : uebersetzen('dashboard.frei')}`")
tpl = tpl.replace('Platz {{ selectedOutlet.position }}', "{{ uebersetzen('dashboard.platz', { position: selectedOutlet.position }) }}")
tpl = tpl.replace('· außerhalb des Racks', '· {{ '+text('ausserhalb','außerhalb des Racks','outside the rack')+' }}')
for german,key,english in [('Verbunden','verbunden','Connected'),('Defekt','defekt','Faulty'),('Deaktiviert','deaktiviert','Disabled'),('Belegt','belegt','Used'),('Frei','frei','Free')]:
    tpl = tpl.replace(german+' ({{', '{{ '+text(key,german,english)+' }} ({{')
text('anschluesseLeer','Für „{name}\" sind weder Ports noch Steckplätze angelegt. Beides richtest du in den Gerätedetails ein.','No ports or outlets are configured for “{name}”. Set them up in the device details.')
tpl = tpl.replace('Für „{{ portOverviewDevice.name }}\" sind weder Ports noch Steckplätze\n          angelegt. Beides richtest du in den Gerätedetails ein.', "{{ uebersetzen('dashboard.anschluesseLeer', { name: portOverviewDevice.name }) }}")
de['sucheFelder'] = {'Name':'Name','IP':'IP','MAC':'MAC','Hersteller':'Hersteller','Modell':'Modell','Seriennummer':'Seriennummer','VLAN':'VLAN'}
en['sucheFelder'] = {'Name':'Name','IP':'IP','MAC':'MAC','Hersteller':'Manufacturer','Modell':'Model','Seriennummer':'Serial number','VLAN':'VLAN'}
tpl = tpl.replace('{{ treffer.grund.label }}:', "{{ uebersetzen('dashboard.sucheFelder.' + treffer.grund.label) }}:")
tpl = tpl.replace('      <div class="sidebar-user">', '      <Sprachwahl />\n      <div class="sidebar-user">')
out = out[:a] + tpl + out[b:]
assert out[out.index('    <div v-if="showRackForm"'):] == s[s.index('    <div v-if="showRackForm"'):], 'Dialogs or styles changed'
assert re.findall(r'@[-\w.]+="[^"]*"', tpl) == re.findall(r'@[-\w.]+="[^"]*"', s[s.index('<template>'):s.index('    <div v-if="showRackForm"')]), 'Event handlers changed'
assert set(en) == set(de)
for key in en:
    if isinstance(en[key],str):
        assert set(re.findall(r'\{(\w+)\}',en[key])) == set(re.findall(r'\{(\w+)\}',de[key])), key
assert set(re.findall(r"'dashboard\.([\w_]+)'",out)) <= set(en)
for lang, data in [('en',en),('de',de)]:
    target = Path(f'frontend/src/i18n/locales/{lang}/dashboard.json')
    assert not target.exists(), f'{target} already exists; refusing to overwrite'
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
p.write_text(out)
