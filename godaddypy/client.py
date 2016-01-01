import logging

import requests

__all__ = ['GoDaddyAPI']

logging.basicConfig(filename=__name__ + '.log',
                    filemode='a',
                    level=logging.DEBUG)


def _get(url, method_name, **kwargs):
    resp = requests.get(url, **kwargs)
    _log_response_from_method('get', method_name, resp)
    _validate_response_success(resp)
    return resp


def _put(url, method_name, **kwargs):
    resp = requests.put(url, **kwargs)
    _log_response_from_method('put', method_name, resp)
    _validate_response_success(resp)
    return resp


def _log(message):
    logging.info(message)


def _log_response_from_method(req_type, func_name, resp):
    logging.info('[{req_type}] {func_name} response: {resp}'.format(func_name=func_name, resp=resp,
                                                                    req_type=req_type.upper()))
    logging.debug('Response data: {}'.format(resp.content))


def _remove_key_from_dict(dictionary, key_to_remove):
    return {key: value for key, value in dictionary.items() if key != key_to_remove}


def _validate_response_success(response):
    if response.status_code != 200:
        raise BadResponse(response.json())


class GoDaddyAPI(object):
    API_TEMPLATE = 'https://api.godaddy.com/v1'

    GET_DOMAINS = '/domains'
    GET_DOMAIN = '/domains/{domain}'
    GET_RECORDS_TYPE_NAME = '/domains/{domain}/records/{type}/@'
    PUT_RECORDS_TYPE_NAME = '/domains/{domain}/records/{type}/{name}'
    PATCH_RECORDS = '/domains/{domain}/records'
    PUT_RECORDS = '/domains/{domain}/records'

    _account = None

    def __init__(self, account):
        self._account = account

    def _get_headers(self):
        return self._account.get_auth_headers()

    def scope_control_account(self, account):
        if account is None:
            return self._account
        else:
            return account

    def get_domains(self):
        url = self.API_TEMPLATE + self.GET_DOMAINS
        data = _get(url, method_name=self.get_domains.__name__, headers=self._get_headers()).json()

        domains = list()
        for item in data:
            domain = item['domain']
            if item['status'] == 'ACTIVE':
                domains.append(domain)
                _log('Discovered domains: {}'.format(domain))

        return domains

    def get_api_url(self):
        return self.API_TEMPLATE

    def get_domain_info(self, domain):
        url = self.API_TEMPLATE + self.GET_DOMAIN.format(domain=domain)
        return _get(url, method_name=self.get_domain_info.__name__, headers=self._get_headers()).json()

    def get_a_records(self, domain):
        url = self.API_TEMPLATE + self.GET_RECORDS_TYPE_NAME.format(domain=domain, type='A')
        data = _get(url, method_name=self.get_a_records.__name__, headers=self._get_headers()).json()

        _log('Retrieved {} records from {}.'.format(len(data), domain))

        return data

    def put_new_a_records(self, domain, records):
        url = self.API_TEMPLATE + self.PUT_RECORDS_TYPE_NAME.format(domain=domain, type='A', name='@')
        _put(url, json=records, method_name=self.get_a_records.__name__, headers=self._get_headers())
        _log('Updated {} records @ {}'.format(len(records), domain))

    def update_ip(self, ip):
        for domain in self.get_domains():
            records = self.get_a_records(domain)

            for record in records:
                data = {'data': ip}
                record.update(data)

            self.put_new_a_records(domain, records)


class BadResponse(Exception):
    def __init__(self, message, *args, **kwargs):
        self._message = message
        super(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        return 'Response Data: {}'.format(self._message)