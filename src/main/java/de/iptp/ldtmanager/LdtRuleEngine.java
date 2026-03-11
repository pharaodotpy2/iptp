package de.iptp.ldtmanager;

import java.util.ArrayList;
import java.util.List;

public final class LdtRuleEngine {
    private LdtRuleEngine() {
    }

    public static List<String> applyRelevantRules(List<LdtField> fields) {
        List<String> changes = new ArrayList<>();
        for (int i = 0; i < fields.size(); i++) {
            LdtField field = fields.get(i);
            String key = field.feldkennung();
            String value = field.inhalt();

            if ("3101".equals(key) || "3102".equals(key)) {
                String normalized = value.toUpperCase().trim();
                if (!normalized.equals(value)) {
                    fields.set(i, new LdtField(field.originalLine(), field.lineNumber(), field.satzart(), key, normalized));
                    changes.add("Name normalisiert in Zeile " + field.lineNumber());
                }
            }

            if ("3622".equals(key)) {
                String digits = value.replaceAll("\\D", "");
                if (digits.length() == 5 && !digits.equals(value)) {
                    fields.set(i, new LdtField(field.originalLine(), field.lineNumber(), field.satzart(), key, digits));
                    changes.add("PLZ bereinigt in Zeile " + field.lineNumber());
                }
            }

            if ("7400".equals(key) && value.isBlank()) {
                fields.set(i, new LdtField(field.originalLine(), field.lineNumber(), field.satzart(), key, "N/A"));
                changes.add("Leeren Befundtext mit N/A ersetzt in Zeile " + field.lineNumber());
            }
        }

        return changes;
    }
}
