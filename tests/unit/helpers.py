import sys
import base64
from testify import TestCase, setup, assert_equal, assert_raises
from .base import ApiTestCase, RighteousTestCase
import righteous
from righteous.api.server_template import _extract_template_id
from righteous.api.base import _build_headers
from righteous import config
from mock import patch


class RequestsTestCase(TestCase):

    def test_request(self):
        username, password, account_id = 'user', 'pass', 'account_id'
        righteous.init(username, password, account_id, debug=False)
        headers = {'X-API-VERSION': '1.0'}

        with patch('righteous.api.base.requests') as mock_requests:
            righteous.api.base._request('/test')
            mock_requests.request.assert_called_once_with('GET',
                'https://my.rightscale.com/api/acct/account_id/test',
                headers=headers, config={}, data=None)

    def test_request_no_prepend(self):
        username, password, account_id = 'user', 'pass', 'account_id'
        righteous.init(username, password, account_id, debug=False)
        headers = {'X-API-VERSION': '1.0'}

        with patch('righteous.api.base.requests') as mock_requests:
            righteous.api.base._request('/test', prepend_api_base=False)
            mock_requests.request.assert_called_once_with('GET', '/test',
                headers=headers, config={}, data=None)


class ExtractTemplateIdTestCase(ApiTestCase):

    def test_ec2_template_href(self):
        assert_equal(_extract_template_id('https://my.rightscale.com/api/acct/'
            'account_id/ec2_server_templates/12345'), '12345')

    def test_unknown_ec2_template_href(self):
        assert not _extract_template_id('https://my.rightscale.com/api/acct/'
            'account_id/rackspace_server_templates/12345')


class BuildHeaderTestCase(RighteousTestCase):

    def test_build_headers(self):
        assert_equal(_build_headers(), {'X-API-VERSION': '1.0'})

    def test_additional_headers(self):
        headers = {'foo': 'bar'}
        assert_equal(_build_headers(headers),
            {'X-API-VERSION': '1.0', 'foo': 'bar'})

    def test_cookie_headers(self):
        config.settings.cookies = 'cookie_value'
        headers = {'baz': 'bar'}
        assert_equal(_build_headers(headers),
            {'X-API-VERSION': '1.0', 'baz': 'bar', 'Cookie': 'cookie_value'})


class InitialiseTestCase(RighteousTestCase):

    def test_init(self):
        assert_raises(Exception, righteous.init)

    def test_init_with_null_arg(self):
        assert_raises(Exception, righteous.init, 'user', 'pass', None)

    def test_init_with_args(self):
        righteous.init('user', 'pass', 'account')
        assert_equal(righteous.config.settings.username, 'user')

    def test_init_with_kwargs(self):
        righteous.init('user', 'pass', 'account', debug=True, foo='bar')
        assert_equal(righteous.config.settings.username, 'user')
        assert_equal(righteous.config.settings.debug, sys.stderr)
        assert_equal(righteous.config.settings.create_server_parameters['foo'],
            'bar')

    def test_init_deployment_id(self):
        righteous.init('user', 'pass', 'account', default_deployment_id='22')

        assert_equal(righteous.config.settings.default_deployment_id, '22')
        server_parameters = righteous.config.settings.create_server_parameters
        assert_equal(server_parameters['deployment_href'],
            'https://my.rightscale.com/api/acct/account/deployments/22')


class LoginTestCase(RighteousTestCase):

    @setup
    def setup(self):
        self.setup_patching('righteous.api.base._request')

    def test_login(self):
        assert_raises(Exception, righteous.login)

    def test_login_failure(self):
        assert not righteous.login('foo', 'bar', 'buzz')

    def test_login_with_init_credentials(self):
        username, password, account_id = 'user', 'pass', 'account_id'
        auth = base64.encodestring('%s:%s' % (username, password))[:-1]

        righteous.init(username, password, account_id)

        self.response.status_code = 204
        self.response.headers['set-cookie'] = 'cookie_value'
        login_result = righteous.login()
        assert login_result
        self.request.assert_called_once_with('/login',
            headers={'Authorization': 'Basic %s' % auth})

    def test_login_with_credentials(self):
        username, password, account_id = 'foo', 'bar', '123'
        auth = base64.encodestring('%s:%s' % (username, password))[:-1]

        self.response.status_code = 204
        self.response.headers['set-cookie'] = 'cookie_value'
        login_result = righteous.login(username, password, account_id)
        assert login_result
        self.request.assert_called_once_with('/login',
            headers={'Authorization': 'Basic %s' % auth})