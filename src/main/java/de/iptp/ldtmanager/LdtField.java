package de.iptp.ldtmanager;

public record LdtField(String originalLine, int lineNumber, String satzart, String feldkennung, String inhalt) {
    public String toDisplayString() {
        return "Zeile " + lineNumber + " | Satz " + satzart + " | Feld " + feldkennung + " | " + inhalt;
    }

    public String toLdtLine() {
        int payloadLength = 4 + inhalt.length();
        String len = String.format("%03d", payloadLength);
        return len + feldkennung + inhalt;
    }
}
