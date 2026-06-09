#!/usr/bin/env python3
"""
TITK Cosmology Engine — Versie 1.4 (Core Simulation)
Topologische Informatietheorie van de Kosmos

Computationele engine voor het simuleren van een schaalinvariant, 
fixed-budget informatienetwerk en de emergentie van kosmologische structuren.

Vereisten: pip install numpy scipy matplotlib
Gebruik: python3 titk_sim.py
"""

import numpy as np
from scipy.fft import fft2, fftshift
from scipy.ndimage import uniform_filter
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import time
import os

# ─── CONFIGURATIE (MASTER SPECIFICATION V1.3.1 / V1.4) ─────────
CFG = {
    "GRID":             256,    # Matrixresolutie (Macht van 2 voor FFT-optimalisatie)
    "Q_MAX":            12,     # Maximale Lokale Consolidatiecapaciteit (Queue Depth)
    "W_MAX":            100.0,  # Totale Kosmische Capaciteit (Vast Budget per Node)
    "K_FACTOR":         6.0,    # Interne routing- en synchronisatiekostenvermenigvuldiger
    "C_RADIUS":         0.055,  # Genormaliseerde verbindingsradius van de netwerktopologie
    "NOISE_AMP":        0.15,   # Primordiale topologische ruisamplitude
    "BACKPRESSURE":     0.75,   # Terugkoppelingssterkte van verzadigde (Q_max) nodes
    "TOPOLOGY_EVO":    0.004,  # Netwerk-herconfiguratiesnelheid tijdens de plasma-fase
    "DECOUPLING":       380,    # Ontkoppelingsmoment (Generatie van het CMB-snapshot)
    "TOTAL_CYCLES":     500,    # Totaal aantal universele matrixcycli (T_obs)
    "OUTPUT_INTERVAL":  20,     # Statistieken weergave-interval
    "SAVE_SNAPSHOTS":   True,   # Bewaar binaire matrix-toestanden (.npy)
}

# ─── PRIMORDIAAL TOPOLOGISCH RUISVELD (Harrison-Zel'dovich 1/f) ───
def make_primordial_field(G, noise_amp, num_seeds=8):
    """
    Genereert een 1/f topologische ruisdistributie over meerdere octaven.
    De amplitude is omgekeerd proportioneel aan de frequentie (1/k),
    waardoor grootschalige netwerkstructuren inherent domineren.
    """
    noise = np.zeros((G, G))
    x = np.arange(G)
    y = np.arange(G)
    xx, yy = np.meshgrid(x, y)

    for oct in range(7):
        freq = 2 ** (oct + 1)
        amplitude = 1.0 / freq          # 1/k schaling van het vermogensspectrum
        px = np.random.uniform(0, 2*np.pi)
        py = np.random.uniform(0, 2*np.pi)
        pxy = np.random.uniform(0, 2*np.pi)
        wave = (np.sin(freq * 2*np.pi * xx/G + px) *
                np.cos(freq * 2*np.pi * yy/G + py) +
                np.sin(freq * 2*np.pi * (xx+yy)/G + pxy) * 0.5)
        noise += amplitude * wave

    # Normalisatie naar het interval [0,1]
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-10)

    # Generatie van stabiele energetische zaaikernen (baryonische condensatie)
    seeds = []
    for _ in range(num_seeds):
        seeds.append({
            "x": G * (0.2 + np.random.uniform() * 0.6),
            "y": G * (0.2 + np.random.uniform() * 0.6),
            "strength": 0.4 + np.random.uniform() * 0.6,
            "width": 0.04 + np.random.uniform() * 0.08,
        })
    
    # Centrale dominante topologische singulariteit (Oer-condensaat)
    seeds.append({"x": G/2, "y": G/2, "strength": 1.0, "width": 0.12})

    cx, cy = np.meshgrid(np.arange(G)/G, np.arange(G)/G)
    seed_field = np.zeros((G, G))
    for s in seeds:
        dx = cx - s["x"]/G
        dy = cy - s["y"]/G
        seed_field += s["strength"] * np.exp(-(dx**2 + dy**2) / (2 * s["width"]**2))
    seed_field = np.clip(seed_field, 0, 1)

    sigma = seed_field * 0.7 + noise * noise_amp * 2.5
    sigma += np.random.normal(0, noise_amp * 0.3, (G, G))
    return np.clip(sigma, 0, 1)


# ─── CORE COMPUTATION ENGINE (TITK UPDATE-REGEL) ──────────────
def simulation_step(sigma, saturated, cycle, G, radius, cfg):
    """
    Eén discrete universele cyclus (T_obs = 1). 
    Volledig gevectoriseerde NumPy-implementatie ter eliminatie van iteratielatency.
    """
    W_MAX = cfg["W_MAX"]
    K_FACTOR = cfg["K_FACTOR"]
    Q_MAX = cfg["Q_MAX"]

    # ── Kosmologische Fasebepaling & Netwerkevolutie ──────────
    if cycle < 20:
        phase = "singularity"
        net_evolution = 0.0
    elif cycle < 80:
        phase = "inflation"
        net_evolution = 0.08
    elif cycle < cfg["DECOUPLING"]:
        phase = "plasma"
        net_evolution = cfg["TOPOLOGY_EVO"]
    elif cycle == cfg["DECOUPLING"]:
        phase = "decoupling"
        net_evolution = cfg["TOPOLOGY_EVO"]
    else:
        phase = "cmb"
        net_evolution = 0.002

    # ── Causale Buuranalyse via Matrix-Convolutie ─────────────
    neighbor_sum = uniform_filter(sigma, size=radius*2+1, mode='wrap') * (radius*2+1)**2
    neighbor_count = (radius*2+1)**2 - 1
    neighbor_avg = (neighbor_sum - sigma) / neighbor_count
    I_conn = neighbor_count  # Constante verbindingsgraad op uniform tweedimensionaal grid

    # ── Boekhoudregel: T_eff (Interne Verwerkingskosten) ──────
    delta = np.abs(sigma - neighbor_avg)
    base_cost = K_FACTOR * delta * max(1, I_conn * 0.3)
    density_boost = sigma * I_conn * 0.5
    t_eff = np.clip(base_cost + density_boost, 0, W_MAX)

    # ── Topologische Backpressure (Congestietransmissie) ──────
    sat_neighbors = uniform_filter(
        saturated.astype(np.float32), size=radius*2+1, mode='wrap'
    ) * (radius*2+1)**2
    backpressure = sat_neighbors * (W_MAX / Q_MAX) * cfg["BACKPRESSURE"]
    t_eff = np.clip(t_eff + backpressure, 0, W_MAX)

    # ── Queue Depth & Singulariteitseffect (Zwart Gat) ───────
    queue_depth = (t_eff / (W_MAX / Q_MAX)).astype(int)
    new_saturated = (queue_depth >= Q_MAX) | (t_eff >= W_MAX)
    
    # Externe output vloeit voort uit het resterende budget: Phi_ext = W_max - T_eff
    phi_ext = np.where(new_saturated, 0.0, np.maximum(0, W_MAX - t_eff))

    # ── Projectie naar Interne Structuur (Sigma_int) ──────────
    sigma_int = neighbor_avg.copy()

    # ── Publicatie naar Publieke Toestand (Sigma_pub) ─────────
    sigma_new = sigma.copy()
    active = ~new_saturated
    sigma_new[active] = (sigma[active] * (1 - net_evolution) +
                         sigma_int[active] * net_evolution)

    # Kwantumfluctuaties (Incoherente perturbatiemasker)
    noise_mask = np.random.random((G, G)) < 0.005
    sigma_new += np.where(noise_mask & active,
                          np.random.normal(0, 0.02, (G, G)), 0)
    sigma_new = np.clip(sigma_new, 0, 1)

    stats = {
        "phase": phase,
        "sat_frac": new_saturated.mean(),
        "avg_sigma": sigma_new.mean(),
        "avg_teff": t_eff.mean(),
        "avg_phi": phi_ext.mean(),
    }

    return sigma_new, new_saturated, t_eff, phi_ext, stats


# ─── VERMOGENSSPECTRUM-ANALYSE (FFT CORRELATIE) ────────────────
def compute_power_spectrum(field):
    """
    Berekent het tweedimensionale vermogensspectrum via Scipy discrete FFT2.
    Voert een radiale binning uit ten behoeve van kosmische schaalvergelijking.
    """
    f = field - field.mean()
    F = fftshift(fft2(f))
    power2d = np.abs(F)**2 / (f.size**2)

    N = field.shape[0]
    halfN = N // 2
    cy, cx = N//2, N//2

    y_idx, x_idx = np.mgrid[0:N, 0:N]
    k_map = np.round(np.sqrt((x_idx - cx)**2 + (y_idx - cy)**2)).astype(int)

    power = np.zeros(halfN)
    counts = np.zeros(halfN)
    for k in range(1, halfN):
        mask = k_map == k
        if mask.any():
            power[k] = power2d[mask].mean()
            counts[k] = mask.sum()

    return power, counts


# ─── PLANCK CMB REFERENTIEDATA (OBSERVATORISCH KADER) ─────────
def get_planck_reference():
    """
    Gereconstrueerde benchmark van het Planck CMB vermogensspectrum (2018 resultaten).
    Bevat de drie akoestische pieken op respectievelijk multipool l ≈ 200, 540 en 810.
    """
    l = np.arange(2, 2500)
    spectrum = (
        1000 / l**0.1 *
        (1 + 2.5 * np.exp(-((l-200)/60)**2) +
             1.4 * np.exp(-((l-540)/80)**2) +
             0.8 * np.exp(-((l-810)/90)**2)) *
        np.exp(-l**2 / (2*2500**2))
    )
    return l, spectrum


# ─── VISUALISATIE EN GRAFISCHE RENDERING ──────────────────────
def make_figure(sigma, cmb_snapshot, t_eff, history, power, G, decoupling):
    fig = plt.figure(figsize=(16, 10), facecolor='#020810')
    fig.suptitle('TITK Cosmology Engine v1.4 — Matrix Evolutie',
                 color='#c8d8f0', fontsize=14, fontfamily='monospace')

    gs = gridspec.GridSpec(2, 3, figure=fig,
                           hspace=0.35, wspace=0.3,
                           left=0.06, right=0.97, top=0.92, bottom=0.08)

    ax_live   = fig.add_subplot(gs[0, 0])
    ax_teff   = fig.add_subplot(gs[0, 1])
    ax_cmb    = fig.add_subplot(gs[0, 2])
    ax_hist   = fig.add_subplot(gs[1, 0:2])
    ax_spec   = fig.add_subplot(gs[1, 2])

    for ax in [ax_live, ax_teff, ax_cmb, ax_hist, ax_spec]:
        ax.set_facecolor('#050a14')
        ax.tick_params(colors='#4466aa', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#1a2a3a')

    # Live Informatiedichtheid (Sigma_pub)
    ax_live.imshow(sigma, cmap='Blues_r', vmin=0, vmax=1, origin='lower')
    ax_live.set_title('Informatiedichtheid (σ_pub)', color='#88bbff',
                      fontsize=9, fontfamily='monospace')

    # Effectieve Interne Tijd (T_eff / Tijddilatatie-gradiënt)
    ax_teff.imshow(t_eff, cmap='hot', vmin=0, vmax=CFG["W_MAX"], origin='lower')
    ax_teff.set_title('Verwerkingslast (T_eff)', color='#ffcc44',
                      fontsize=9, fontfamily='monospace')

    # Kosmische Achtergrondstraling (CMB Snapshot)
    if cmb_snapshot is not None:
        ax_cmb.imshow(cmb_snapshot, cmap='RdYlBu_r', origin='lower')
        ax_cmb.set_title(f'CMB Horizon Snapshot (T_obs = {decoupling})',
                         color='#00cc66', fontsize=9, fontfamily='monospace')
    else:
        ax_cmb.set_title(f'CMB Horizon Snapshot (T_obs = {decoupling})',
                         color='#335577', fontsize=9, fontfamily='monospace')
        ax_cmb.text(0.5, 0.5, f'Wacht op cyclus {decoupling}...',
                    ha='center', va='center', color='#335577',
                    transform=ax_cmb.transAxes, fontfamily='monospace', fontsize=9)

    # Systeembetrouwbaarheid en Historiek
    if len(history) > 2:
        cycles = [h['cycle'] for h in history]
        ax_hist.plot(cycles, [h['avg_sigma'] for h in history],
                     color='#00aaff', lw=1.5, label='Gemiddelde σ')
        ax_hist.plot(cycles, [h['avg_teff']/CFG["W_MAX"] for h in history],
                     color='#ffcc00', lw=1.5, label='T_eff / W_max Ratio')
        ax_hist.plot(cycles, [h['sat_frac'] for h in history],
                     color='#ff4422', lw=1.5, label='Saturatiefractie (Zwarte Gaten)')
        ax_hist.axvline(x=decoupling, color='#00ff88', lw=1,
                        linestyle='--', alpha=0.6, label='Ontkoppelingsdrempel')
        ax_hist.legend(loc='upper right', fontsize=7,
                       facecolor='#050a14', labelcolor='white')
        ax_hist.set_title('Systeemmetrieken over de Tijd', color='#88bbff',
                          fontsize=9, fontfamily='monospace')
        ax_hist.set_xlabel('Matrix Cyclus (T_obs)', color='#4466aa', fontsize=8)
        ax_hist.set_ylim(0, 1)

    # Radiaal Vermogensspectrum vs Observatiedata
    if power is not None:
        halfN = G // 2
        k_arr = np.arange(1, halfN)
        l_titk = k_arr * (2500 / halfN)

        p = power[1:halfN]
        p_smooth = np.convolve(p, np.ones(5)/5, mode='same')
        p_norm = p_smooth / (p_smooth.max() + 1e-10)

        ax_spec.plot(l_titk, p_norm, color='#00e5ff', lw=2, label='TITK Simulatie')

        l_ref, spec_ref = get_planck_reference()
        spec_norm = spec_ref / spec_ref.max()
        ax_spec.plot(l_ref, spec_norm, color='#ffcc00', lw=1,
                     linestyle='--', alpha=0.6, label='Planck Referentie')

        # Akoestische Piekindicatoren (Schaalinvariantietoets)
        for l_peak, label in [(200, 'ℓ₁'), (540, 'ℓ₂'), (810, 'ℓ₃')]:
            ax_spec.axvline(x=l_peak, color='#ffcc00', lw=0.8,
                            linestyle=':', alpha=0.4)
            ax_spec.text(l_peak+20, 0.95, label, color='#ffcc00',
                         fontsize=7, fontfamily='monospace')

        ax_spec.set_xlim(0, 2000)
        ax_spec.set_ylim(0, 1.1)
        ax_spec.set_xlabel('Multipool Moment (ℓ)', color='#4466aa', fontsize=8)
        ax_spec.legend(loc='upper right', fontsize=7,
                       facecolor='#050a14', labelcolor='white')
        ax_spec.set_title('Vermogensspectrum vs Observatiedata',
                          color='#88bbff', fontsize=9, fontfamily='monospace')
    else:
        ax_spec.text(0.5, 0.5, f'Berekening start bij T_obs = {decoupling}',
                     ha='center', va='center', color='#335577',
                     transform=ax_spec.transAxes,
                     fontfamily='monospace', fontsize=9)
        ax_spec.set_title('Vermogensspectrum vs Observatiedata',
                          color='#335577', fontsize=9, fontfamily='monospace')

    return fig


# ─── EXECUTION CONTEXT ────────────────────────────────────────
def run():
    G = CFG["GRID"]
    radius = max(2, int(CFG["C_RADIUS"] * G))

    print(f"\n[START] TITK Cosmology Engine — Execution Initialized")
    print(f"Grid Resolutie: {G}×{G} ({G*G:} actieve ruimtetijd-actors)")
    print(f"Topologische Connectiviteitsradius: {radius}")
    print(f"Ontkoppelingsmatrix gepland op T_obs = {CFG['DECOUPLING']}")
    print("=" * 65)

    print("Genereren primordiaal ruisveld (Harrison-Zel'dovich spectrum)...")
    sigma = make_primordial_field(G, CFG["NOISE_AMP"])
    saturated = np.zeros((G, G), dtype=bool)

    cmb_snapshot = None
    power_spectrum = None
    history = []

    os.makedirs("titk_output", exist_ok=True)
    t_start = time.time()

    for cycle in range(1, CFG["TOTAL_CYCLES"] + 1):

        sigma, saturated, t_eff, phi_ext, stats = simulation_step(
            sigma, saturated, cycle, G, radius, CFG
        )
        stats["cycle"] = cycle
        history.append(stats)

        # Triggerschot voor de Kosmische Achtergrondstraling
        if cycle == CFG["DECOUPLING"]:
            cmb_snapshot = sigma.copy()
            print(f"\n[HORIZON SNAPSHOT] T_obs = {cycle} bereikt.")
            power_spectrum, _ = compute_power_spectrum(cmb_snapshot)
            np.save("titk_output/cmb_snapshot.npy", cmb_snapshot)
            np.save("titk_output/power_spectrum.npy", power_spectrum)
            print(f" -> Tweedimensionale FFT succesvol berekend over het grid.")

        # Real-time Telemetrie-output
        if cycle % CFG["OUTPUT_INTERVAL"] == 0 or cycle == 1:
            elapsed = time.time() - t_start
            eta = elapsed / cycle * (CFG["TOTAL_CYCLES"] - cycle)
            print(f"Cyclus {cycle:4d}/{CFG['TOTAL_CYCLES']} | "
                  f"Fase: {stats['phase']:12s} | "
                  f"avg_σ: {stats['avg_sigma']:.4f} | "
                  f"avg_Teff: {stats['avg_teff']:5.1f} | "
                  f"Saturatie: {stats['sat_frac']*100:.1f}% | "
                  f"ETA: {eta:.0f}s")

        if CFG["SAVE_SNAPSHOTS"] and cycle % 100 == 0:
            np.save(f"titk_output/sigma_cycle_{cycle:04d}.npy", sigma)

    total_time = time.time() - t_start
    print(f"\n[COMPLETED] Engine-run succesvol afgerond in {total_time:.1f}s")
    print(f"Binaire matrix-toestanden weggeschreven naar ./titk_output/")

    print("Grafische componenten renderen...")
    fig = make_figure(sigma, cmb_snapshot, t_eff, history,
                      power_spectrum, G, CFG["DECOUPLING"])
    fig.savefig("titk_output/titk_result.png", dpi=150,
                bbox_inches='tight', facecolor='#020810')
    print("Analyse-figuur opgeslagen: titk_output/titk_result.png")

    # Toetsing van de Multipool-piekverhoudingen (Sectie 7.5 Predictie)
    if power_spectrum is not None:
        print("\n── VERMOGENSSPECTRUM QUANTITATIEVE EVALUATIE ──")
        halfN = G // 2
        k_arr = np.arange(1, halfN)
        l_arr = k_arr * (2500 / halfN)
        p = power_spectrum[1:halfN]
        p_smooth = np.convolve(p, np.ones(5)/5, mode='same')

        from scipy.signal import find_peaks
        peaks, props = find_peaks(p_smooth, height=p_smooth.max()*0.1,
                                  distance=10)
        if len(peaks) > 0:
            print(f"Gedetecteerde matrix-pieken op ℓ ≈ {[int(l_arr[p]) for p in peaks[:5]]}")
            print(f"Planck Observatiedoelen:      ℓ ≈ [200, 540, 810]")
            if len(peaks) >= 2:
                ratio_titk = l_arr[peaks[1]] / l_arr[peaks[0]]
                ratio_planck = 540 / 200  # Standaard Akoestische Verhouding = 2.70
                print(f"\nAkoestische Piekverhouding (ℓ₂ / ℓ₁):")
                print(f"  TITK Engine:      {ratio_titk:.2f}")
                print(f"  Planck Baseline:  {ratio_planck:.2f}")
                match = abs(ratio_titk - ratio_planck) / ratio_planck < 0.15
                print(f"  Kwantitatieve Match (Marge ±15%): {'✓ BEVESTIGD' if match else '✗ AFGEWEZEN'}")
        else:
            print("Geen statistisch significante pieken gedetecteerd.")
            print("Advies: Verhoog GRID-resolutie of kalibreer K_FACTOR / Q_MAX verhouding.")

    plt.show()


if __name__ == "__main__":
    run()
