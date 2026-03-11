package de.iptp.ldtmanager;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class LdtParser {
    private LdtParser() {
    }

    public static List<LdtField> parse(Path path) throws IOException {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
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
