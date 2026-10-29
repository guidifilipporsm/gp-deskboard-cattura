# GP DeskBoard – cattura automatica dei weekend di gara

Questo repository contiene solo l'automazione: una GitHub Action che, durante ogni weekend di gara MotoGP,
registra le risposte delle API pubbliche dei risultati e le salva in un repository **privato** di Filippo
Guidi. Servono a provare il firmware di GP DeskBoard su weekend veri (banco replay). I dati catturati non
stanno qui.

- `quando.py`: dice se adesso e' un weekend di gara o di test (dal giovedi' sera a 12 ore dopo l'ultima
  sessione) e quanto deve durare il blocco: mai oltre la fine della finestra.
- `.github/workflows/cattura.yml`: ogni 3 ore controlla; nel weekend fa girare la cattura a blocchi di
  circa 6 ore, uno dopo l'altro, e la salva nel repository privato.
- `ultimo_giro.txt`: aggiornato a ogni weekend e il primo del mese, perche' GitHub non spenga l'Action
  dopo 60 giorni senza attivita'.

Prudenza con le API: le stesse cadenze dello script usato finora dal PC (al massimo ~5 richieste al minuto
durante le sessioni, molto meno fuori), con attese crescenti dopo un errore.

© 2026 Filippo Guidi. GP DeskBoard non e' affiliato a Dorna Sports.
