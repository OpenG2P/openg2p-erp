class GatewayTransaction(models.Model):
    _name = "openg2p.gateway.transaction"

    origin_id = fields.Reference(
        selection=[
            ("sale.order", "Sale Order"),
            ("account.invoice", "Account Invoice"),
        ]
    )
