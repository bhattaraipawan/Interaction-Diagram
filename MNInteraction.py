import numpy as np
import matplotlib.pyplot as plt

def Interaction_Diagram(w, h, ec, Ast, Asb, fc, fy):
    """
    Calculates key points for a tied rectangular column per ACI 318-19.

    Returns:
        Mrd, Nrd : 7 key points
    """

    # Material & section
    d = h - ec
    Ag = w * h
    Es = 29000  # ksi
    eps_cu = 0.003
    eps_y = fy / Es
    eps_t_controlled = eps_y + 0.003
    beta1 = 0.85 if fc <= 4 else max(0.65, 0.85 - 0.05 * (fc - 4))

    def get_phi(eps_t):
        if eps_t <= eps_y:
            return 0.65
        elif eps_t >= eps_t_controlled:
            return 0.90
        else:
            return 0.65 + (0.25 * (eps_t - eps_y) / 0.003)

    def steel_stress(eps, adjust_concrete=False):
        stress = min(max(eps * Es, -fy), fy)
        if adjust_concrete:
            stress -= 0.85 * fc
            stress = min(max(stress, -fy), fy)
        return stress

    def compute_forces(c, adjust_top_steel=False):
        a = beta1 * c
        if a > h:  # Limit a to section height
            a = h
        Cc = 0.85 * fc * w * a
        ygc = a / 2
        Mc = Cc * (h / 2 - ygc)

        eps_s1 = eps_cu * (d - c) / c if c > 0 else 0  # Bottom steel strain
        eps_s2 = eps_cu * (c - ec) / c if c > 0 else 0  # Top steel strain

        Cs1 = Asb * steel_stress(eps_s1)
        Cs2 = Ast * steel_stress(eps_s2, adjust_concrete=(adjust_top_steel and c >= ec))

        N = Cc - Cs1 + Cs2
        M = (Mc + Cs1 * (d - h / 2) + Cs2 * (h / 2 - ec)) / 12  # kip-ft
        phi = get_phi(eps_s1)
        return phi * N, phi * M, phi, eps_s1

    # Key ACI Points
    Mrd, Nrd = [], []

    # Point 1: Max Compression
    Po = 0.85 * fc * (Ag - Ast - Asb) + fy * (Ast + Asb)
    phi = 0.65
    Nrd.append(0.8 * phi * Po)
    Mrd.append(0.0)

    # Point 2: εs = 0 (tension rebar)
    c = d
    N, M, _, _ = compute_forces(c, adjust_top_steel=True)
    Nrd.append(N)
    Mrd.append(M)

    # Point 3: fs = 0.5fy
    eps_s1 = 0.5 * fy / Es
    c = d * eps_cu / (eps_cu + eps_s1)
    N, M, _, _ = compute_forces(c, adjust_top_steel=True)
    Nrd.append(N)
    Mrd.append(M)

    # Point 4: Balanced failure fs = fy
    eps_s1 = fy / Es
    c = d * eps_cu / (eps_cu + eps_s1)
    N, M, _, _ = compute_forces(c, adjust_top_steel=True)
    Nrd.append(N)
    Mrd.append(M)

    # Point 5: Tension controlled (eps = 0.00507)
    c = d * eps_cu / (eps_cu + eps_t_controlled)
    N, M, _, _ = compute_forces(c, adjust_top_steel=True)
    Nrd.append(N)
    Mrd.append(M)

    # Point 6: Pure bending (Pn = 0)
    c_low, c_high = 0.1, h
    for _ in range(100):
        c_mid = (c_low + c_high) / 2
        N, _, _, _ = compute_forces(c_mid, adjust_top_steel=True)
        if abs(N) < 0.01:
            break
        if N > 0:
            c_high = c_mid
        else:
            c_low = c_mid
    N, M, _, _ = compute_forces(c_mid, adjust_top_steel=True)
    Nrd.append(0.0)
    Mrd.append(M)

    # Point 7: Max tension
    N = -0.9 * fy * (Ast + Asb)
    Nrd.append(N)
    Mrd.append(0.0)

    return np.array(Mrd), np.array(Nrd)