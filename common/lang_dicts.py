from models.Language import Language

TEXTS = {
    Language.ARABIC: {
        "welcome_msg": "أهلاً بك...",
        "force_join_msg": (
            f"لبدء استخدام البوت يجب عليك الانضمام الى قناة البوت أولاً\n\n"
            "اشترك أولاً 👇\n"
            "ثم اضغط <b>تحقق ✅</b>"
        ),
        "join_first_answer": "قم بالاشتراك بالقناة أولاً ❗️",
        "settings": "الإعدادات ⚙️",
        "change_lang": "اختر اللغة 🌐",
        "change_lang_success": "تم تغيير اللغة بنجاح ✅",
        "home_page": "القائمة الرئيسية 🔝",
        "request_home_team": "أرسل اسم الفريق الأول",
        "request_away_team": "أرسل اسم الفريق الثاني",
        "request_date": "أرسل تاريخ المباراة بالصيغة التالية YYYY-MM-DD",
        "request_league": "أرسل اسم دوري هذه المباراة",
        "request_league_year": "أرسل عام هذا الدوري",
        "wrong_home_team": "اسم الفريق الأول خاطئ ❗️",
        "wrong_away_team": "اسم الفريق الثاني خاطئ ❗️",
        "no_h2h": "لا يوجد مباراة بين {} و {} في تاريخ {} ❗️",
        "request_game_info": (
            "أرسل بيانات المباراة\n"
            "يمكنك أيضاً اختيار مباراة من مباريات اليوم من القائمة أدناه"
        ),
        "either_teams_wrong": "تعذر العثور على أحد الفريقين.",
        "analyze_game_ai_result": (
            "تفاصيل مباراة:\n\n"
            "• التاريخ:\n<b>{}</b>\n"
            "• البطولة: <b>{}</b>\n"
            "• الملعب: <b>{}</b>\n"
            "• المواجهة: <b>{}</b>\n\n"
            "هل تريد تحليلًا ذكيًا؟ اضغط على زر الدفع."
        ),
        "no_upcoming_games": "لا توجد مواجهة قادمة بين الفريقين.",
        "plz_wait": "الرجاء الانتظار ⏳",
        "soon": "قريباً 🔜",
        "game_smart_analysis": (
            "تحليل ذكي للمباراة:\n\n" "{}\n\n" "للمتابعة اضغط /start"
        ),
        "send_voucher_odd_number": "كم تريد odd القسيمة؟",
        "choose_duration_type": "ما هي مدة القسيمة؟",
        "send_duration_days": "أدخل عدد الأيام بدءا من اليوم، يمكنك إرسال حتى 10 أيام",
        "send_duration_hours": "أرسل عدد الساعات، يمكنك إرسال حتى 72 ساعة",
        "send_odds": "أرسل ال odds، مثال: 2.5",
        "voucher_summary": (
            "ملخص القسيمة\n"
            "- المدة: {}\n"
            "- Odds: {}\n"
            "- السعر: {} AED\n"
            "- التفضيلات:\n{}\n\n"
            "هل تريد المتابعة للدفع؟"
        ),
        "voucher_canceled": "تم إلغاء القسيمة",
        "choose_preferences": "اختر تفضيلاتك من أجل هذه القسيمة",
        "payment_confirmed": "نقوم بتوليد تحليل ذكي، الرجاء الانتظار...⏳",
        "send_league_pref": "أرسل اسم البطولة",
        "gpt_buy_voucher_reply_empty": "لم يتم العثور على نتائج، الرجاء إعادة المحاولة مرة أخرى",
        "send_matches_pref": (
            "أدخل المباريات التي تريدها في القسيمة بهذا الشكل:\n\n"
            "ريال مدريد vs برشلونة\n"
            "مانشستر سيتي vs يونايتد\n\n"
            "ضع كل مباراة على سطر جديد."
        ),
        "choose_plan": "اختر خطة من القائمة أدناه",
        "get_capital_management_plan": "كم تريد أن تضاعف رأس المال؟ (مثال: 3 أو 5 أو 10...)",
        "get_capital_management_days": "خلال كم يوم تريد تحقيق هذا الهدف؟ (مثال: 7، 14، 30)",
        "capital_management_order_summary": (
            "طلبك: مضاعفة رأس المال x{} خلال {} يوم.\n\n" "السعر: {} دولار 💲"
        ),
        "pay_plan_msg": (
            "✅ {}\n\n"
            "{}\n\n"
            "المبلغ المطلوب: {}$\n"
            "الحد الأعلى للأودز لكل قسيمة: {}\n"
            "المدة: {} يوم\n"
            "عدد القسائم: {}\n\n"
            "يرجى إتمام الدفع عبر الرابط التالي: <a href='https://example.com/pay?amount={}'>دفع</a>\n"
        ),
        "pay_capital_msg": (
            "✅ طلب إدارة رأس المال\n\n"
            "المضاعفة المطلوبة: x{}\n"
            "المدة: {} يوم\n"
            "المبلغ المطلوب: {}$\n\n"
            "يرجى إتمام الدفع عبر الرابط التالي: <a href='https://example.com/pay?amount={}'>دفع</a>\n"
        ),
        "payment_success": "تم الدفع بنجاح ✅",
        "payment_failed": "فشل الدفع، أعد المحاولة ❗️",
        "subscription_expired": "تم إلغاء تفعيل اشتراكك. إذا أردت إعادة التفعيل يمكنك الاشتراك من جديد ❗️",
        "already_subscribed": "أنت مشترك بالفعل ❗️",
        "choose_sport": "اختر رياضة من القائمة أدناه",
        "create_account_group_reply": (
            "👋 مرحباً <b>{}</b>!\n\n"
            "🔗 رابطك الشخصي للتسجيل: <a href={}>رابط التسجيل</a>\n"
            "⬇️ لتحميل التطبيق: <a href={}>رابط التحميل</a>\n"
            "⚽️ تسجيل الرياضة: <a href={}>رابط الرياضة</a>\n"
            "استخدم هذا الرابط حتى نتمكّن من تتبع مكافآتك 🎁\n\n"
            "<i><b>سيتم ربط الحساب مع معرفك في أقرب وقت ممكن.\n"
            "يمكنك أن ترسل رقم الحساب مباشرة بعد التسجيل للمحاولة لربط الحساب بشكل فوري.</b></i>"
        ),
        "start_chat_first": "يرجى فتح محادثة خاصة معي أولاً ثم إعادة إرسال كلمة حساب ❗️",
        "link_sent_in_private": "📩 تم إرسال الرابط في الخاص ✅",
        "duplicate_account_not_yours": "رقم حساب مكرر ❗️",
        "account_link_success": "تم ربط الحساب بمعرفك بنجاح ✅",
        "account_not_reg": "هذا الحساب غير مسجل بعد، الرجاء المحاولة لاحقاً ❗️",
        "already_have_an_account": "لديك حساب مسجل بالفعل <code>{}</code> ❗️",
        "link_account_request": (
            "طلب ربط حساب:\n" "{}" "تحقق من التسجيلات وقم بتأكيد الطلب"
        ),
        "link_account_request_submited": "تم إرسال طلبك للمراجعة، ستصلك رسالة عند اكتمال العملية",
    },
    Language.ENGLISH: {
        "welcome_msg": "Welcome...",
        "force_join_msg": (
            f"You have to join the bot's channel in order to be able to use it\n\n"
            "Join First 👇\n"
            "And then press <b>Verify ✅</b>"
        ),
        "join_first_answer": "Join the channel first ❗️",
        "settings": "Settings ⚙️",
        "change_lang": "Choose a language 🌐",
        "change_lang_success": "Language changed ✅",
        "home_page": "Home page 🔝",
        "request_home_team": "Send the First team name",
        "request_away_team": "Send the Second team name",
        "request_date": "Send the Date fo the game in this format YYYY-MM-DD",
        "request_league": "Send the League of this game",
        "request_league_year": "Send the Year Of The League",
        "wrong_home_team": "Wrong First team name ❗️",
        "wrong_away_team": "Wrong Second team name ❗️",
        "no_h2h": "There's no game between {} and {} in {} ❗️",
        "request_game_info": (
            "Send the Game info\n\n"
            "You can also Choose a game of todays games from the list below."
        ),
        "either_teams_wrong": "Can't find one of the teams.",
        "analyze_game_ai_result": (
            "Match Summary:\n\n"
            "• Date: <b>{}</b>\n"
            "• League: <b>{}</b>\n"
            "• Venue: <b>{}</b>\n"
            "• Teams: <b>{}</b>\n\n"
            "Want smart analysis, Press Pay."
        ),
        "no_upcoming_games": "There's no upcoming games between these teams.",
        "plz_wait": "Please Wait ⏳",
        "soon": "Coming Soon 🔜",
        "game_smart_analysis": (
            "Smart Analysis for the game:\n\n" "{}\n\n" "Press /start to continue"
        ),
        "send_voucher_odd_number": "How much is the voucher's odd number you want?",
        "choose_duration_type": "What is the voucher duration?",
        "send_duration_days": "Enter number of days up to 10 days. Time starts from now.\n\nHow many days?",
        "send_duration_hours": "You can enter up to 72 hours. Time starts from now.\n\nEnter number of hours:",
        "send_odds": "Enter the odds you want (e.g. 2.5):",
        "voucher_summary": (
            "Voucher Summary\n"
            "- Duration: {}\n"
            "- Odds: {}\n"
            "- Price: {} AED\n"
            "- Preferences:\n{}\n\n"
            "Continue to Payment?"
        ),
        "voucher_canceled": "Voucher Canceled",
        "choose_preferences": "Choose your preferences for this voucher.",
        "payment_confirmed": "Generating smart slips for you, please wait...⏳",
        "send_league_pref": "Send the League name",
        "gpt_buy_voucher_reply_empty": "No results found, please try again",
        "send_matches_pref": (
            "Send the matches you want in the voucher in this format:\n\n"
            "Barcelona vs Real Madrid\n"
            "Manchester City vs Manchester United\n\n"
            "Put each match in a new line."
        ),
        "choose_plan": "Choose a plan from our plans below",
        "get_capital_management_plan": "How much you want to multiply your capital? (e.g: 3 or 5 or 10...)",
        "get_capital_management_days": "In how many days you want to achieve your goal? (e.g: 7, 14, 30)",
        "capital_management_order_summary": (
            "Your Goal is to grow your capital by x{} in {} Days.\n\n"
            "Price: {} Dollar 💲"
        ),
        "pay_plan_msg": (
            "✅ {}\n\n"
            "{}\n\n"
            "Amount: {}$\n"
            "Max Odds per voucher: {}\n"
            "Duration: {} days\n"
            "Vouchers: {}\n\n"
            "Please complete the payment through the following link: <a href='https://example.com/pay?amount={}'>دفع</a>\n"
        ),
        "pay_capital_msg": (
            "✅ Manage Capital Order\n\n"
            "Multiplier: x{}\n"
            "Duration: {} Days\n"
            "Amount: {}$\n\n"
            "Please complete the payment through the following link: <a href='https://example.com/pay?amount={}'>دفع</a>\n"
        ),
        "payment_success": "Payment Success ✅",
        "payment_failed": "Payment Failed, Try again ❗️",
        "subscription_expired": "Your Subscription has expired, you can activate your subscription by subscribing again ❗️",
        "already_subscribed": "You already have a subscription ❗️",
        "choose_sport": "Choose a sport from the menue below",
        "create_account_group_reply": (
            "👋 Hello <b>{}</b>!\n\n"
            "🔗 Your Personal link to register: <a href={}>Registeration Link</a>\n"
            "⬇️ Download the app: <a href={}>Download Link</a>\n"
            "⚽️ Sport registration: <a href={}>Sport Registration Link</a>\n"
            "🎁 Use This link to be able to keep track of your rewards\n\n"
            "<i><b>The account will be linked with your telegram account automatically soon.\n"
            "you can try to link it immediately by sending me your player id after registration.</b></i>"
        ),
        "start_chat_first": "Please start a chat with me first and then resend the last message you sent ❗️",
        "link_sent_in_private": "📩 Registeration link was sent in private, check your inbox ✅",
        "duplicate_account_not_yours": "Duplicate account number ❗️",
        "account_link_success": "Account link success ✅",
        "account_not_reg": "This account is not registered yet, try again later ❗️",
        "already_have_an_account": "You already have an account <code>{}</code> ❗️",
        "link_account_request": (
            "Link account request:\n" "{}" "Check the registeration and confirm"
        ),
        "link_account_request_submited": "Request submited successfully, you'll recieve a message when it's done",

    },
}

BUTTONS = {
    Language.ARABIC: {
        "check_joined": "تحقق ✅",
        "bot_channel": "قناة البوت 📢",
        "back_button": "الرجوع 🔙",
        "settings": "الإعدادات ⚙️",
        "lang": "اللغة 🌐",
        "back_to_home_page": "العودة إلى القائمة الرئيسية 🔙",
        "buy_voucher": "شراء قسيمة 🎟",
        "analyze_game": "تحليل مباراة ⚽️",
        "pay": "💳 الدفع",
        "duration_days": "أيام",
        "duration_hours": "ساعات",
        "confirm_payment": "المتابعة والدفع ✅",
        "cancel_voucher": "إلغاء ❌",
        "choose_pref_for_me": "اختر لي",
        "choose_pref_league": "من بطولة محددة",
        "choose_pref_sport": "من رياضة محددة",
        "choose_pref_matches": "من مباريات محددة",
        "prev": "⬅️ السابق",
        "next": "التالي ➡️",
        "our_plans": "خططنا 🗂",
        "payment_done": "تم الدفع ✅",
        "use_sub": "استخدام الاشتراك",
        "football": "⚽️ كرة القدم",
        "basketball": "🏀 كرة السلة",
        "american_football": "🏈 كرة القدم الأمريكية",
        "hockey": "🏒 هوكي الجليد",
    },
    Language.ENGLISH: {
        "check_joined": "Verify ✅",
        "bot_channel": "Bot's Channel 📢",
        "back_button": "Back 🔙",
        "settings": "Settings ⚙️",
        "lang": "Language 🌐",
        "back_to_home_page": "Back to home page 🔙",
        "buy_voucher": "Buy Voucher 🎟",
        "analyze_game": "Analyze Game ⚽️",
        "pay": "💳 Pay",
        "duration_days": "Days",
        "duration_hours": "Hours",
        "confirm_payment": "Continue to Payment ✅",
        "cancel_voucher": "Cancel ❌",
        "choose_pref_for_me": "Choose For Me",
        "choose_pref_league": "Specific League",
        "choose_pref_sport": "Specific Sport",
        "choose_pref_matches": "Specific Matches",
        "prev": "⬅️ Previous",
        "next": "Next ➡️",
        "our_plans": "Our Plans 🗂",
        "payment_done": "Payment Done ✅",
        "use_sub": "Use Subscription",
        "football": "Football ⚽️",
        "basketball": "Basketball 🏀",
        "american_football": "American Football 🏈",
        "hockey": "Hockey 🏒",
    },
}
