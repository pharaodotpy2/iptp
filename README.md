# LDT Manager (Java + GUI)

Ein einfacher Java-Swing-Manager für LDT-Dateien mit folgenden Funktionen:

- LDT-Dateien laden und analysieren
- Satzbeschreibungen / Satzarten **1, 2, 3** durchsuchen und zusammenfassen
- Einzelne Felder anzeigen und ändern
- Relevante Regeländerungen automatisch anwenden (z. B. Namens-Normalisierung, PLZ-Bereinigung)
- LDT-Dateien wieder speichern

## Starten

```bash
javac -d out src/main/java/de/iptp/ldtmanager/*.java
java -cp out de.iptp.ldtmanager.LdtManagerApp
```

## Regeln (aktuell)

- Feld `3101`/`3102`: Name in Großbuchstaben + trim
- Feld `3622`: Nur Ziffern, wenn genau 5-stellige PLZ möglich
- Feld `7400`: Leere Inhalte werden auf `N/A` gesetzt

Diese Regeln können im Code in `LdtRuleEngine` erweitert werden.

## Häufiger JPA-Fehler (Praxisverwaltung)

Wenn in einem anderen Java-Projekt (z. B. Praxisverwaltung) der Fehler
`jakarta.persistence.column ist keine wiederholbare Annotationsschnittstelle`
auftaucht, liegt meistens ein Schreib- oder Importfehler vor.

### Ursache

- Falsche Annotation: `@column` statt `@Column`
- Falscher Import oder gemischte `javax.persistence`/`jakarta.persistence`-Imports

### Korrektes Beispiel

```java
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class Patient {
    @Id
    private Long id;

    @Column(name = "nachname")
    private String nachname;
}
```

### Checkliste zur Behebung

1. Annotation überall als `@Column` (großes **C**) schreiben.
2. Nur `jakarta.persistence.*` **oder** nur `javax.persistence.*` verwenden (nicht mischen).
3. Doppelte Annotationen auf demselben Feld vermeiden (z. B. zwei `@Column`-Zeilen).
