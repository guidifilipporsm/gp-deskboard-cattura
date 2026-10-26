#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weekend di gara in corso? Stampa "sigla=<SIGLA>" (formato di $GITHUB_OUTPUT) se adesso e' dentro la
finestra di cattura di un GP, altrimenti "sigla=". Lo usa la GitHub Action di questo repository.

Finestra: dal giorno PRIMA della data di inizio (le 16:00 UTC, cioe' giovedi' sera in Italia) al lunedi'
alle 06:00 UTC: copre tutto il weekend in ogni fuso, Australia e Americhe comprese (gara americana finita la
domenica sera UTC, classifica e mondiale arrivano entro poche ore). CORRETTO (26/10): era fino al lunedi'
alle 18:00 UTC, si catturava mezza giornata a weekend finito. Due richieste all'API pubblica dei risultati (stagioni e calendario), niente altro.
"""
import sys
from datetime import datetime, timedelta, timezone

import requests

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
    e = requests.get(f"{RESULTS}/results/events", params={"seasonUuid": cur["id"]}, headers=HEADERS, timeout=20)
    e.raise_for_status()
    for ev in lista(e.json(), "events"):
        if ev.get("test"):
            continue
        try:
            inizio = datetime.fromisoformat(str(ev["date_start"])[:10]).replace(tzinfo=timezone.utc)
            fine = datetime.fromisoformat(str(ev["date_end"])[:10]).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        da = inizio - timedelta(days=1) + timedelta(hours=16)
        a = fine + timedelta(days=1) + timedelta(hours=6)
        if da <= adesso <= a:
            print(f"sigla={ev.get('short_name')}")
            print(f"weekend {ev.get('short_name')}: cattura da {da:%d/%m %H:%M} a {a:%d/%m %H:%M} UTC", file=sys.stderr)
            return
    print("sigla=")
    print("nessun weekend di gara adesso: niente cattura", file=sys.stderr)


if __name__ == "__main__":
    main()
