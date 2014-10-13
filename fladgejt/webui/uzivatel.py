

class WebuiUzivatelMixin:
    def get_meno_uzivatela(self):
        app = self._open_administracia_studia()

        return app.d.studentTextField.value.split(',')[0]
