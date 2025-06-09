from models.Language import Language

TEXTS = {
    Language.ARABIC: {
        "receipt_unclear_chars": "النظام: الإيصال يحتوي على أحرف غير واضحة. يرجى إرسال صورة أوضح بجودة عالية.",
        "missing_essential_details": "النظام: لم نتمكن من استخراج التفاصيل الأساسية: {}. إذا لم يحتوي الإيصال على المعلومات المفقودة الرجاء إرسالها يدوياً.",
        "fraud_detected_blacklisted": "النظام: تم اكتشاف محاولة احتيال. هذه العملية (رقم العملية: {}) استخدمها في الأصل المستخدم @{} ({}) في {}. هذه محاولتك رقم {}. لقد تم إضافتك إلى القائمة السوداء.",
        "fraud_detected_warning": "النظام: تم اكتشاف محاولة احتيال. هذه العملية (رقم العملية: {}) استخدمها في الأصل المستخدم @{} ({}) في {}. هذه محاولتك رقم {}. للعلم، في حال وصول عدد المحاولات إلى 5، سيتم إنهاء التعامل معك وإضافتك إلى القائمة السوداء.",
        "receipt_verified_success": "النظام: تم التحقق من الإيصال بنجاح:\n{}",
        "missing_optional_details": "ملاحظة: التفاصيل التالية مفقودة: {}. يُرجى تقديمها يدويًا إذا أمكن.\n",
        "blacklisted_user": "عذرًا، تم إضافتك إلى القائمة السوداء بسبب محاولات احتيال متكررة.",
        "session_link": "🔗 Private {} session link:\n{}",
        "account_belongs_another": "هذا الحساب {} عائد لمستخدم آخر",
        "account_change_failed": "فشل تغيير الحساب ❗️\nالنظام: تم اكتشاف محاولات متكررة لتغيير رقم الحساب. هذه محاولتك رقم {}.",
        "account_updated": "تم تحديث الحساب الخاص بك من {} إلى {}. هذه محاولتك رقم {}",
        "account_saved": "النظام: تم حفظ رقم الحساب {} بنجاح. جاري معالجة الإيداع.",
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
    },
    Language.ENGLISH: {
        "receipt_unclear_chars": "System: The receipt contains unclear characters. Please send a clearer, higher quality image.",
        "missing_essential_details": "System: We couldn't extract the essential details: {}. If the receipt doesn't contain the missing info please provide them manually.",
        "fraud_detected_blacklisted": "System: Fraud attempt detected. This transaction (ID: {}) was sent from another user. This is your attempt number {}. You have been added to the blacklist.",
        "fraud_detected_warning": "System: Fraud attempt detected. This transaction (ID: {}) was sent from another user. This is your attempt number {}. Note that if you reach 5 attempts, you will be blacklisted.",
        "receipt_verified_success": "System: Receipt verified successfully:\n{}",
        "missing_optional_details": "Note: The following details are missing: {}. Please provide them manually if possible.\n",
        "blacklisted_user": "Sorry, you have been blacklisted due to repeated fraud attempts.",
        "session_link": "🔗 Private {} session link:\n{}",
        "account_belongs_another": "This account {} belongs to another user",
        "account_change_failed": "Account change failed ❗️\nSystem: Repeated account change attempts detected. This is your attempt number {}.",
        "account_updated": "Your account has been updated from {} to {}. This is your attempt number {}",
        "account_saved": "System: Account number {} saved successfully. Processing your deposit.",
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
