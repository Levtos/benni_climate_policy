# Climate Policy Logic

Kurzform: Aussen entscheidet, was erlaubt ist. Innen entscheidet, ob es gebraucht wird. Apply setzt hoch oder runter.

## Aussenfreigabe

Die Aussenfreigabe bewertet den Heizwert, Wetter, Forecast und Saisonband. Daraus entsteht die maximal erlaubte Stufe: Aus, Eco, Komfort oder Boost. Diese Stufe ist eine Freigabe, keine Heizanforderung.

Die gefuehlte Aussentemperatur wird in der Policy aus Rohwerten berechnet:

- reale Aussentemperatur
- Aussenluftfeuchte
- Windgeschwindigkeit

Ein fertig berechneter Feels-like-Sensor wird nicht mehr als fachlicher Input verwendet.

## Innenbedarf

Wohnzimmer und Kueche nutzen eine gemeinsame Wohnbereichsmatrix. Das Bad nutzt eine eigene Matrix. Jede Stufe hat:

- `heat_on_below`: darunter darf die freigegebene Stufe aktiv heizen
- `heat_off_at`: ab hier wird nicht nachgeheizt
- `min_hold_minutes`: vorbereitete Mindestdauer gegen Flapping

Liegt der Raum ueber `heat_off_at`, entsteht ein Downshift-Plan mit `room_temperature_above_target_no_heating` oder `bath_temperature_above_target_no_heating`.

## Zieltemperaturen

Der Plan weist drei Werte aus:

- `policy_target_temperature`: fachlicher Komfortwert, z. B. Eco 21,0 Grad
- `floor_slab_delta_current`: technischer Bodenplatten-Aufschlag
- `thermostat_target_temperature`: Zielwert, der ans Thermostat geht

Der Innenbedarf wird gegen die gemessene Raumtemperatur bewertet, nicht gegen den technisch erhoehten Thermostat-Zielwert.

## Dynamisches Bodenplatten-Delta

Das Delta wird getrennt von `floor_slab_tau` berechnet. Tau bleibt die Traegheit in der Heizwertberechnung. Delta ist der aktuelle technische Aufschlag auf den Thermostat-Zielwert.

Das dynamische Modell nutzt einen kleinen 3-Tage-Kaelteindex:

- gestern: kleiner In-Memory-Tageswert, falls vorhanden
- heute: aktuelle reale Aussentemperatur
- morgen: Forecast um ca. 12 Uhr, gecached ueber den vorhandenen Weather-Forecast

Fehlen Werte, wird die Qualitaet als `degraded` oder `fallback` markiert. Es gibt keine sekundenweisen Polls und keine schweren History-Abfragen pro Recalculate.

## Apply und Downshift

Apply setzt nicht nur hoch. Ein Plan kann auch bewusst herunterregeln oder ausschalten. Downshifts durch Fenster/Tuer, Raum ueber Ziel oder Bad ueber Ziel nutzen denselben Off-Pfad und duerfen nicht durch Cooldown blockiert werden.
