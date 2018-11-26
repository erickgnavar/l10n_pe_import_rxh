from io import BytesIO

from lxml import etree


def _party_info(node, ns):
    return {
        "name": node.find("cac:PartyName", ns).find("cbc:Name", ns).text,
        "address": node.find("cac:PostalAddress", ns).find("cbc:StreetName", ns).text,
        "phone": node.find("cac:Contact", ns).find("cbc:Telephone", ns).text,
    }


def _supplier_info(node, ns):
    """
    Given a cac:AccountingSupplierParty node extract its data
    """
    account_id = node.find("cbc:CustomerAssignedAccountID", ns).text
    party = _party_info(node.find("cac:Party", ns), ns)
    return {
        "account_id": account_id.strip(),
        "party": party,
    }


def _customer_info(node, ns):
    """
    Given a cac:AccountingCustomerParty node extract its data
    """
    account_id = node.find("cbc:CustomerAssignedAccountID", ns).text
    additional_account_id = node.find("cbc:AdditionalAccountID", ns).text
    party = _party_info(node.find("cac:Party", ns), ns)
    return {
        "account_id": account_id.strip(),
        "additional_account_id": additional_account_id.strip(),
        "party": party,
    }


def _invoice_line_info(node, ns):
    """
    Given a cac:InvoiceLine node extract its data
    """
    id_ = node.find("cbc:ID", ns).text
    note = node.find("cbc:Note", ns).text
    qty = node.find("cbc:InvoicedQuantity", ns).text
    description = node.find("cac:Item", ns).find("cbc:Description", ns).text

    tax_node = node.find("cac:TaxTotal", ns)
    tax_subtotal_node = tax_node.find("cac:TaxSubtotal", ns)
    tax = {
        "amount": tax_node.find("cbc:TaxAmount", ns).text,
        "subtotal": tax_subtotal_node.find("cbc:TaxAmount", ns).text,
        "percent": tax_subtotal_node.find("cbc:Percent", ns).text,
        "category": tax_subtotal_node.find("cac:TaxCategory", ns).find("cbc:ID", ns).text
    }

    return {
        "id": id_,
        "note": note,
        "quantity": qty,
        "description": description,
        "tax": tax,
    }


def _tax_info(node, ns):
    """
    Given a cac:TaxTotal node extract its data
    """
    amount = node.find("cbc:TaxAmount", ns).text
    subtotal_node = node.find("cac:TaxSubtotal", ns)
    taxable_amount = subtotal_node.find("cbc:TaxableAmount", ns).text
    tax_amount = subtotal_node.find("cbc:TaxAmount", ns).text
    tax_category = subtotal_node.find("cac:TaxCategory", ns).find("cbc:ID", ns).text
    return {
        "amount": amount,
        "taxable_amount": taxable_amount,
        "tax_amount": tax_amount,
        "tax_category": tax_category,
    }


def _legal_monetary_info(node, ns):
    """
    Given a cac:LegalMonetaryTotal node extract its data
    """
    return {
        "line_extension_amount": node.find("cbc:LineExtensionAmount", ns).text,
        "tax_exclusive_amount": node.find("cbc:TaxExclusiveAmount", ns).text,
        "payable_amount": node.find("cbc:PayableAmount", ns).text,
    }


def _invoice_info(node, ns):
    """
    Given a cac:Invoice node extract its data
    """
    supplier_data = _supplier_info(node.find("cac:AccountingSupplierParty", ns), ns)
    customer_data = _customer_info(node.find("cac:AccountingCustomerParty", ns), ns)
    line_data = _invoice_line_info(node.find("cac:InvoiceLine", ns), ns)
    tax_data = _tax_info(node.find("cac:TaxTotal", ns), ns)
    legal_monetary_data = _legal_monetary_info(node.find("cac:LegalMonetaryTotal", ns), ns)
    id_ = node.find("cbc:ID", ns).text
    issue_date = node.find("cbc:IssueDate", ns).text
    issue_time = node.find("cbc:IssueTime", ns).text

    return {
        "supplier": supplier_data,
        "customer": customer_data,
        "id": id_,
        "issue_date": issue_date,
        "issue_time": issue_time,
        "line": line_data,
        "tax": tax_data,
        "legal_amount": legal_monetary_data,
    }


def extract_data_from_xml(xml):
    """
    Given a file like object extract its content
    """
    buffer = BytesIO()
    buffer.write(xml)
    buffer.seek(0)

    try:
        root = etree.parse(buffer).getroot()
        ns = root.nsmap
        if None in ns:
            del ns[None]
        return _invoice_info(root, ns), None
    except etree.XMLSyntaxError:
        return None, "The xml content is not valid"
