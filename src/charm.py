#!/usr/bin/env python3
# Copyright 2022 Erik Lonroth <erik.lonroth@gmail.com>
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""snmpd service charm.
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus, Relation
from subprocess import check_call, check_output
from pathlib import Path

from charms.operator_libs_linux.v0 import systemd
from charms.operator_libs_linux.v0 import apt
from jinja2 import Environment, FileSystemLoader


logger = logging.getLogger(__name__)

class snmpdCharm(CharmBase):
    """snmpd service charm."""


    def __init__(self, *args):
        super().__init__(*args)

        self._service_name = "snmpd.service"
        self._template_dir = Path(__file__).parent.parent / "templates"
        self._snmpd_config_path = "/etc/snmp/snmpd.conf"

        fw = self.framework
        fw.observe(self.on.install, self._on_install)
        fw.observe(self.on.stop, self._on_stop)

        fw.observe(self.on.config_changed, self._on_config_changed)

    def _on_install(self, _event):
        """Install and start the snmpd service.
        """

        self.unit.status = MaintenanceStatus('Installing snmpd')

        try:
            # Run `apt-get update`
            apt.update()
            apt.add_package("snmpd")

        except apt.PackageNotFoundError:
            logger.error("snmpd package not found in package cache or on system")
        except apt.PackageError as e:
            logger.error("could not install snmpd package. Reason: %s", e.message)

        self.unit.status = MaintenanceStatus('Configuring snmpd')

        #render out the config
        self._render_config()

        systemd.service_restart(self._service_name)

        self.unit.status = ActiveStatus("snmpd installed/configured")

    def _on_config_changed(self, _event):
        """Updates the service on config change.
        """
        self.unit.status = MaintenanceStatus('Configuring snmpd')

        #render out the config
        self._render_config()

        # restart the service
        systemd.service_restart("snmpd.service")

        self.unit.status = ActiveStatus("snmpd installed/configured")

    def _on_stop(self, _event):
        """Stop the service.
        """
        systemd.service_stop(self._service_name)
        self.unit.status = ActiveStatus('Service stopped.')


    # UTILITIES
    def _render_config(self):
        """Render out snmpd.conf .
        """

        config_attrs = {
            'sysLocation': self.sys_location,
            'sysContact': self.sys_contact,
            'acls': [l.strip() for l in self.acls.splitlines()],
            'other': [l.strip() for l in self.other.splitlines()],
        }

        environment = Environment(loader=FileSystemLoader(self._template_dir))
        template = environment.get_template("snmpd.conf")
        snmpd_config_contents = template.render(config_attrs)
        with open(self._snmpd_config_path, mode='w') as f:
            f.write(snmpd_config_contents)

    @property
    def sys_location(self) -> str:
        """SNMP sysLocation.
        """
        return self.config['sysLocation']

    @property
    def sys_contact(self) -> str:
        """SNMP sysContact.
        """
        return self.config['sysContact']

    @property
    def acls(self) -> str:
        """SNMP ACLs.
        """
        return self.config['acls']

    @property
    def other(self) -> str:
        """SNMP other config.
        """
        return self.config['other']

if __name__ == "__main__":
    main(snmpdCharm)
