{
    "name": "ODK Connector",
    "summary": "Connect ODK Central to Odoo",
    "version": "12.0.2.2.2",
    "category": "Connector",
    "author": "Subham Pramanik",
    "depends": [
        "base",
        "web",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/odk_submissions_view.xml",
        "views/odk_config_form.xml",
        "views/action.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
}
