from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class Admin(UpdateFilter):
    def filter(self, update: Update):
        with models.session_scope() as s:
            try:
                return s.get(
                    models.User,
                    update.effective_user.id,
                ).is_admin
            except:
                return False
