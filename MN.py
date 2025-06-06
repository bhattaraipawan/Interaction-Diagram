import numpy as np

# Mapping from bar size to diameter (inches) and area (in²)
BAR_PROPERTIES = {
    "#3": {"diameter": 0.375, "area": 0.11},
    "#4": {"diameter": 0.5,   "area": 0.20},
    "#5": {"diameter": 0.625, "area": 0.31},
    "#6": {"diameter": 0.75,  "area": 0.44},
    "#7": {"diameter": 0.875, "area": 0.60},
    "#8": {"diameter": 1.0,   "area": 0.79},
    "#9": {"diameter": 1.128, "area": 1.0},
    "#10": {"diameter": 1.27, "area": 1.27},
    "#11": {"diameter": 1.41, "area": 1.56},
}

def Interaction_Diagram(w, h, Ctt, Cbt, Tie_d, Top_bar_size, Bottom_bar_size, Nt, Nb, fc, fy):
    Dt = 0 if Nt == 0 else BAR_PROPERTIES[Top_bar_size]["diameter"]
    At = 0 if Nt == 0 else BAR_PROPERTIES[Top_bar_size]["area"]
    Db = 0 if Nb == 0 else BAR_PROPERTIES[Bottom_bar_size]["diameter"]
    Ab = 0 if Nb == 0 else BAR_PROPERTIES[Bottom_bar_size]["area"]
    Ast = Nt * At
    Asb = Nb * Ab
    y_top = Ctt + Tie_d + Dt / 2 if Nt > 0 else h / 2
    y_bottom = h - (Cbt + Tie_d + Db / 2) if Nb > 0 else h / 2

    if Nt > 0 or Nb > 0:
        if y_top >= y_bottom or y_top >= h / 2 or y_bottom <= h / 2:
            raise ValueError("Invalid bar placement: check clear covers and bar sizes")

    Ag = w * h
    Es = 29000
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
            return 0.65 + 0.25 * (eps_t - eps_y) / (0.005 - 0.002)

    def steel_stress(eps, adjust_concrete=False):
        stress = min(max(eps * Es, -fy), fy)
        if adjust_concrete:
            stress -= 0.85 * fc
            stress = min(max(stress, -fy), fy)
        return stress

    def compute_forces(c, adjust_top_steel=False):
        a = beta1 * c
        if a > h:
            a = h
        Cc = 0.85 * fc * w * a
        ygc = a / 2

        eps_s1 = eps_cu * (y_bottom-c) / c if c > 0 and Nb > 0 else 0   # Tension steel strain
        eps_s2 = eps_cu * (c - y_top) / c if c > 0 and Nt > 0 else 0    # Compression steel strain

        Cs1 = Asb * steel_stress(eps_s1)
        Cs2 = Ast * steel_stress(eps_s2, adjust_concrete=(adjust_top_steel and c >= y_top))

        Pn = Cc - Cs1 + Cs2
        Mn = (Cc * (h/2 - ygc) + Cs2 * (h/2 - y_top) + Cs1 * (y_bottom-h/2)) / 12
        phi = get_phi(eps_s1)

        return Pn, Mn, phi * Pn, phi * Mn, phi, eps_s1

    # Initialize lists for points
    Mrd, Nrd, Mn_list, Pn_list = [], [], [], []
    c_values = []
    key_indices = []

    # Point 1: Max Compression
    Ast_total = Ast + Asb
    Po = 0.85 * fc * (Ag - Ast_total) + fy * Ast_total
    Pn = 0.8 * Po  # ACI 318-19 factor for tied columns
    phi = 0.65
    Nrd.append(phi * Pn)
    Mrd.append(0.0)
    Pn_list.append(Pn)
    Mn_list.append(0.0)
    c_values.append(h)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between Max Compression and Bar Stress = 0
    c2 = y_bottom if Nb > 0 else h / 2
    c_intermediate = np.linspace(h, c2, 22)[1:-1]  # 20 points between c1 and c2
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 2: Bar Stress = 0 (tension rebar: es=0)
    Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c2, adjust_top_steel=True)
    Nrd.append(PhiPn)
    Mrd.append(PhiMn)
    Pn_list.append(Pn)
    Mn_list.append(Mn)
    c_values.append(c2)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between Bar Stress = 0 and fs = 0.5fy
    eps_s1 = 0.5 * eps_y
    c3 = (eps_cu * y_bottom) / (eps_cu + eps_s1) if Nb > 0 else h / 2
    c_intermediate = np.linspace(c2, c3, 22)[1:-1]
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 3: fs = 0.5fy
    Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c3, adjust_top_steel=True)
    Nrd.append(PhiPn)
    Mrd.append(PhiMn)
    Pn_list.append(Pn)
    Mn_list.append(Mn)
    c_values.append(c3)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between fs = 0.5fy and Balanced Failure
    eps_s1 = eps_y
    c4 = (eps_cu * y_bottom) / (eps_cu + eps_s1) if Nb > 0 else h / 2
    c_intermediate = np.linspace(c3, c4, 22)[1:-1]
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 4: Balanced Failure (fs = fy)
    Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c4, adjust_top_steel=True)
    Nrd.append(PhiPn)
    Mrd.append(PhiMn)
    Pn_list.append(Pn)
    Mn_list.append(Mn)
    c_values.append(c4)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between Balanced Failure and Tension-Controlled
    c5 = (eps_cu * y_bottom) / (eps_cu + eps_t_controlled) if Nb > 0 else h / 2
    c_intermediate = np.linspace(c4, c5, 22)[1:-1]
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 5: Tension controlled (eps = 0.00507)
    Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c5, adjust_top_steel=True)
    Nrd.append(PhiPn)
    Mrd.append(PhiMn)
    Pn_list.append(Pn)
    Mn_list.append(Mn)
    c_values.append(c5)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between Tension-Controlled and Pure Bending
    c_low, c_high = 0.1, h
    for _ in range(1000):
        c_mid = (c_low + c_high) / 2
        Pn, *_ = compute_forces(c_mid, adjust_top_steel=True)
        if abs(Pn) < 0.01:
            break
        if Pn > 0:
            c_high = c_mid
        else:
            c_low = c_mid
    c6 = c_mid
    c_intermediate = np.linspace(c5, c6, 22)[1:-1]
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 6: Pure bending (Pn = 0)
    Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c6, adjust_top_steel=True)
    Nrd.append(PhiPn)
    Mrd.append(PhiMn)
    Pn_list.append(Pn)
    Mn_list.append(Mn)
    c_values.append(c6)
    key_indices.append(len(Mrd) - 1)

    # Adding 20 points between Pure Bending and Max Tension
    c7 = 0.0
    c_intermediate = np.linspace(c6, c7, 22)[1:-1]
    for c in c_intermediate:
        Pn, Mn, PhiPn, PhiMn, _, _ = compute_forces(c, adjust_top_steel=True)
        Nrd.append(PhiPn)
        Mrd.append(PhiMn)
        Pn_list.append(Pn)
        Mn_list.append(Mn)

    # Point 7: Max tension
    Pn = -fy * (Ast + Asb)
    phi = 0.9
    PhiPn = phi * Pn
    Nrd.append(PhiPn)
    Mrd.append(0.0)
    Pn_list.append(Pn)
    Mn_list.append(0.0)
    c_values.append(c7)
    key_indices.append(len(Mrd) - 1)

    return (
        np.array(Mrd), 
        np.array(Nrd), 
        np.array(Mn_list), 
        np.array(Pn_list), 
        key_indices
    )
