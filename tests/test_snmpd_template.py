import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class TestSnmpdTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        template_dir = Path(__file__).parent.parent / "templates"
        cls.template = Environment(
            loader=FileSystemLoader(template_dir)
        ).get_template("snmpd.conf")

    def render(self, monitor_disks=True, disk_threshold=10):
        return self.template.render(
            sysLocation="undermydesk",
            sysContact="John Doe <john.doe@example.org>",
            acls=["rocommunity public localhost"],
            monitorDisks=monitor_disks,
            diskThreshold=disk_threshold,
            other=[],
        )

    def test_disk_monitoring_defaults_to_ten_percent(self):
        self.assertIn("includeAllDisks 10%", self.render())

    def test_disk_monitoring_uses_custom_threshold(self):
        self.assertIn("includeAllDisks 25%", self.render(disk_threshold=25))

    def test_disk_monitoring_can_be_disabled(self):
        self.assertNotIn("includeAllDisks", self.render(monitor_disks=False))


if __name__ == "__main__":
    unittest.main()
