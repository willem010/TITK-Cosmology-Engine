## 4. HET WACHTRIJ-PRINCIPE (QUEUE-DEPTH & LIMITS)

### 4.1 De Topologische Wachtrij
Wanneer een node of node-cluster wordt blootgesteld aan een extreme instroom van causale updates ($I_{conn}$), dwingt de wet van informatiebehoud de node om zich als een buffer te gedragen. De interne verwerking verloopt via een strikt opeenvolgende keten:

$$\text{Ingang} \longrightarrow \text{Buffer } (\sigma_{int}) \longrightarrow \text{Verwerking } (T_{eff}) \longrightarrow \text{Output } (\sigma_{pub})$$

Elke causale update reist tussen de nodes onwrikbaar met de maximale propagatiesnelheid $c$. Echter, door de verhoogde interne synchronisatietijd ($T_{eff}$) binnen de private structuur, wordt de uiteindelijke publicatie naar de publieke toestand ($\sigma_{pub}$) vertraagd. De update moet wachten tot de interne netwerkcyclus volledig is afgerond.

---

### 4.2 Kritieke Consolidatiecapaciteit ($Q_{max}$)
Om te voorkomen dat de computationele wachtrij van een node oneindig diep wordt — wat de stabiliteit van de matrix zou ontwrichten — introduceert TITK een harde structurele grens: **$Q_{max}$ (Maximale Lokale Consolidatiecapaciteit)**. Een node bezit een absolute limiet voor de hoeveelheid causale stappen die hij gelijktijdig in de wachtrij kan houden binnen één universele matrixcyclus ($T_{obs} = 1$).

#### Het Singulair Effect (Topologische Definitie van een Zwart Gat)
Wanneer de lokale netwerkdichtheid de kritieke waarde $Q_{max}$ overschrijdt, raakt de topologische wachtrij onherroepelijk verzadigd. 

* De node kan de inkomende causale belasting niet langer verwerken binnen de universele klokslag.
* Het causale pad loopt op dit specifieke punt asymptotisch vast.

Dit levert binnen TITK de exacte mechanistische verklaring voor wat de klassieke fysica omschrijft als een **zwart gat**: het is geen oneindige massa-oneindigheid (singulariteit), maar een zone waar de netwerk-latency asymptotisch oneindig wordt omdat de maximale *queue depth* ($Q_{max}$) is bereikt.

---

# 4.3 Theoretische Grenswaarden & Systeemlimieten

## De Onmogelijkheid van Faster-Than-Light (FTL) Informatieoverdracht

Binnen TITK is de lichtsnelheid ($c$) geen arbitraire geometrische constante, maar de fundamentele **I/O-limiet van de netwerktopologie**. Ruimte en tijd zijn emergent — zij vloeien voort uit de opeenvolgende interacties en toestandsovergangen tussen nodes. FTL-informatieoverdracht is binnen dit framework computationeel onmogelijk vanwege drie harde netwerkbarrières.

---

### I. De Kosmische Systeemklok (Transitie-limiet)

De basissnelheid van het netwerk wordt bepaald door de minimale tijd voor één topologische sprong:

$$\Delta t_{min} = 1 \text{ netwerk-tick} = T_{obs}$$

Sneller gaan dan $c$ zou betekenen dat een informatiepakket een node overslaat, of arriveert *voordat* de lokale netwerkcyclus heeft plaatsgevonden. Een subsysteem kan niet sneller muteren dan de kloksnelheid van de processor waarop het draait.

**Verband met T_eff:** De lokale tijddilatatie ($T_{eff}$) werkt als een automatische *rate-limiter*. Bij hogere informatiedichtheid stijgt $T_{eff}$, daalt $\Phi_{ext}$, en vertraagt de effectieve propagatiesnelheid — zonder dat $c$ zelf verandert. Tijddilatatie is in TITK geen geometrisch effect maar een verwerkingsbudget-effect. Dit is de mechanistische verklaring van de Schwarzschild-metriek (zie Spec v1.4, Sectie 1).

---

### II. Topologische Deadlocks (De Kosmische Race Condition)

Als informatie zich sneller door de topologie zou verplaatsen dan causale updatesignalen kunnen propageren, ontstaat een computationele **Race Condition**:

- Node B neemt een toestand aan op basis van input van Node A, nog voordat de causale link in de omliggende topologie is verwerkt.
- Dit resulteert in een niet-causale feedbackloop waarin een output zijn eigen input overschrijft of wist.
- Het netwerk spert deze optie mathematisch af: FTL leidt tot een logische `Deadlock` die de data-integriteit van de kosmos zou vernietigen.

**Verband met het Consolidatieprincipe:** De consolidatieoperatie (Spec 1.3.1, Sectie 2.2) is de mechanisme waarmee het netwerk deadlocks voorkomt — door causale bijdragen te absorberen zodra zij volledig zijn verwerkt, wordt de feedbackloop gesloten voordat hij recursief kan worden.

---

### III. De Oneindige Bandbreedte Paradox (Massa-toename bij $v \to c$)

In de klassieke relativiteitstheorie heeft een object op lichtsnelheid oneindig veel energie nodig. In TITK vertaalt massa/energie zich naar **informatiedichtheid en routingcomplexiteit**:

- Naarmate een object $c$ nadert, dwingt de Lorentz-contractie het netwerk om de data over een steeds compacter cluster van nodes te berekenen.
- De transitie-load (het aantal netwerk-updates per klokcyclus) nadert oneindig bij $v \to c$.
- FTL is onmogelijk omdat het de totale verwerkingscapaciteit ($W_{max}$) van het universele netwerk zou overschrijden.

$$v \to c \implies T_{eff} \to W_{max} \implies \Phi_{ext} \to 0$$

Dit is identiek aan de zwart gat conditie (Spec 1.3.1, Sectie 4.2) — een object dat $c$ bereikt verzadigt zijn eigen queue. FTL en zwarte gaten zijn in TITK hetzelfde fenomeen op verschillende schalen.

---

### TITK Postulaat omtrent Causaliteit

> *Faster-Than-Light (FTL) is binnen een informatietheoretische topologie een ongedefinieerde bewerking. De natuurkundige limiet $c$ is de maximale doorvoersnelheid van causale netwerk-updates. Het overschrijden van deze limiet is inherent gelijk aan het crashen van de lokale netwerkintegriteit.*

---

*Sectie toegevoegd: juni 2026 — v1.4*
