#!/usr/bin/env python3
"""
TITK Simulatie v1.5 — Python/NumPy versie
Topologische Informatietheorie van de Kosmos

Vereisten: pip install numpy scipy matplotlib
Gebruik: python3 titk_sim.py
"""

import numpy as np
from scipy.fft import fft2, fftshift, ifft2
from scipy.ndimage import uniform_filter
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import time
import os

# ─── CONFIGURATIE ─────────────────────────────────────────────
CFG = {
    "GRID":             512,    # Gridgrootte (macht van 2)
    "Q_MAX":            66,     # Max queue depth (zwart gat drempel)
    "W_MAX":            100.0,  # Vast budget — nooit overschreden
    "K_FACTOR":         1,    # Interne kostenvermenigvuldiger
    "C_RADIUS":         0.07 ,  # Verbindingsradius (genormaliseerd)
    "NOISE_AMP":        0.05,   # Primordiaal ruisamplitude
    "BACKPRESSURE":     0.01,   # Terugkoppelingssterkte van verzadigde nodes
    "PLASMA_EXPANSION": 0.006,  # Expansiesnelheid plasma-era
    "DECOUPLING":       380,    # Ontkoppelingsmoment (CMB snapshot)
    "TOTAL_CYCLES":     500,    # Totaal aantal cycli
    "OUTPUT_INTERVAL":  20,     # Print statistieken elke N cycli
    "MONITOR_INTERVAL": 50,     # Monitor output interval
    "SAVE_SNAPSHOTS":   True,   # Sla tussentijdse snapshots op
}

start_time = time.time()

# ─── FOURIER INITIALISATIE (Harrison-Zel'dovich P(k) ∝ k) ─────
def make_primordial_field(G, noise_amp):
    """
    Genereert initieel veld direct in Fourier-ruimte.
    Harrison-Zel'dovich spectrum: P(k) ∝ k → amplitude ∝ sqrt(k)
    Geen grote zaaikernens — energie gelijkmatig verdeeld over alle schalen.
    """
    print("  Fourier-initialisatie (Harrison-Zel'dovich P(k) ∝ k)...")
    N = G
    # Bouw amplitude spectrum op in k-ruimte
    F = np.zeros((N, N), dtype=complex)
    ky_arr = np.fft.fftfreq(N) * N   # [-N/2, N/2)
    kx_arr = np.fft.fftfreq(N) * N
    KX, KY = np.meshgrid(kx_arr, ky_arr)
    K = np.sqrt(KX**2 + KY**2)
    K[0, 0] = 1  # Vermijd deling door nul voor k=0

    # Harrison-Zel'dovich: amplitude ∝ sqrt(k)
    amplitude = np.sqrt(K) * noise_amp
    amplitude[0, 0] = 0  # DC component = 0 (geen gemiddeld offset)

    # Willekeurige fasen voor isotropie
    phases = np.random.uniform(0, 2*np.pi, (N, N))
    F = amplitude * np.exp(1j * phases)

    # Herstel Hermitische symmetrie zodat ifft reëel is
    field_complex = np.fft.ifft2(F)
    field = np.real(field_complex)

    # Normaliseer naar [0, 1]
    field = (field - field.min()) / (field.max() - field.min() + 1e-10)

    print(f"  Veld klaar: mean={field.mean():.4f}, std={field.std():.4f}")
    return field.astype(np.float32)


# ─── MONITOR ──────────────────────────────────────────────────
def run_monitor(stats, cycle, cfg):
    """Monitor output — gebruikt uitsluitend CFG voor consistentie."""
    if cycle % cfg["MONITOR_INTERVAL"] != 0:
        return

    sat_frac  = stats.get('sat_frac', 0)
    avg_teff  = stats.get('avg_teff', 0)
    avg_phi   = stats.get('avg_phi', 0)
    G         = cfg["GRID"]
    num_nodes = G * G

    # Backlog via CFG["Q_MAX"] — niet een losse variabele
    total_queue = int(avg_teff / (cfg["W_MAX"] / cfg["Q_MAX"]) * num_nodes)
    efficiency  = avg_phi / (avg_teff + 1e-9)
    elapsed     = time.time() - start_time

    if sat_frac > 0.90:
        status = "CRITICAL (Faseovergang?)"
    elif sat_frac > 0.70:
        status = "WANKEL"
    elif sat_frac > 0.30:
        status = "ACTIEF"
    else:
        status = "STABIEL"

    print(f"[Iter {cycle:5d}] | T: {elapsed:6.2f}s | "
          f"Sat: {sat_frac:5.2%} | Eff: {efficiency:5.3f} | "
          f"Backlog: {total_queue:10d} | STATUS: {status}")


# ─── SIMULATIESTAP ────────────────────────────────────────────
def simulation_step(sigma, saturated, cycle, G, radius, cfg):
    """
    Eén TITK-cyclus. Volledig NumPy-gevectoriseerd.
    T_eff wordt elke cycle opnieuw berekend — geen accumulatie.
    Saturatie is reversibel — nodes kunnen desatureren.
    """
    W_MAX    = cfg["W_MAX"]
    K_FACTOR = cfg["K_FACTOR"]
    Q_MAX    = cfg["Q_MAX"]

    # ── Fase & expansie ───────────────────────────────────────
    if cycle < 20:
        phase, expansion = "singularity", 0.0
    elif cycle < 80:
        phase, expansion = "inflation", 0.08
    elif cycle < cfg["DECOUPLING"]:
        phase, expansion = "plasma", cfg["PLASMA_EXPANSION"]
    elif cycle == cfg["DECOUPLING"]:
        phase, expansion = "decoupling", cfg["PLASMA_EXPANSION"]
    else:
        phase, expansion = "cmb", 0.002

    # ── Buurgemiddelde ────────────────────────────────────────
    filter_size    = radius * 2 + 1
    neighbor_sum   = uniform_filter(sigma, size=filter_size, mode='wrap') * filter_size**2
    neighbor_count = filter_size**2 - 1
    neighbor_avg   = (neighbor_sum - sigma) / neighbor_count
    I_conn         = neighbor_count

    # ── T_eff (elke cycle opnieuw — geen accumulatie) ─────────
    delta      = np.abs(sigma - neighbor_avg)
    base_cost  = K_FACTOR * delta * max(1, I_conn * 0.3)
#      dens_boost = sigma * I_conn * 0.5
    dens_boost = sigma * min(I_conn, 10) * 0.05  # begrensd

    t_eff      = np.clip(base_cost + dens_boost, 0, W_MAX)

    # ── Backpressure van verzadigde buren ─────────────────────
    sat_neighbors = (uniform_filter(
        saturated.astype(np.float32), size=filter_size, mode='wrap'
    ) * filter_size**2)
    backpressure = sat_neighbors * (W_MAX / Q_MAX) * cfg["BACKPRESSURE"]
    t_eff = np.clip(t_eff + backpressure, 0, W_MAX)

    # ── Saturatie (reversibel) ────────────────────────────────
    # Zwart gat definitie: queue_depth >= Q_MAX OF t_eff >= W_MAX
    queue_depth   = (t_eff / (W_MAX / Q_MAX)).astype(int)
    new_saturated = (queue_depth >= Q_MAX) | (t_eff >= W_MAX)
    # Reversibel: node kan desatureren als t_eff daalt
    # (geen | met oude saturated — elke cycle opnieuw bepaald)
    phi_ext = np.where(new_saturated, 0.0, np.maximum(0, W_MAX - t_eff))

    # ── Sigma publiceren ──────────────────────────────────────
    sigma_int = neighbor_avg.copy()
    sigma_new = sigma.copy()
    active    = ~new_saturated

    sigma_new[active] = (sigma[active] * (1 - expansion) +
                         sigma_int[active] * expansion)

    # Kleine kwantumperturbatie (niet destructief)
    noise_mask  = np.random.random((G, G)) < 0.005
    sigma_new  += np.where(noise_mask & active,
                           np.random.normal(0, 0.02, (G, G)), 0)
    sigma_new   = np.clip(sigma_new, 0, 1)

    stats = {
        "phase":     phase,
        "sat_frac":  new_saturated.mean(),
        "avg_sigma": sigma_new.mean(),
        "avg_teff":  t_eff.mean(),
        "avg_phi":   phi_ext.mean(),
    }
    return sigma_new, new_saturated, t_eff, phi_ext, stats


# ─── POWER SPECTRUM ───────────────────────────────────────────
def compute_power_spectrum(field):
    """2D FFT → radiaal gemiddeld power spectrum. Gemiddelde afgetrokken."""
    f      = field - field.mean()
    F      = fftshift(fft2(f))
    power2d = np.abs(F)**2 / (f.size**2)

    N    = field.shape[0]
    halfN = N // 2
    cy, cx = N//2, N//2

    y_idx, x_idx = np.mgrid[0:N, 0:N]
    k_map = np.round(np.sqrt((x_idx-cx)**2 + (y_idx-cy)**2)).astype(int)

    power  = np.zeros(halfN)
    counts = np.zeros(halfN)
    for k in range(1, halfN):
        mask = k_map == k
        if mask.any():
            power[k]  = power2d[mask].mean()
            counts[k] = mask.sum()
    return power, counts


# ─── PLANCK REFERENTIE ────────────────────────────────────────
def get_planck_reference():
    l = np.arange(2, 2500)
    spectrum = (
        1000 / l**0.1 *
        (1 + 2.5 * np.exp(-((l-200)/60)**2) +
             1.4 * np.exp(-((l-540)/80)**2) +
             0.8 * np.exp(-((l-810)/90)**2)) *
        np.exp(-l**2 / (2*2500**2))
    )
    return l, spectrum


# ─── VISUALISATIE ─────────────────────────────────────────────
def make_figure(sigma, cmb_snapshot, t_eff, history, power, cfg):
    G          = cfg["GRID"]
    decoupling = cfg["DECOUPLING"]

    fig = plt.figure(figsize=(16, 10), facecolor='#020810')
    fig.suptitle(f'TITK v1.5 — Big Bang Simulatie ({G}×{G})',
                 color='#c8d8f0', fontsize=14, fontfamily='monospace')

    gs = gridspec.GridSpec(2, 3, figure=fig,
                           hspace=0.35, wspace=0.3,
                           left=0.06, right=0.97, top=0.92, bottom=0.08)

    ax_live = fig.add_subplot(gs[0, 0])
    ax_teff = fig.add_subplot(gs[0, 1])
    ax_cmb  = fig.add_subplot(gs[0, 2])
    ax_hist = fig.add_subplot(gs[1, 0:2])
    ax_spec = fig.add_subplot(gs[1, 2])

    for ax in [ax_live, ax_teff, ax_cmb, ax_hist, ax_spec]:
        ax.set_facecolor('#050a14')
        ax.tick_params(colors='#4466aa', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#1a2a3a')

    ax_live.imshow(sigma, cmap='Blues_r', vmin=0, vmax=1, origin='lower')
    ax_live.set_title('Informatiedichtheid (σ)', color='#88bbff',
                      fontsize=9, fontfamily='monospace')

    ax_teff.imshow(t_eff, cmap='hot', vmin=0, vmax=cfg["W_MAX"], origin='lower')
    ax_teff.set_title('Tijddilatatie (T_eff)', color='#ffcc44',
                      fontsize=9, fontfamily='monospace')

    if cmb_snapshot is not None:
        ax_cmb.imshow(cmb_snapshot, cmap='RdYlBu_r', origin='lower')
        ax_cmb.set_title(f'CMB Snapshot (cycle {decoupling})',
                         color='#00cc66', fontsize=9, fontfamily='monospace')
    else:
        ax_cmb.set_title(f'CMB Snapshot — wacht op cycle {decoupling}',
                         color='#335577', fontsize=9, fontfamily='monospace')

    if len(history) > 2:
        cycles = [h['cycle'] for h in history]
        ax_hist.plot(cycles, [h['avg_sigma'] for h in history],
                     color='#00aaff', lw=1.5, label='avg σ')
        ax_hist.plot(cycles, [h['avg_teff']/cfg["W_MAX"] for h in history],
                     color='#ffcc00', lw=1.5, label='T_eff/W_max')
        ax_hist.plot(cycles, [h['sat_frac'] for h in history],
                     color='#ff4422', lw=1.5, label='zwarte gaten %')
        ax_hist.axvline(x=decoupling, color='#00ff88', lw=1,
                        linestyle='--', alpha=0.6, label='CMB')
        ax_hist.legend(loc='upper right', fontsize=7,
                       facecolor='#050a14', labelcolor='white')
        ax_hist.set_title('Historiek', color='#88bbff',
                          fontsize=9, fontfamily='monospace')
        ax_hist.set_xlabel('Cycle', color='#4466aa', fontsize=8)
        ax_hist.set_ylim(0, 1)

    if power is not None:
        halfN  = G // 2
        k_arr  = np.arange(1, halfN)
        l_titk = k_arr * (2500 / halfN)
        p      = power[1:halfN]
        p_smooth = np.convolve(p, np.ones(7)/7, mode='same')
        p_norm   = p_smooth / (p_smooth.max() + 1e-10)

        ax_spec.plot(l_titk, p_norm, color='#00e5ff', lw=2, label='TITK')

        l_ref, spec_ref = get_planck_reference()
        ax_spec.plot(l_ref, spec_ref/spec_ref.max(), color='#ffcc00',
                     lw=1, linestyle='--', alpha=0.6, label='Planck ref')

        for l_peak, lbl in [(200, 'ℓ₁'), (540, 'ℓ₂'), (810, 'ℓ₃')]:
            ax_spec.axvline(x=l_peak, color='#ffcc00', lw=0.8,
                            linestyle=':', alpha=0.4)
            ax_spec.text(l_peak+20, 0.95, lbl, color='#ffcc00',
                         fontsize=7, fontfamily='monospace')

        ax_spec.set_xlim(0, 2000)
        ax_spec.set_ylim(0, 1.1)
        ax_spec.set_xlabel('Multipool moment ℓ', color='#4466aa', fontsize=8)
        ax_spec.legend(loc='upper right', fontsize=7,
                       facecolor='#050a14', labelcolor='white')
        ax_spec.set_title('Power Spectrum vs Planck',
                          color='#88bbff', fontsize=9, fontfamily='monospace')
    return fig


# ─── HOOFDSIMULATIE ───────────────────────────────────────────
def run():
    G      = CFG["GRID"]
    radius = max(2, int(CFG["C_RADIUS"] * G))

    print(f"\nTITK v1.5 — Python/NumPy Simulatie")
    print(f"Grid: {G}×{G} = {G*G:,} nodes | Radius: {radius} | "
          f"Q_MAX: {CFG['Q_MAX']} | W_MAX: {CFG['W_MAX']}")
    print(f"Ontkoppeling: cycle {CFG['DECOUPLING']} / {CFG['TOTAL_CYCLES']}")
    print("=" * 60)

    sigma     = make_primordial_field(G, CFG["NOISE_AMP"])
    saturated = np.zeros((G, G), dtype=bool)

    cmb_snapshot   = None
    power_spectrum = None
    history        = []

    os.makedirs("titk_output", exist_ok=True)
    t_start = time.time()

    for cycle in range(1, CFG["TOTAL_CYCLES"] + 1):

        sigma, saturated, t_eff, phi_ext, stats = simulation_step(
            sigma, saturated, cycle, G, radius, CFG
        )
        stats["cycle"] = cycle
        history.append(stats)

        # Monitor
        run_monitor(stats, cycle, CFG)

        # CMB snapshot
        if cycle == CFG["DECOUPLING"]:
            cmb_snapshot = sigma.copy()
            print(f"\n*** CMB SNAPSHOT op cycle {cycle} ***")
            power_spectrum, _ = compute_power_spectrum(cmb_snapshot)
            np.save("titk_output/cmb_snapshot.npy", cmb_snapshot)
            np.save("titk_output/power_spectrum.npy", power_spectrum)
            print(f"    Power spectrum berekend (scipy FFT, {G}×{G}).")

        # Statistieken
        if cycle % CFG["OUTPUT_INTERVAL"] == 0 or cycle == 1:
            elapsed = time.time() - t_start
            eta     = elapsed / cycle * (CFG["TOTAL_CYCLES"] - cycle)
            print(f"Cycle {cycle:4d}/{CFG['TOTAL_CYCLES']} | "
                  f"Fase: {stats['phase']:12s} | "
                  f"σ: {stats['avg_sigma']:.4f} | "
                  f"T_eff: {stats['avg_teff']:5.1f} | "
                  f"ZG: {stats['sat_frac']*100:.1f}% | "
                  f"ETA: {eta:.0f}s")

        if CFG["SAVE_SNAPSHOTS"] and cycle % 100 == 0:
            np.save(f"titk_output/sigma_cycle_{cycle:04d}.npy", sigma)

    total_time = time.time() - t_start
    print(f"\nSimulatie klaar in {total_time:.1f}s")

    # ── Figuur ────────────────────────────────────────────────
    fig = make_figure(sigma, cmb_snapshot, t_eff, history,
                      power_spectrum, CFG)
    fig.savefig("titk_output/titk_result.png", dpi=150,
                bbox_inches='tight', facecolor='#020810')
    print("Figuur: titk_output/titk_result.png")

    # ── Piekanalyse ───────────────────────────────────────────
    if power_spectrum is not None:
        print("\n── Power Spectrum Analyse ──────────────────────")
        halfN  = G // 2
        k_arr  = np.arange(1, halfN)
        l_arr  = k_arr * (2500 / halfN)
        p      = power_spectrum[1:halfN]
        p_smooth = np.convolve(p, np.ones(7)/7, mode='same')

        peaks, _ = find_peaks(p_smooth,
                              height=p_smooth.max() * 0.1,
                              distance=10)
        if len(peaks) > 0:
            print(f"Gevonden pieken op ℓ ≈ {[int(l_arr[pk]) for pk in peaks[:5]]}")
            print(f"Planck referentie:      ℓ ≈ [200, 540, 810]")
            if len(peaks) >= 2:
                ratio_titk   = l_arr[peaks[1]] / l_arr[peaks[0]]
                ratio_planck = 540 / 200
                match = abs(ratio_titk - ratio_planck) / ratio_planck < 0.15
                print(f"\nVerhouding eerste twee pieken:")
                print(f"  TITK:   {ratio_titk:.2f}")
                print(f"  Planck: {ratio_planck:.2f}")
                print(f"  Match (±15%): {'✓ JA' if match else '✗ NEE'}")
            if len(peaks) >= 3:
                ratio2 = l_arr[peaks[2]] / l_arr[peaks[0]]
                print(f"  Verhouding piek 1→3: TITK {ratio2:.2f} vs Planck 4.05")
        else:
            print("Geen pieken gevonden — probeer lagere K_FACTOR of Q_MAX.")

    plt.show()


if __name__ == "__main__":
    run()
