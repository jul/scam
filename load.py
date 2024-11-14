from requests import post
url = lambda table : "http://127.0.0.1:5000/" +table
post(url("user"), params = dict(id=2,  secret_password="aucun", name="jul2", email="j2@j.com", _action="create"), files=dict(pic_file=open("diag.png", "rb").read())).text

