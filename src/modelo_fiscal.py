"""Modelo fiscal simplificado del TP de Visualización (IRPF + Seguridad Social, 2015-2025).

Supuestos (ver claude/TP_supuestos_modelo_fiscal.md): asalariado del régimen general,
contrato indefinido, sin otras rentas ni deducciones. Escala autonómica = estatal
(escala consolidada = 2 x estatal). Familia: matrimonio con 2 hijos menores de 3 años
o más (sin el adicional por menores de 3).

Uso:  python3 -I modelo_fiscal.py --test
      python3 -I modelo_fiscal.py SALARIOS.csv IPC.csv SALIDA.csv
"""
import csv
import collections
import sys

# ----------------------------------------------------------------------------
# Parámetros por año
# ----------------------------------------------------------------------------
TIPOS_ESTATAL = [9.5, 12.0, 15.0, 18.5, 22.5, 24.5]  # %, la consolidada es el doble

BASE_MAX_MENSUAL = {
    2015: 3606.0, 2016: 3642.0, 2017: 3751.2, 2018: 3751.2,
    2019: 4070.1, 2020: 4070.1, 2021: 4070.1,
    2022: 4139.4,  # por confirmar
    2023: 4495.5, 2024: 4720.5, 2025: 4909.5,
}
MEI_TRABAJADOR = {2023: 0.10, 2024: 0.12, 2025: 0.13}  # %, antes de 2023 no existía

MINIMO_CONTRIBUYENTE = 5550.0
MINIMO_DESCENDIENTES = 2400.0 + 2700.0     # 1.º y 2.º hijo
GASTOS_OTROS = 2000.0                      # art. 19.2.f) LIRPF (por confirmar)
REDUCCION_CONJUNTA = 3400.0                # matrimonio

AÑOS = list(range(2015, 2026))
AÑO_BASE_INDEXACION = 2016


def umbrales_escala(y):
    if y == 2015:
        return [0, 12450, 20200, 34000, 60000]
    if y <= 2020:
        return [0, 12450, 20200, 35200, 60000]
    return [0, 12450, 20200, 35200, 60000, 300000]


def escala_estatal(x, y, f=1.0):
    """Cuota estatal de la escala general para una base x (umbrales x f)."""
    thr = [t * f for t in umbrales_escala(y)]
    tipos = TIPOS_ESTATAL[:len(thr)]
    cuota = 0.0
    for i, t in enumerate(thr):
        techo = thr[i + 1] if i + 1 < len(thr) else float("inf")
        if x > t:
            cuota += (min(x, techo) - t) * tipos[i] / 100.0
    return cuota


def tipo_ss(y):
    return 4.70 + 1.55 + 0.10 + MEI_TRABAJADOR.get(y, 0.0)


def cotizacion_ss(bruto, y):
    base = min(bruto, BASE_MAX_MENSUAL[y] * 12)
    return base * tipo_ss(y) / 100.0


def _red(rn, regimen):
    if regimen == "2015":
        if rn <= 11250:
            return 3700.0
        if rn <= 14450:
            return max(0.0, 3700.0 - 1.15625 * (rn - 11250))
        return 0.0
    if regimen == "2019":
        if rn <= 13115:
            return 5565.0
        if rn <= 16825:
            return max(0.0, 5565.0 - 1.5 * (rn - 13115))
        return 0.0
    if regimen == "2023":
        if rn <= 14047.5:
            return 6498.0
        if rn <= 19747.5:
            return max(0.0, 6498.0 - 1.14 * (rn - 14047.5))
        return 0.0
    if regimen == "2024":
        if rn <= 14852:
            return 7302.0
        if rn <= 17673.52:
            return 7302.0 - 1.75 * (rn - 14852)
        if rn <= 19747.5:
            return max(0.0, 2364.34 - 1.14 * (rn - 17673.52))
        return 0.0
    raise ValueError(regimen)


def reduccion_trabajo(rn_previo, y):
    """rn_previo = ingresos - gastos a)-e) del art. 19.2 (la SS), sin los 2.000 de la letra f)."""
    if y <= 2017:
        return _red(rn_previo, "2015")
    if y == 2018:   # año de transición: aproximación = media de ambas reglas
        return 0.5 * (_red(rn_previo, "2015") + _red(rn_previo, "2019"))
    if y <= 2022:
        return _red(rn_previo, "2019")
    if y == 2023:
        return _red(rn_previo, "2023")
    return _red(rn_previo, "2024")


# ----------------------------------------------------------------------------
# Cálculo del IRPF
# ----------------------------------------------------------------------------
def rendimiento_neto(bruto, y, f=1.0):
    ss = cotizacion_ss(bruto, y)
    previo = bruto - ss
    red = reduccion_trabajo(previo, y)          # la reducción NO se indexa (la legisló el Gobierno)
    return max(0.0, previo - GASTOS_OTROS * f - red), ss


def cuota_desde_base(bl, minimo, y, f=1.0):
    return max(0.0, 2.0 * (escala_estatal(bl, y, f) - escala_estatal(minimo, y, f)))


def irpf_individual(bruto, y, minimo_hijos=0.0, f=1.0):
    rn, ss = rendimiento_neto(bruto, y, f)
    minimo = (MINIMO_CONTRIBUYENTE + minimo_hijos) * f
    return cuota_desde_base(rn, minimo, y, f), ss


def irpf_conjunta(brutos, y, minimo_hijos, f=1.0):
    rn_total, ss_total = 0.0, 0.0
    for b in brutos:
        rn, ss = rendimiento_neto(b, y, f)
        rn_total += rn
        ss_total += ss
    bl = max(0.0, rn_total - REDUCCION_CONJUNTA * f)
    minimo = (MINIMO_CONTRIBUYENTE + minimo_hijos) * f   # el mínimo del contribuyente cuenta una vez
    return cuota_desde_base(bl, minimo, y, f), ss_total


def familia(brutos, y, f=1.0):
    """Mejor de individual (hijos al 50 %) y conjunta."""
    mitad = MINIMO_DESCENDIENTES / 2.0
    ind, ss_i = 0.0, 0.0
    for b in brutos:
        c, s = irpf_individual(b, y, minimo_hijos=mitad, f=f)
        ind += c
        ss_i += s
    conj, ss_c = irpf_conjunta(brutos, y, MINIMO_DESCENDIENTES, f)
    if conj < ind:
        return conj, ss_c, "conjunta", ind, conj
    return ind, ss_i, "individual", ind, conj


# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
def _num(s):
    return float(s.replace(".", "").replace(",", "."))


def cargar_salarios(path):
    d = {}
    with open(path, encoding="latin-1") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if r["Comunidades autónomas"] == "Total Nacional" and r["Sexo"] == "Ambos sexos":
                d[(r["Medidas y percentiles"], int(r["Periodo"]))] = _num(r["Total"])
    return d


def cargar_ipc_medio(path):
    m = collections.defaultdict(list)
    with open(path, encoding="latin-1") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if r["Comunidades y Ciudades Autónomas"] == "Nacional" and r["Tipo de dato"] == "Índice":
                m[int(r["Periodo"][:4])].append(_num(r["Total"]))
    return {y: sum(v) / len(v) for y, v in m.items() if len(v) == 12}


def factor(y, ipc):
    if y < AÑO_BASE_INDEXACION:
        return 1.0
    return ipc[y] / ipc[AÑO_BASE_INDEXACION]


def calcular(path_salarios, path_ipc):
    sal = cargar_salarios(path_salarios)
    ipc = cargar_ipc_medio(path_ipc)
    filas = []
    for y in AÑOS:
        if ("Media", y) not in sal:      # los salarios del INE llegan hasta 2024
            continue
        media, mediana = sal[("Media", y)], sal[("Mediana", y)]
        f = factor(y, ipc)
        for perfil, brutos in (("media_individual", [media]),
                               ("mediana_individual", [mediana]),
                               ("familia_media_mas_mediana", [media, mediana])):
            if perfil.startswith("familia"):
                real, ss, mod, _, _ = familia(brutos, y, 1.0)
                idx, _, mod_idx, _, _ = familia(brutos, y, f)
            else:
                real, ss = irpf_individual(brutos[0], y, 0.0, 1.0)
                idx, _ = irpf_individual(brutos[0], y, 0.0, f)
                mod = mod_idx = "individual"
            bruto = sum(brutos)
            filas.append({
                "anio": y, "perfil": perfil, "bruto": round(bruto, 2),
                "ss_trabajador": round(ss, 2), "irpf_real": round(real, 2),
                "irpf_tarifa_indexada_ipc": round(idx, 2),
                "diferencia": round(real - idx, 2),
                "tipo_irpf_real_pct": round(100 * real / bruto, 2),
                "tipo_irpf_indexado_pct": round(100 * idx / bruto, 2),
                "neto": round(bruto - ss - real, 2),
                "modalidad_real": mod, "modalidad_indexada": mod_idx,
                "factor_ipc_vs_2016": round(f, 4),
            })
    return filas


# ----------------------------------------------------------------------------
# Pruebas con cálculos hechos a mano
# ----------------------------------------------------------------------------
def _casi(a, b, tol=0.01):
    return abs(a - b) <= tol


def pruebas():
    ok = True

    def check(nombre, obtenido, esperado, tol=0.01):
        nonlocal ok
        bien = _casi(obtenido, esperado, tol)
        ok &= bien
        print(("OK  " if bien else "FALLA"), nombre, round(obtenido, 4), "esperado", esperado)

    # 1) soltero 30.000 € en 2024 (cálculo manual)
    #    SS = 30.000 x 6,47 % = 1.941 ; RN previo = 28.059 ; sin reducción ;
    #    RN = 28.059 - 2.000 = 26.059 ; estatal = 2.112,75 + (26.059-20.200) x 15 % = 2.991,60
    #    gravamen del mínimo (5.550) = 527,25 ; cuota = 2 x (2.991,60 - 527,25) = 4.928,70
    c, ss = irpf_individual(30000, 2024)
    check("SS 30.000 € (2024)", ss, 1941.0)
    check("IRPF soltero 30.000 € (2024)", c, 4928.70)

    # 2) SMI 2024 (15.876 €): queda exento
    c, _ = irpf_individual(15876, 2024)
    check("IRPF con SMI 2024", c, 0.0)

    # 3) SMI 2023 (15.120 €): paga una cuota pequeña
    #    SS = 15.120 x 6,45 % = 975,24 ; previo = 14.144,76 ; red = 6.498 - 1,14 x 97,26 = 6.387,12
    #    RN = 14.144,76 - 2.000 - 6.387,12 = 5.757,64 ; cuota = 2 x (5.757,64-5.550) x 9,5 % = 39,45
    c, _ = irpf_individual(15120, 2023)
    check("IRPF con SMI 2023", c, 39.45, 0.05)

    # 4) escala estatal 2025 para 60.000 € de base (umbrales 12.450 / 20.200 / 35.200 / 60.000)
    #    12.450 x 9,5 % + 7.750 x 12 % + 15.000 x 15 % + 24.800 x 18,5 % = 8.950,75
    check("Escala estatal 60.000 (2025)", escala_estatal(60000, 2025), 8950.75)

    # 5) la reducción es continua en los cortes
    check("Reducción 2024 en 17.673,52", _red(17673.52, "2024"), 2364.34, 0.01)
    check("Reducción 2023 en 14.047,5", _red(14047.5, "2023"), 6498.0)

    # 6) más ingresos -> nunca menos neto (monotonía)
    prev = -1.0
    mono = True
    for b in range(10000, 80001, 500):
        cuota, ss = irpf_individual(b, 2024)
        neto = b - cuota - ss
        if neto < prev:
            mono = False
        prev = neto
    print("OK  " if mono else "FALLA", "monotonía del neto (2024)")
    ok &= mono

    print("\nTODAS LAS PRUEBAS OK" if ok else "\nHAY PRUEBAS QUE FALLAN")
    return ok


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        sys.exit(0 if pruebas() else 1)
    if len(sys.argv) == 4:
        filas = calcular(sys.argv[1], sys.argv[2])
        with open(sys.argv[3], "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(filas)
        print("Escrito", sys.argv[3], len(filas), "filas")
    else:
        print(__doc__)
