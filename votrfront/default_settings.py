
instance_id = 'votr'

instance_title = 'Votr (dev)'

var_path = './var'

session_max_age = 60 * 60 * 24

log_max_age = 60 * 60 * 25

root_url = None

ua_code = None

anketa_season = ''
anketa_end_ymd = (0, 0, 0)

feedback_link = ''

announcement_html = ''

servers = [
    dict(
        title='ais2.uniba.sk + REST',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2.uniba.sk/',
        rest_cookie='JSESSIONID',
        rest_url='https://votr-api.uniba.sk/',
    ),
    dict(
        title='ais2.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2.uniba.sk/',
    ),
    dict(
        title='ais2-beta.uniba.sk + REST',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-beta.uniba.sk/',
        rest_cookie='JSESSIONID',
        rest_url='https://int-dev.uniba.sk:8443/beta/',
    ),
    dict(
        title='ais2-beta.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-beta.uniba.sk/',
    ),
    dict(
        title='ais2-test.uniba.sk + REST',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-test.uniba.sk/',
        rest_cookie='JSESSIONID',
        rest_url='https://int-dev.uniba.sk:8443/test/',
    ),
    dict(
        title='ais2-test.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-test.uniba.sk/',
    ),
    dict(
        title='ais2.euba.sk',
        login_types=('plain_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2.euba.sk/',
    ),
    dict(
        title='Flashback',
        login_types=('flashback',),
        flashbacks_dir='./var/flashbacks',
    ),
]
