#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weekend di gara in corso? Stampa "sigla=<SIGLA>" (formato di $GITHUB_OUTPUT) se adesso e' dentro la
finestra di cattura di un GP, altrimenti "sigla=". Lo usa la GitHub Action di questo repository.

Vale anche per i test (29/10), della stagione corrente e di quella dopo. Finestra: dal giorno PRIMA della data di inizio (le 16:00 UTC, cioe' giovedi' sera in Italia) al lunedi'
alle 06:00 UTC: copre tutto il weekend in ogni fuso, Australia e Americhe comprese (gara americana finita la
domenica sera UTC, classifica e mondiale arrivano entro poche ore). CORRETTO (26/10): era fino al lunedi'
alle 18:00 UTC, si catturava mezza giornata a weekend finito. Due richieste all'API pubblica dei risultati (stagioni e calendario), niente altro.

AGGIUNTA (30/10, Filippo): stampa anche "minuti=<N>", la durata del blocco: mai oltre la fine della finestra
(al massimo 345). E la finestra di un evento finisce UN'ORA PRIMA del giorno di inizio dell'evento dopo
(00:00 UTC) quando le due si toccano: un test il lunedi' subito dopo un GP prima perdeva le prime ore, perche'
il blocco del GP (fino a 5 h 45 min) era ancora in corso e la cattura del test partiva solo dopo.
"""
import sys
from datetime import datetime, timedelta, timezone

import requests

MINUTI_MAX = 345   # durata massima di un blocco (timeout del job: 358 min)
MINUTI_MIN = 10    # sotto, niente blocco
RESULTS = "https://api.motogp.pulselive.com/motogp/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def lista(x, chiave):
    return x if isinstance(x, list) else (x or {}).get(chiave, [])


def main():
    adesso = datetime.now(timezone.utc)
    s = requests.get(f"{RESULTS}/results/seasons", headers=HEADERS, timeout=20)
    s.raise_for_status()
    stagioni = lista(s.json(), "seasons")
    cur = next((x for x in stagioni if x.get("current")), None) or max(stagioni, key=lambda x: x.get("year", 0))
    # CORRETTO (29/10, pausa invernale): anche i TEST, e anche la stagione DOPO la corrente: il test dopo
    # Valencia sta nella stagione dell'anno dopo (VC1 del 18/11/2025 era nella 2026). Prima i test si
    # saltavano e si guardava solo la stagione corrente: il test di dicembre 2026 non sarebbe stato catturato.
    # Una richiesta in piu' solo quando la stagione dopo esiste gia'.
    eventi = []
    for st in [cur] + [x for x in stagioni if x.get("year") == cur.get("year", 0) + 1]:
        e = requests.get(f"{RESULTS}/results/events", params={"seasonUuid": st["id"]}, headers=HEADERS, timeout=20)
        e.raise_for_status()
        eventi += lista(e.json(), "events")
    finestre = []
    for ev in eventi:
        try:
            inizio = datetime.fromisoformat(str(ev["date_start"])[:10]).replace(tzinfo=timezone.utc)
            fine = datetime.fromisoformat(str(ev["date_end"])[:10]).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        da = inizio - timedelta(days=1) + timedelta(hours=16)
        a = fine + timedelta(days=1) + timedelta(hours=6)
        finestre.append([da, a, inizio, ev.get("short_name")])
    # AGGIUNTA (30/10): finestre consecutive che si sovrappongono (GP la domenica, test il lunedi'): la prima
    # finisce un'ora prima della mezzanotte UTC del giorno d'inizio della seconda, che parte da li'.
    finestre.sort(key=lambda f: f[0])
    for prima, dopo in zip(finestre, finestre[1:]):
        if dopo[0] < prima[1]:
            taglio = dopo[2] - timedelta(hours=1)
            prima[1] = max(prima[0], min(prima[1], taglio))
            dopo[0] = max(dopo[0], taglio)
    for da, a, _, sigla in finestre:
        if da <= adesso < a:
            minuti = min(MINUTI_MAX, int((a - adesso).total_seconds() // 60))
            if minuti < MINUTI_MIN:
                break   # finestra quasi finita: il blocco non servirebbe a niente
            print(f"sigla={sigla}")
            print(f"minuti={minuti}")
            print(f"weekend {sigla}: cattura da {da:%d/%m %H:%M} a {a:%d/%m %H:%M} UTC, blocco di {minuti} min",
                  file=sys.stderr)
            return
    print("sigla=")
    print("nessun weekend di gara adesso: niente cattura", file=sys.stderr)

if __name__ == "__main__":
    main()
