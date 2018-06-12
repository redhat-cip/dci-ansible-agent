import mock
import os
import tempfile
import unittest
import xmlrpclib

from bugcheck import BugVerifyCmd
from bugcheck import BugzillaConnector
from bugcheck import LaunchpadConnector
from bugcheck import VerifyBug
from bugcheck import OPEN
from bugcheck import CLOSED
from bugcheck import INVALID


class TestLaunchpadConnector(unittest.TestCase):

    @mock.patch('launchpadlib.launchpad.Launchpad.login_anonymously')
    def test_get_bug_status(self, launchpad_mock):
        lp_connector = LaunchpadConnector()

        bugs = launchpad_mock.return_value.bugs
        bug_tasks = bugs.__getitem__().bug_tasks
        item = bug_tasks.__getitem__()

        for status in ['Fix Released', 'Fix Committed', 'Invalid']:
            item.status = status
            self.assertEquals(lp_connector.get_bug_status(1693838), CLOSED)

        item.status = 'No idea'
        self.assertEquals(lp_connector.get_bug_status(1693838), OPEN)

        bugs.__getitem__.side_effect = KeyError()
        self.assertEquals(lp_connector.get_bug_status(1693838), INVALID)


class TestBugzillaConnector(unittest.TestCase):
    @mock.patch('bugzilla.Bugzilla')
    def test_get_bug_status(self, bugzilla_mock):
        bz_connector = BugzillaConnector()
        bug = bugzilla_mock.return_value.getbug
        bug.return_value.status = 'CLOSED'
        self.assertEquals(bz_connector.get_bug_status(123), CLOSED)
        bz_status = ['ASSIGNED', 'NEEDINFO', 'NEW', 'REOPENED', 'RESOLVED',
                     'UNCONFIRMED', 'VERIFIRED']
        for status in bz_status:
            bug.return_value.status = status
            self.assertEquals(bz_connector.get_bug_status(123), OPEN)

        bug.side_effect = xmlrpclib.Fault(faultCode=102,
                                          faultString='Permission')
        self.assertEquals(bz_connector.get_bug_status(123), OPEN)
        bug.side_effect = xmlrpclib.Fault(faultCode=42,
                                          faultString='Other fault')
        self.assertEquals(bz_connector.get_bug_status(123), INVALID)


class TestVerifyBug(unittest.TestCase):
    @mock.patch('launchpadlib.launchpad.Launchpad.login_anonymously')
    @mock.patch('bugzilla.Bugzilla')
    def setUp(self, bz_mock, lp_mock):
        self.v_bug = VerifyBug()

    def test__get_id_from_url(self):
        self.assertEquals(self.v_bug._get_id_from_url(
            'https://bugs.launchpad.net/tripleo/+bug/1577769'), 1577769)
        self.assertEquals(self.v_bug._get_id_from_url(
            'https://bugzilla.redhat.com/show_bug.cgi?id=1380187'), 1380187)

    def test__get_connector(self):
        self.assertIsInstance(self.v_bug._get_connector(
            'https://bugs.launchpad.net/tripleo/+bug/1577769'),
            LaunchpadConnector)
        self.assertIsInstance(self.v_bug._get_connector(
            'https://bugzilla.redhat.com/show_bug.cgi?id=1380187'),
            BugzillaConnector)
        self.assertRaises(ValueError, self.v_bug._get_connector,
                          'https://review.openstack.org')

    @mock.patch('bugcheck.VerifyBug.check_bug_status')
    def test_is_bug_open(self, bug_status_mock):
        for status in [CLOSED, INVALID]:
            bug_status_mock.return_value = status
            self.assertEquals(self.v_bug.is_bug_open(
                'https://bugzilla.redhat.com/show_bug.cgi?id=1380187'), False)

        bug_status_mock.return_value = OPEN
        self.assertEquals(self.v_bug.is_bug_open(
            'https://bugzilla.redhat.com/show_bug.cgi?id=1380187'), True)


class TestBugVerifyCmd(unittest.TestCase):
    def setUp(self):
        self.fd_file, self.tmp_file = tempfile.mkstemp()
        self._populate_skip_file()
        self.known_failures = [
            {'test': '.*test_external_network_visibility',
             'reason': 'Tempest test "external network visibility" fails',
             'lp': 'https://bugs.launchpad.net/tripleo/+bug/1577769'},
            {'test': 'tempest.api.data_processing',
             'reason': 'tempest.api.data_processing tests failing on newton',
             'bz': 'https://bugzilla.redhat.com/show_bug.cgi?id=1357667'},
            {'test': 'neutron.tests.tempest.api.test_revisions.TestRevisions',
             'reason': 'New test, need investigation'}]
        self.txt_output = ('# Tempest test "external network visibility" '
                           'fails\n'
                           '.*test_external_network_visibility\n'
                           '# tempest.api.data_processing tests failing on '
                           'newton\n'
                           'tempest.api.data_processing\n'
                           '# New test, need investigation\n'
                           'neutron.tests.tempest.api.test_revisions.'
                           'TestRevisions\n')
        self.yaml_output = ('---\nknown_failures:\n'
                            '- lp: https://bugs.launchpad.net/tripleo/+bug/'
                            '1577769\n'
                            '  reason: Tempest test "external network '
                            'visibility" fails\n'
                            '  test: .*test_external_network_visibility\n'
                            '- bz: https://bugzilla.redhat.com/show_bug.cgi'
                            '?id=1357667\n'
                            '  reason: tempest.api.data_processing tests '
                            'failing on newton\n'
                            '  test: tempest.api.data_processing\n'
                            '- reason: New test, need investigation\n'
                            '  test: neutron.tests.tempest.api.test_'
                            'revisions.TestRevisions\n')
        self.cmd = BugVerifyCmd()
        self.cmd.parse_arguments(['--skip-file', self.tmp_file])

    def tearDown(self):
        os.close(self.fd_file)
        os.unlink(self.tmp_file)

    def _populate_skip_file(self):
        content = '''
        known_failures:
        - test: '.*test_external_network_visibility'
          reason: 'Tempest test "external network visibility" fails'
          lp: 'https://bugs.launchpad.net/tripleo/+bug/1577769'
        - test: 'tempest.api.data_processing'
          reason: 'tempest.api.data_processing tests failing on newton'
          bz: 'https://bugzilla.redhat.com/show_bug.cgi?id=1357667'
        - test: 'neutron.tests.tempest.api.test_revisions.TestRevisions'
          reason: 'New test, need investigation'
        '''
        self.skip_file = open(self.tmp_file, 'w')
        self.skip_file.write(content)
        self.skip_file.close()

    def test_load_skip_file(self):
        known_failures = self.cmd.load_skip_file()
        self.assertEquals(known_failures, self.known_failures)

    def test__print_txt(self):
        output = self.cmd._print_txt(self.known_failures)
        self.assertEquals(output, self.txt_output)

    def test__print_yaml(self):
        output = self.cmd._print_yaml(self.known_failures)
        self.assertEquals(output, self.yaml_output)

    @mock.patch('bugcheck.BugVerifyCmd._print_txt')
    @mock.patch('bugcheck.BugVerifyCmd._print_yaml')
    def test_get_output(self, yaml_mock, txt_mock):
        self.cmd.get_output(self.known_failures, 'txt')
        self.cmd.get_output(self.known_failures, 'yaml')
        yaml_mock.assert_called_once()
        txt_mock.assert_called_once()
        self.assertRaises(ValueError,
                          self.cmd.get_output, self.known_failures, 'xml')

    def test_save_output(self):
        fd, tmp_f = tempfile.mkstemp()
        cmd = BugVerifyCmd()
        cmd.parse_arguments(['--skip-file', self.tmp_file, '--to-file', tmp_f])
        cmd.save_output(self.known_failures, 'txt')
        output = open(tmp_f, 'r').readlines()
        expected = ['# Tempest test "external network visibility" fails\n',
                    '.*test_external_network_visibility\n',
                    '# tempest.api.data_processing tests failing on newton\n',
                    'tempest.api.data_processing\n',
                    '# New test, need investigation\n',
                    'neutron.tests.tempest.api.test_revisions.TestRevisions\n']
        self.assertEquals(output, expected)

        cmd.save_output(self.known_failures, 'yaml')
        output = open(tmp_f, 'r').readlines()
        expected = ['---\n',
                    'known_failures:\n',
                    '- lp: https://bugs.launchpad.net/tripleo/+bug/1577769\n',
                    '  reason: Tempest test "external network visibility" '
                    'fails\n',
                    '  test: .*test_external_network_visibility\n',
                    '- bz: https://bugzilla.redhat.com/show_bug.cgi?'
                    'id=1357667\n',
                    '  reason: tempest.api.data_processing tests failing on '
                    'newton\n',
                    '  test: tempest.api.data_processing\n',
                    '- reason: New test, need investigation\n',
                    '  test: neutron.tests.tempest.api.test_revisions.Tes'
                    'tRevisions\n']
        self.assertEquals(output, expected)

