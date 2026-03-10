# GAEB + ZUGFeRD CLI

Kleines Python-Programm, das:

- GAEB-XML einlesen kann (`parse`)
- aus einer Eingabe eine einfache **X83**-Datei erzeugt
- aus einer Eingabe eine einfache **X84**-Datei erzeugt
- ein minimales ZUGFeRD-/Factur-X-kompatibles PDF mit eingebetteter XML erzeugt (mit `pypdf`)

## Nutzung

```bash
python3 gaeb_zugferd_tool.py parse sample_gaeb.xml
python3 gaeb_zugferd_tool.py x83 sample_gaeb.xml out/x83.xml
python3 gaeb_zugferd_tool.py x84 sample_gaeb.xml out/x84.xml
python3 gaeb_zugferd_tool.py zugferd sample_gaeb.xml out/rechnung.pdf
```

## Hinweis

Dieses Tool ist ein **Starter** für Workflows um GAEB/X83/X84 und ZUGFeRD. Für produktiven Einsatz müssen in der Regel vollständige Schemavalidierung, Profile (z. B. EN16931) und fachliche Pflichtfelder ergänzt werden.


## GUI

Starte die Oberfläche mit:

```bash
python3 gaeb_zugferd_gui.py
```

In der GUI kannst du eine GAEB-XML auswählen und per Button X83, X84 oder ZUGFeRD-PDF erzeugen.
