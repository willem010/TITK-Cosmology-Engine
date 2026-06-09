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

### 4.3 Theoretische Grenswaarden & Systeemlimieten

####  De Onmogelijkheid van Faster-Than-Light (FTL) Informatieoverdracht
Binnen het Topological Information Theoretical Kernel (TITK) model is de lichtsnelheid ($c$) geen arbitraire geometrische constante, maar de fundamentele **I/O-limiet van de netwerktopologie**. Ruimte en tijd zijn immers emergent en vloeien voort uit de opeenvolgende interacties en state-transities tussen onderlinge nodes. 

FTL-reizen of informatieoverdracht is binnen dit framework computationeel onmogelijk vanwege drie harde netwerk-technische barrières:

##### I. De Kosmische Systeemklok (Transitie-limiet)
De basissnelheid van het netwerk wordt bepaald door de tijd die één topologische sprong (een informatie-update tussen twee direct verbonden nodes) kost:

$$\Delta t_{min} = 1 \text{ netwerk-tick}$$

Sneller gaan dan de lichtsnelheid zou betekenen dat een informatie-pakketje een node overslaat of arriveert *voordat* de lokale netwerkcyclus heeft plaatsgevonden. Een subsysteem kan niet sneller muteren dan de kloksnelheid van de processor waar het op draait.

##### II. Topologische Deadlocks (De Kosmische Race Condition)
Als informatie zich sneller door de topologie zou verplaatsen dan de causale update-signalen kunnen propageren, ontstaat er een computationele **Race Condition**. 

* Een Node B zou een status aannemen op basis van een input uit Node A, nog voordat de causale link in de omliggende topologie is verwerkt.
* Dit resulteert in een niet-causale feedback-loop waarin een output zijn eigen input overschrijft of wist.
* Om de data-integriteit en causale consistentie van de kosmos te bewaken, spert het netwerk deze optie mathematisch af; FTL leidt tot een logische `Deadlock`.

##### III. De Oneindige Bandbreedte Paradox (Massa-toename)
In de klassieke relativiteitstheorie heeft een object op lichtsnelheid oneindig veel energie nodig. Binnen TITK vertaalt 'massa/energie' zich naar **informatiedichtheid en routing-complexiteit**.

* Naarmate een object de snelheid $c$ nadert, dwingt de Lorentz-contractie het netwerk om de data over een steeds compacter cluster van nodes te berekenen.
* Om exact de grens van $c$ te passeren, zou de transitie-load (het aantal netwerk-updates per klokcyclus) naar oneindig schieten. 
* FTL is onmogelijk omdat het de totale verwerkingscapaciteit (bandbreedte) van het universele netwerk overschrijdt. Tijddilatatie treedt hierbij op als een automatische *rate-limiter* (buffer) om een lokale data-overflow te voorkomen.

> **TITK Postulaat omtrent Causaliteit:** *Faster-Than-Light (FTL) is binnen een informatietheoretische topologie een ongedefinieerde bewerking. De natuurkundige limiet $c$ is de maximale doorvoersnelheid van causale netwerk-updates. Het overschrijden van deze limiet is inherent gelijk aan het crashen van de lokale netwerkintegriteit.*

