from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env.cr, "openg2p", "migrations/14.0/noupdate_changes.xml")
