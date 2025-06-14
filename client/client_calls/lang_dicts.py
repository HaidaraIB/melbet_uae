from models.Language import Language

TRANSACTION_TYPES = {
    Language.ARABIC: {
        "deposit": "الإيداع",
        "withdraw": "السحب",
    },
    Language.ENGLISH: {
        "deposit": "Deposit",
        "withdraw": "Withdrawal",
    },
}

TEXTS = {
    Language.ARABIC: {
        "blacklisted_user": "عذرًا، تم إضافتك إلى القائمة السوداء بسبب محاولات احتيال متكررة.",
        "session_link": "🔗 Private {} session link:\n{}",
        "no_account": (
            "ليس لديك حساب بعد، يمكنك إنشاء حساب باتباع الخطوات التالية\n\n"
            "1️⃣ عد إلى المجموعة العامة\n"
            "2️⃣ أرسل أحد الكلمات المفتاحية المتعلقة بإنشاء حساب مثل: حساب، إنشاء حساب\n"
            "3️⃣ المدير @MANAGER25628 سيرسل لك رسالة تحتوي على رابط التسجيل\n"
            "4️⃣ تابع خطوات التسجيل وقم باختيار التسجيل بنقرة واحدة\n"
            "5️⃣ عد إلى المحادثة مع المدير @MANAGER25628 وأرسل رقم الحساب الذي أنشأته\n\n"
            "وستتمكن من الإيداع والسحب بشكل طبيعي بعد ذلك."
        ),
        "account_not_reg": "لم تقم بإنشاء هذا الحساب عبر الرابط المرسل إليك ❗️",
        "no_text_extracted_from_photo": "عذرًا، لم يتم استخراج أي نص من الصورة. يرجى إرسال صورة أوضح بجودة عالية.",
        "google_vision_error": "عذرًا، حدث خطأ أثناء معالجة الصورة. يرجى إرسال صورة أوضح أو التأكد من جودة الصورة.",
        "deposit_approved": "تمت الموافقة على الإيداع رقم <code>{}</code> وإضافة {} {} إلى حسابك <code>{}</code>",
        "withdraw_approved": "تمت الموافقة على السحب رقم <code>{}</code> لكود السحب <code>{}</code> لحساب اللاعب <code>{}</code>",
        "transaction_declined": (
            "للأسف، تم رفض طلب {} رقم <code>{}</code>\n" "السبب:\n{}"
        ),
        "withdraw_failed": (
            "فشلت عملية السحب، رسالة الخطأ: {}\n" "تحقق من صحة كود السحب وأعد المحاولة"
        ),
    },
    Language.ENGLISH: {
        "blacklisted_user": "Sorry, you have been blacklisted due to repeated fraud attempts.",
        "session_link": "🔗 Private {} session link:\n{}",
        "no_account": (
            "You don't have an account yet, you can create one by doing the following:\n\n"
            "1️⃣ Go to our group\n"
            "2️⃣ Send an account related keyword like: account, Account or create account etc...\n"
            "3️⃣ The manager @MANAGER25628 will send you a message with the registeration link\n"
            "4️⃣ Follow the registeration link and make an account with one click\n"
            "5️⃣ Go back to the manager chat and send him your new account number\n\n"
            "and that's it you'll be able to withdraw or deposit normally."
        ),
        "account_not_reg": "Account is not created via the previous registeratin link ❗️",
        "no_text_extracted_from_photo": "Sorry, I was unable to extract any text from this photo, please try again with a better photo resollution",
        "google_vision_error": "Sorry, an error occured while processing your image, please try with a more clear one.",
        "deposit_approved": "Deposit number <code>{}</code> has been approved and a <b>{} {}</b> is added to your account <code>{}</code>",
        "withdraw_approved": "Withdrawal number <code>{}</code> has been approved for the code <code>{}</code> on account <code>{}</code>",
        "transaction_declined": (
            "Unfortunatly, {} number <code>{}</code> has been decline\n" "Reason:\n{}"
        ),
        "withdraw_failed": (
            "Withdrawal failed with error message: {}\n"
            "check if your withdrawal code is correct and try again"
        ),
    },
}


ERROR_TEXTS = {
    Language.ARABIC: {
        "pin_error": "خطأ في تثبيت الرسالة: {}",
        "permission_error": "خطأ في تعديل الأذونات: {}",
        "session_start_failed": "فشل في بدء الجلسة للمستخدم {} بسبب خطأ في الكيان: {}",
        "unexpected_session_error": "خطأ غير متوقع في بدء الجلسة للمستخدم {}: {}",
    },
    Language.ENGLISH: {
        "pin_error": "Error pinning message: {}",
        "permission_error": "Error modifying permissions: {}",
        "session_start_failed": "Failed to start session for user {} due to entity error: {}",
        "unexpected_session_error": "Unexpected error starting session for user {}: {}",
    },
}
