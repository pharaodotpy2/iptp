# LDT Manager (Java + GUI)

Ein einfacher Java-Swing-Manager für LDT-Dateien mit folgenden Funktionen:

- LDT-Dateien laden und analysieren
- Satzbeschreibungen / Satzarten **1, 2, 3** durchsuchen und zusammenfassen
- Einzelne Felder anzeigen und ändern
- Relevante Regeländerungen automatisch anwenden (z. B. Namens-Normalisierung, PLZ-Bereinigung)
- LDT-Dateien wieder speichern
- Modernes Look-and-Feel mit FlatLaf (falls FlatLaf im Classpath vorhanden ist), sonst System-Look-and-Feel

## Starten

```bash
javac -d out src/main/java/de/iptp/ldtmanager/*.java
java -cp out de.iptp.ldtmanager.LdtManagerApp
```

Mit FlatLaf (optional, wenn z. B. `flatlaf-<version>.jar` vorliegt):

```bash
java -cp "out:flatlaf-<version>.jar" de.iptp.ldtmanager.LdtManagerApp
```

## Regeln (aktuell)

- Feld `3101`/`3102`: Name in Großbuchstaben + trim
- Feld `3622`: Nur Ziffern, wenn genau 5-stellige PLZ möglich
- Feld `7400`: Leere Inhalte werden auf `N/A` gesetzt

Diese Regeln können im Code in `LdtRuleEngine` erweitert werden.
