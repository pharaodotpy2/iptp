from pathlib import Path
import xml.etree.ElementTree as ET

from gaeb_zugferd_tool import parse_gaeb_xml, write_gaeb_x8x, build_zugferd_xml


def test_parse_and_totals(tmp_path: Path):
    source = Path("sample_gaeb.xml")
    data = parse_gaeb_xml(source)
    assert data.invoice_number == "RE-2026-001"
    assert str(data.grand_total) == "4182.00"


def test_write_x83(tmp_path: Path):
    data = parse_gaeb_xml(Path("sample_gaeb.xml"))
    output = tmp_path / "x83.xml"
    write_gaeb_x8x(data, output, "X83")

    tree = ET.parse(output)
    root = tree.getroot()
    assert root.findtext("Phase") == "X83"
    assert root.findtext("GrandTotal") == "4182.00"


def test_build_zugferd_xml():
    data = parse_gaeb_xml(Path("sample_gaeb.xml"))
    payload = build_zugferd_xml(data).decode("utf-8")
    assert "CrossIndustryInvoice" in payload
    assert "RE-2026-001" in payload
