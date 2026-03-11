package de.iptp.ldtmanager;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.MalformedInputException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class LdtParser {
    private static final List<Charset> CHARSET_FALLBACKS = List.of(
            StandardCharsets.UTF_8,
            Charset.forName("windows-1252"),
            StandardCharsets.ISO_8859_1
    );

    private LdtParser() {
    }

    public static List<LdtField> parse(Path path) throws IOException {
        IOException lastException = null;
        for (Charset charset : CHARSET_FALLBACKS) {
            try {
                return parseWithCharset(path, charset);
            } catch (MalformedInputException ex) {
                lastException = ex;
            }
        }

        if (lastException != null) {
            throw new IOException("Datei kann mit UTF-8/Windows-1252/ISO-8859-1 nicht gelesen werden.", lastException);
        }

        throw new IOException("Unbekannter Fehler beim Lesen der LDT-Datei.");
    }

    private static List<LdtField> parseWithCharset(Path path, Charset charset) throws IOException {
        List<String> lines = Files.readAllLines(path, charset);
        List<LdtField> fields = new ArrayList<>();
        String currentSatzart = "unbekannt";

        for (int i = 0; i < lines.size(); i++) {
            String line = lines.get(i).trim();
            if (line.isEmpty()) {
                continue;
            }

            String feldkennung;
            String inhalt;

            if (line.length() >= 7 && line.substring(0, 3).chars().allMatch(Character::isDigit)) {
                feldkennung = line.substring(3, 7);
                inhalt = line.length() > 7 ? line.substring(7) : "";
            } else if (line.contains("|")) {
                String[] parts = line.split("\\|", 2);
                feldkennung = parts[0];
                inhalt = parts.length > 1 ? parts[1] : "";
            } else {
                feldkennung = "RAW";
                inhalt = line;
            }

            if ("8000".equals(feldkennung) || "0001".equals(feldkennung)) {
                currentSatzart = normalizeSatzart(inhalt);
            }

            fields.add(new LdtField(line, i + 1, currentSatzart, feldkennung, inhalt));
        }

        return fields;
    }

    private static String normalizeSatzart(String raw) {
        String value = raw.trim();
        if (value.startsWith("1")) {
            return "1";
        }
        if (value.startsWith("2")) {
            return "2";
        }
        if (value.startsWith("3")) {
            return "3";
        }
        return value.isEmpty() ? "unbekannt" : value;
    }

    public static void write(Path path, List<LdtField> fields) throws IOException {
        List<String> out = new ArrayList<>();
        for (LdtField field : fields) {
            if ("RAW".equals(field.feldkennung())) {
                out.add(field.inhalt());
            } else {
                out.add(field.toLdtLine());
            }
        }
        Files.write(path, out, StandardCharsets.UTF_8);
    }
}
