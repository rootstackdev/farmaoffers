# -*- coding: utf-8 -*-

from . import models
from . import controllers
from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers
from odoo.addons.payment import reset_payment_provider


def _post_init_hook(cr, registry):
    from pynpm import NPMPackage
    from os.path import dirname
    create_missing_journal_for_acquirers(cr, registry)
    pkg = NPMPackage(dirname(__file__) + '/models/node_sdk/package.json')
    pkg.install()
    pkg.run_script('build')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'yappy')
