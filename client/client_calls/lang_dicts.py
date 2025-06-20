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
        "deposit_failed": ("فشل الإيداع، رسالة الخطأ:\n" "{}"),
        "unexpected_session_error": "حدث خطأ غير متوقع",
        "player_account_set": "تم اختيار رقم الحساب",
        "payment_method_set": "تم اختيار وسيلة الدفع",
        "stripe_payment_text": (
            f"الرجاء الدفع عبر الرابط أدناه ثم الضغط على <b>تم ✅</b> عند إتمام العملية\n"
            "ملاحظة: هناك رسوم إضافية قدرها <b>3% بالإضافة إلى 1 درهم</b> من إجمالي المبلغ المحول\n"
            "مثلاً عند تحويل 10 درهم يكون المبلغ الذي سيتم إيداعه في حسابك <b>10 - (10 * 0.03 -1) = 8.7 درهم</b>"
        ),
        "provide_withdrawal_info": "الرجاء إرسال <b>كود السحب ومعلومات محفظتك</b>.",
        "payemnt_method_info": (
            "تفاصيل الدفع الخاصة ب <b>{}</b>:\n"
            "<code>{}</code>\n"
            "الرجاء إرسال صورة لإيصال الدفع عند إتمام العملية."
        ),
        "progress_msg": (
            "🚀 أنت على الطريق الصحيح نحو جائزتك!\n\n"
            "بقي لك فقط إيداع {} {} في {} أيام مختلفة لتستلم مكافأتك المميزة 🎁\n\n"
            "استمر بالإيداع، وكل عملية تقربك أكثر لتحقيق الشروط والفوز بالجائزة!\n\n"
            "✨ لا تدع الفرصة تفوتك — تابع التقدم!\n\n"
            "<i>ينتهي العرض بتاريخ:\n{}</i>"
        ),
        "offer_completed_msg": (
            "🎉 تهانينا! لقد أكملت جميع شروط العرض بنجاح.\n"
            "✅ ستتم إضافة جائزتك إلى حسابك الأساسي تلقائيًا.\n\n"
            "استمر في نشاطك على منصتنا للاستفادة من المزيد من العروض والمكافآت قريبًا!"
        ),
        "select_payment_method_first": "الرجاء اختيار وسيلة دفع من الرسالة المثبتة أولاً، أو إتمام الدفع عبر الرابط المرسل إن كنا قد أرسلنا رابطاً إليك",
        "receipt_in_withdraw_session": "الإيصالات مقبولة في جلسات الإيداع فقط، معلومات السحب يجب إرسالها يدوياً.",
        "congrats_txt": (
            "🎁 تهانينا! لقد حصلت على قسيمة توقعات مجانية 🔥\n\n"
            "بمناسبة إيداعك الأخير بقيمة 100 درهم أو أكثر (أو 100 ألف ليرة سورية)، نقدم لك هدية مميزة: قسيمة توقعات مجانية يمكنك استخدامها لأي مباراة من اختيارك!\n\n"
            "لا تتردد في الاستفادة من فرصتك الجديدة، ونتمنى لك حظًا موفقًا في توقعاتك القادمة! ⚽️✨"
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
        "deposit_failed": ("Deposit failed, error message:\n" "{}"),
        "unexpected_session_error": "Unexpected Error",
        "player_account_set": "Player Account Set",
        "payment_method_set": "Payment Method Set",
        "stripe_payment_text": (
            f"Please pay through the link below and press <b>Done ✅</b> when the payment is done\n"
            "Note that there's a fee of <b>3% plus 1 AED</b> on the total amount you'll transfer\n"
            "for example transferring 10 AED will give you <b>10 - (10 * 0.03 -1) = 8.7 AED</b>"
        ),
        "provide_withdrawal_info": "Please Provide the <b>Withdrawal Code</b> and your <b>Payment Info</b>.",
        "payemnt_method_info": (
            "The Payment info of <b>{}</b>:\n"
            "<code>{}</code>\n"
            "Please send a photo of the receipt after completing the transaction."
        ),
        "progress_msg": (
            "🚀 You're on the right track to your reward!\n\n"
            "You only need to deposit {} {} on {} different days to claim your special bonus 🎁\n\n"
            "Keep depositing—every step brings you closer to winning!\n\n"
            "✨ Don't miss out — keep progressing!\n\n"
            "<i>Offer expires at: {}</i>"
        ),
        "offer_completed_msg": (
            "🎉 Congratulations! You have successfully completed all the offer requirements.\n"
            "✅ Your reward will be added to your main account automatically.\n\n"
            "Keep being active on our platform to enjoy more offers and rewards soon!"
        ),
        "select_payment_method_first": "Please select a payment method from the pinned message first or complete the payment through the link if one was sent",
        "receipt_in_withdraw_session": "Receipts can only be send in deposit sessions, withdraw info must be provided manualy.",
        "congrats_txt": (
            "🎁 Congratulations! You’ve received a free prediction voucher 🔥\n\n"
            "With your latest deposit of 100 AED or more (or 100,000 Syrian Pounds), you've unlocked a special gift: a free prediction voucher that you can use for any match of your choice!\n\n"
            "Don't miss your chance—make the most of your new opportunity and good luck with your predictions! ⚽️✨"
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


BUTTONS = {
    Language.ARABIC: {
        "link": "الرابط 🔗",
        "done": "تم ✅",
    },
    Language.ENGLISH: {
        "link": "Link 🔗",
        "done": "Done ✅",
    },
}
