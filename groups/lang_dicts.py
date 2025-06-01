from models.Language import Language

TEXTS = {
    Language.ARABIC: {
        "choose_lang": "اختر لغة النشر في الغروب",
        "choose_dialect": "اختر اللهجة المحلية",
        "choose_sports": "اختر أنواع الرياضات المرغوبة (يمكنك اختيار أكثر من نوع)",
        "choose_leagues": "اختر الدوريات لـ {}",
        "prefs_save_success": "تم حفظ تفضيلات الغروب بنجاح ✅",
        "operation_canceled": "تم إلغاء العملية",
        "admin_only": "فقط الأدمن يمكنه القيام بهذه العملية ❗️",
    },
    Language.ENGLISH: {
        "choose_lang": "Choose the language you want to post in",
        "choose_dialect": "Choose the dialect",
        "choose_sports": "Choose sports (You can choose more than one)",
        "choose_leagues": "Choose the leagues for {}",
        "prefs_save_success": "Group Preferences saved successfully ✅",
        "operation_canceled": "Operation Canceled",
        "admin_only": "Admins only operation ❗️",
    },
}

BUTTONS = {
    Language.ARABIC: {
        "save": "حفظ 💾",
        "cancel": "إلغاء ❌",
        "continue": "متابعة ⬅️",
    },
    Language.ENGLISH: {
        "save": "Save 💾",
        "cancel": "Cancel ❌",
        "continue": "⬅️ Continue",
    },
}
