from dateutil import tz
from Config import Config

BACK_TO_HOME_PAGE_TEXT = "العودة إلى القائمة الرئيسية 🔙"

HOME_PAGE_TEXT = "القائمة الرئيسية 🔝"

BACK_BUTTON_TEXT = "الرجوع 🔙"


TIMEZONE_NAME = "Asia/Dubai"

TIMEZONE = tz.gettz(TIMEZONE_NAME)


CREATE_ACCOUNT_LINKS = {
    Config.UAE_MONITOR_GROUP_ID: {
        "wlcm": "https://buy785.online/L?tag=d_4467940m_37513c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "apk": "https://buy785.online/L?tag=d_4467940m_63871c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "reg": "https://buy785.online/L?tag=d_4467940m_64133c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "pic": "assets/uae_create_account.jpg",
        "important_note": "uae_create_account_important_note",
    },
    Config.SYR_MONITOR_GROUP_ID: {
        "wlcm": "https://buy785.online/L?tag=d_4468867m_37513c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "apk": "https://buy785.online/L?tag=d_4468867m_63871c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "reg": "https://buy785.online/L?tag=d_4468867m_64133c_{}&pb=a49b407b60cd42b895270d6d8b10b1ed&click_id={}",
        "pic": "assets/syr_create_account.jpg",
        "important_note": "syr_create_account_important_note",
    },
}


MONITOR_GROUPS = [Config.UAE_MONITOR_GROUP_ID, Config.SYR_MONITOR_GROUP_ID]
