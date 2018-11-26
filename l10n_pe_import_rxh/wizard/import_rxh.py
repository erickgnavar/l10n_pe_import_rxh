import base64

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..utils import extract_data_from_xml


class ImportRxH(models.TransientModel):

    _name = "import.rxh"

    xml_file = fields.Binary(
        "SUNAT xml file",
        required=True,
        help_text="This is the file generated when the RxH is created in SUNAT website",
    )

    create_supplier = fields.Boolean(
        "Create supplier if it doesn't exist",
        default=False,
        help_text="If the supplier RUC isn't found it will be created using RxH data",
    )

    account_id = fields.Many2one(
        "account.account",
        "Account",
        required=True,
        help_text="Used for invoice line account",
    )

    @api.multi
    def action_process_file(self):
        self.ensure_one()
        decoded_file = base64.b64decode(self.xml_file)
        data, message = extract_data_from_xml(decoded_file)
        if not data:
            raise ValidationError(message)

        supplier = self.env["res.partner"].search([
            ("vat", "=", data["supplier"]["account_id"]),
            ("supplier", "=", True),
        ], limit=1)
        if not supplier and self.create_supplier:
            supplier = self.env["res.partner"].create({
                "name": data["supplier"]["party"]["name"],
                "vat": data["supplier"]["account_id"],
                "supplier": True,
                "street": data["supplier"]["party"]["address"],
                "phone": data["supplier"]["party"]["phone"],
            })
        elif not supplier:
            sup = data["supplier"]
            name = "{} - {}".format(sup["account_id"], sup["party"]["name"])
            raise ValidationError("The supplier {} doesn't exist".format(name))

        invoice_data = {
            "partner_id": supplier.id,
            "date_invoice": data["issue_date"],
            "type": "in_invoice",
            "invoice_line_ids": [
                (0, False, {
                    "name": data["line"]["description"],
                    "quantity": 1,
                    "price_unit": data["legal_amount"]["payable_amount"],
                    "account_id": self.account_id.id,
                }),
            ],
        }
        invoice = self.env["account.invoice"].create(invoice_data)
        view = self.env.ref("account.invoice_supplier_form")
        return {
            "name": "Invoice created from RxH",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_model": "account.invoice",
            "view_id": view.id,
            "res_id": invoice.id,
        }
