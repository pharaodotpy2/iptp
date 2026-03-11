package de.iptp.ldtmanager;

import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.ListSelectionModel;
import javax.swing.SwingUtilities;
import java.awt.BorderLayout;
import java.awt.GridLayout;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class LdtManagerApp extends JFrame {
    private final DefaultListModel<LdtField> listModel = new DefaultListModel<>();
    private final JList<LdtField> fieldList = new JList<>(listModel);
    private final JTextArea infoArea = new JTextArea();
    private final JTextField valueField = new JTextField();

    private Path currentFile;
    private List<LdtField> loadedFields = new ArrayList<>();

    public LdtManagerApp() {
        super("LDT Manager");
        setSize(1100, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout(8, 8));

        JButton openBtn = new JButton("LDT laden");
        JButton saveBtn = new JButton("LDT speichern");
        JButton applyRulesBtn = new JButton("Relevante Regel-Änderungen anwenden");

        JPanel topBar = new JPanel();
        topBar.add(openBtn);
        topBar.add(saveBtn);
        topBar.add(applyRulesBtn);
        add(topBar, BorderLayout.NORTH);

        fieldList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        fieldList.setCellRenderer((list, value, index, isSelected, cellHasFocus) ->
                new JLabel(value.toDisplayString()));

        JScrollPane leftPane = new JScrollPane(fieldList);

        infoArea.setEditable(false);
        valueField.setEditable(false);

        JButton editBtn = new JButton("Ausgewähltes Feld ändern");

        JPanel rightPanel = new JPanel(new BorderLayout(6, 6));
        rightPanel.add(new JScrollPane(infoArea), BorderLayout.CENTER);

        JPanel editPanel = new JPanel(new GridLayout(2, 1, 6, 6));
        editPanel.add(valueField);
        editPanel.add(editBtn);
        rightPanel.add(editPanel, BorderLayout.SOUTH);

        JPanel center = new JPanel(new GridLayout(1, 2, 8, 8));
        center.add(leftPane);
        center.add(rightPanel);
        add(center, BorderLayout.CENTER);

        openBtn.addActionListener(e -> openFile());
        saveBtn.addActionListener(e -> saveFile());
        applyRulesBtn.addActionListener(e -> applyRules());

        fieldList.addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                showFieldDetails(fieldList.getSelectedValue());
            }
        });

        editBtn.addActionListener(e -> editSelectedField());
    }

    private void openFile() {
        JFileChooser chooser = new JFileChooser();
        if (chooser.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) {
            return;
        }

        try {
            currentFile = chooser.getSelectedFile().toPath();
            loadedFields = LdtParser.parse(currentFile);
            refreshList();
            showSummary();
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Fehler beim Laden: " + ex.getMessage());
        }
    }

    private void refreshList() {
        listModel.clear();
        for (LdtField field : loadedFields) {
            listModel.addElement(field);
        }
    }

    private void showSummary() {
        Map<String, Long> countBySatzart = loadedFields.stream()
                .collect(Collectors.groupingBy(LdtField::satzart, Collectors.counting()));

        String text = "Analyse der LDT Satzbeschreibungen 1, 2, 3\n\n"
                + "Satzart 1: " + countBySatzart.getOrDefault("1", 0L) + " Felder\n"
                + "Satzart 2: " + countBySatzart.getOrDefault("2", 0L) + " Felder\n"
                + "Satzart 3: " + countBySatzart.getOrDefault("3", 0L) + " Felder\n"
                + "Sonstige: " + loadedFields.stream().filter(f -> !List.of("1", "2", "3").contains(f.satzart())).count();

        infoArea.setText(text);
        valueField.setText("");
        valueField.setEditable(false);
    }

    private void showFieldDetails(LdtField field) {
        if (field == null) {
            return;
        }
        infoArea.setText("Detailinformationen\n\n"
                + "Zeile: " + field.lineNumber() + "\n"
                + "Satzart: " + field.satzart() + "\n"
                + "Feldkennung: " + field.feldkennung() + "\n"
                + "Inhalt: " + field.inhalt() + "\n");

        valueField.setText(field.inhalt());
        valueField.setEditable(true);
    }

    private void editSelectedField() {
        int idx = fieldList.getSelectedIndex();
        if (idx < 0) {
            JOptionPane.showMessageDialog(this, "Bitte zuerst ein Feld auswählen.");
            return;
        }
        LdtField oldField = loadedFields.get(idx);
        String newValue = valueField.getText();
        loadedFields.set(idx, new LdtField(oldField.originalLine(), oldField.lineNumber(), oldField.satzart(), oldField.feldkennung(), newValue));
        refreshList();
        fieldList.setSelectedIndex(idx);
    }

    private void applyRules() {
        if (loadedFields.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Bitte zuerst eine LDT-Datei laden.");
            return;
        }
        List<String> changes = LdtRuleEngine.applyRelevantRules(loadedFields);
        refreshList();
        if (changes.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Keine relevanten Änderungen notwendig.");
            return;
        }
        JOptionPane.showMessageDialog(this, "Regeln angewendet:\n- " + String.join("\n- ", changes));
    }

    private void saveFile() {
        if (loadedFields.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Keine Daten zum Speichern vorhanden.");
            return;
        }
        JFileChooser chooser = new JFileChooser();
        if (currentFile != null) {
            chooser.setSelectedFile(currentFile.toFile());
        }
        if (chooser.showSaveDialog(this) != JFileChooser.APPROVE_OPTION) {
            return;
        }

        try {
            Path target = chooser.getSelectedFile().toPath();
            LdtParser.write(target, loadedFields);
            JOptionPane.showMessageDialog(this, "Datei gespeichert: " + target);
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Fehler beim Speichern: " + ex.getMessage());
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new LdtManagerApp().setVisible(true));
    }
}
