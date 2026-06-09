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
