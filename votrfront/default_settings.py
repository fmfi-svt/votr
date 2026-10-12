'''Local changes belong in votrfront/local_settings.py.'''

from fladgejt.login import ServerDict as ServerDict

instance_id = 'votr'

instance_title = 'Votr (dev)'

session_max_age = 60 * 60 * 24

root_url = None

ua_code = None

anketa_season = ''
anketa_end_ymd = (0, 0, 0)

feedback_link = ''

announcement_html = ''

servers = [
    ServerDict(
        title='ais2.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2.uniba.sk/',
    ),
    ServerDict(
        title='ais2-beta.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-beta.uniba.sk/',
    ),
    ServerDict(
        title='ais2-test.uniba.sk',
        login_types=('saml_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-test.uniba.sk/',
    ),
    ServerDict(
        title='ais2.euba.sk',
        login_types=('plain_password', 'cookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2.euba.sk/',
    ),
    ServerDict(
        title='Flashback',
        login_types=('flashback',),
        flashbacks_dir='./var/flashbacks',
    ),
]
