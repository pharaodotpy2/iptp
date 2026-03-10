#!/usr/bin/env python3
"""CLI tool to read GAEB files and generate simple X83/X84 and ZUGFeRD-like PDF output."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class Item:
    line_id: str
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class InvoiceData:
    invoice_number: str
    issue_date: str
    seller_name: str
    buyer_name: str
    currency: str
    items: list[Item]

    @property
    def grand_total(self) -> Decimal:
        return sum((it.total for it in self.items), Decimal("0"))


def _find_first_text(node: ET.Element, tag_options: list[str], default: str = "") -> str:
    for tag in tag_options:
        found = node.find(f".//{tag}")
        if found is not None and found.text:
            return found.text.strip()
    return default


def parse_gaeb_xml(path: Path) -> InvoiceData:
    tree = ET.parse(path)
    root = tree.getroot()

    invoice_number = _find_first_text(root, ["AngebotNr", "RechnungNr", "DocumentID"], "UNBEKANNT")
    issue_date = _find_first_text(root, ["Datum", "IssueDate"], dt.date.today().isoformat())
    seller_name = _find_first_text(root, ["Auftragnehmer", "SellerName"], "Unbekannter Auftragnehmer")
    buyer_name = _find_first_text(root, ["Auftraggeber", "BuyerName"], "Unbekannter Auftraggeber")
    currency = _find_first_text(root, ["Waehrung", "Currency"], "EUR")

    items: list[Item] = []
    for pos in root.findall(".//Position") + root.findall(".//Item"):
        line_id = _find_first_text(pos, ["OZ", "LineID"], str(len(items) + 1))
        description = _find_first_text(pos, ["Kurztext", "Description"], "Ohne Text")
        qty_text = _find_first_text(pos, ["Menge", "Quantity"], "1")
        unit = _find_first_text(pos, ["Einheit", "Unit"], "Stk")
        price_text = _find_first_text(pos, ["EP", "UnitPrice"], "0")

        items.append(
            Item(
                line_id=line_id,
                description=description,
                quantity=Decimal(qty_text.replace(",", ".")),
                unit=unit,
                unit_price=Decimal(price_text.replace(",", ".")),
            )
        )

    if not items:
        raise ValueError("Keine Positionen in der GAEB-Datei gefunden.")

    return InvoiceData(
        invoice_number=invoice_number,
        issue_date=issue_date,
        seller_name=seller_name,
        buyer_name=buyer_name,
        currency=currency,
        items=items,
    )


def write_gaeb_x8x(data: InvoiceData, output: Path, phase: str) -> None:
    root = ET.Element("GAEB")
    ET.SubElement(root, "Phase").text = phase
    ET.SubElement(root, "DocumentID").text = data.invoice_number
    ET.SubElement(root, "IssueDate").text = data.issue_date
    ET.SubElement(root, "SellerName").text = data.seller_name
    ET.SubElement(root, "BuyerName").text = data.buyer_name
    ET.SubElement(root, "Currency").text = data.currency

    items_node = ET.SubElement(root, "Items")
    for it in data.items:
        n = ET.SubElement(items_node, "Item")
        ET.SubElement(n, "LineID").text = it.line_id
        ET.SubElement(n, "Description").text = it.description
        ET.SubElement(n, "Quantity").text = str(it.quantity)
        ET.SubElement(n, "Unit").text = it.unit
        ET.SubElement(n, "UnitPrice").text = str(it.unit_price)
        ET.SubElement(n, "LineTotal").text = str(it.total)

    ET.SubElement(root, "GrandTotal").text = str(data.grand_total)

    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)


def build_zugferd_xml(data: InvoiceData) -> bytes:
    lines = []
    for it in data.items:
        lines.append(
            f"""
      <ram:IncludedSupplyChainTradeLineItem>
        <ram:AssociatedDocumentLineDocument><ram:LineID>{it.line_id}</ram:LineID></ram:AssociatedDocumentLineDocument>
        <ram:SpecifiedTradeProduct><ram:Name>{it.description}</ram:Name></ram:SpecifiedTradeProduct>
        <ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>{it.unit_price}</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
        <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="{it.unit}">{it.quantity}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
        <ram:SpecifiedLineTradeSettlement><ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{it.total}</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>
      </ram:IncludedSupplyChainTradeLineItem>
""".strip()
        )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
  <rsm:ExchangedDocument>
    <ram:ID>{data.invoice_number}</ram:ID>
    <ram:IssueDateTime><ram:DateTimeString format="102">{data.issue_date.replace('-', '')}</ram:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    {' '.join(lines)}
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>{data.currency}</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:GrandTotalAmount>{data.grand_total}</ram:GrandTotalAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""
    return xml.encode("utf-8")


def create_zugferd_pdf(data: InvoiceData, output_pdf: Path) -> None:
    """Create a simple PDF and attach invoice XML (requires pypdf)."""
    try:
        from pypdf import PdfWriter
    except ImportError as exc:
        raise RuntimeError("Bitte 'pip install pypdf' ausführen, um PDF zu erzeugen.") from exc

    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)

    xml_payload = build_zugferd_xml(data)
    writer.add_attachment("factur-x.xml", xml_payload)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as fp:
        writer.write(fp)


def cmd_parse(args: argparse.Namespace) -> None:
    data = parse_gaeb_xml(Path(args.input))
    print(json.dumps({**asdict(data), "grand_total": str(data.grand_total)}, indent=2, default=str, ensure_ascii=False))


def cmd_x83(args: argparse.Namespace) -> None:
    data = parse_gaeb_xml(Path(args.input))
    write_gaeb_x8x(data, Path(args.output), "X83")
    print(f"X83 geschrieben: {args.output}")


def cmd_x84(args: argparse.Namespace) -> None:
    data = parse_gaeb_xml(Path(args.input))
    write_gaeb_x8x(data, Path(args.output), "X84")
    print(f"X84 geschrieben: {args.output}")


def cmd_zugferd(args: argparse.Namespace) -> None:
    data = parse_gaeb_xml(Path(args.input))
    create_zugferd_pdf(data, Path(args.output))
    print(f"ZUGFeRD-PDF geschrieben: {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GAEB + ZUGFeRD Helfer")
    sub = parser.add_subparsers(required=True)

    p_parse = sub.add_parser("parse", help="GAEB lesen und als JSON ausgeben")
    p_parse.add_argument("input")
    p_parse.set_defaults(func=cmd_parse)

    p_x83 = sub.add_parser("x83", help="X83 XML erzeugen")
    p_x83.add_argument("input")
    p_x83.add_argument("output")
    p_x83.set_defaults(func=cmd_x83)

    p_x84 = sub.add_parser("x84", help="X84 XML erzeugen")
    p_x84.add_argument("input")
    p_x84.add_argument("output")
    p_x84.set_defaults(func=cmd_x84)

    p_zug = sub.add_parser("zugferd", help="ZUGFeRD PDF erzeugen")
    p_zug.add_argument("input")
    p_zug.add_argument("output")
    p_zug.set_defaults(func=cmd_zugferd)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
