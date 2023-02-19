
instance_name = 'votr'

var_path = './var'

lock_path = '/run/lock'

session_max_age = 60 * 60 * 24

log_max_age = 60 * 60 * 25

cosign_proxy = None

cosign_proxy_logout = 'https://login.uniba.sk/logout.cgi'

ua_code = None

anketa_season = ''
anketa_end_ymd = (0, 0, 0)

feedback_link = ''

announcement_html = ''

servers = [
    dict(
        title='ais2.uniba.sk + REST',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='cosign-filter-ais2.uniba.sk',
        ais_url='https://ais2.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
        rest_cookie='cosign-filter-votr-api.uniba.sk',
        rest_url='https://votr-api.uniba.sk/',
    ),
    dict(
        title='ais2.uniba.sk',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='cosign-filter-ais2.uniba.sk',
        ais_url='https://ais2.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
    ),
    dict(
        title='ais2-beta.uniba.sk + REST',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-beta.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
        rest_cookie='cosign-filter-int-dev.uniba.sk',
        rest_url='https://int-dev.uniba.sk:8443/beta/',
    ),
    dict(
        title='ais2-beta.uniba.sk',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-beta.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
    ),
    dict(
        title='ais2-test.uniba.sk + REST',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-test.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
        rest_cookie='cosign-filter-int-dev.uniba.sk',
        rest_url='https://int-dev.uniba.sk:8443/test/',
    ),
    dict(
        title='ais2-test.uniba.sk',
        login_types=('cosignpassword', 'cosigncookie'),
        ais_cookie='JSESSIONID',
        ais_url='https://ais2-test.uniba.sk/',
        ais_login_path='ais/loginCosign.do',
        ais_logout_path='ais/logoutCosign.do',
    ),
    dict(
        title='ais2.euba.sk',
        login_types=('plainpassword',),
        ais_url='https://ais2.euba.sk/',
    ),
    dict(
        title='Demo',
        login_types=('demo',),
    ),
]
