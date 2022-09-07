# -*- coding: utf-8 -*-

from . import models
from . import controllers
from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers
from odoo.addons.payment import reset_payment_provider


def _post_init_hook(cr, registry):
    import shutil
    import os
    from pynpm import NPMPackage
    from os.path import dirname
    source_dir = dirname(__file__) + '/node_sdk'
    destination_dir = os.path.expanduser('~') + '/node_sdk'
    shutil.copytree(source_dir, destination_dir)
    create_missing_journal_for_acquirers(cr, registry)
    pkg = NPMPackage(destination_dir + '/package.json')
    pkg.install()
    pkg.run_script('build')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'yappy')
