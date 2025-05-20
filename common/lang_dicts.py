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
        "request_game_info": "أرسل بيانات المباراة",
        "either_teams_wrong": "تعذر العثور على أحد الفريقين.",
        "analyze_game_ai_result": (
            "أقرب مواجهة بين <b>{}</b> و <b>{}</b>:\n\n"
            "• التاريخ:\n<b>{}</b>\n"
            "• البطولة: <b>{}</b>\n"
            "• الملعب: <b>{}</b>\n"
            "• المواجهة: <b>{}</b>\n\n"
            "هل تريد تحليلًا ذكيًا؟ اضغط على زر الدفع."
        ),
        "no_upcoming_games": "لا توجد مواجهة قادمة بين الفريقين.",
        "plz_wait": "الرجاء الانتظار ⏳",
        "soon": "قريباً 🔜",
        "game_smart_analysis": "تحليل ذكي للمباراة:\n\n{}",
        "send_voucher_odd_number": "كم تريد odd القسيمة؟",
        "choose_duration_type": "ما هي مدة القسيمة؟",
        "send_duration_days": "أدخل عدد الأيام بدءا من اليوم؟",
        "send_duration_hours": "أرسل عدد الساعات، يمكنك إرسال حتى 72 ساعة",
        "send_odds": "أرسل ال odds، مثال: 2.5",
        "voucher_summary": (
            "ملخص القسيمة\n"
            "- الكمية: {} AED\n"
            "- المدة: {}\n"
            "- Odds: {}\n"
            "- التفضيلات: {}\n"
            "- السعر: {} AED\n\n"
            "هل تريد المتابعة للدفع؟"
        ),
        "voucher_canceled": "تم إلغاء القسيمة",
        "send_preferences": (
            "الرجاء كتابة تفضيلاتك من أجل هذه القسيمة.\n"
            "يمكنك ذكر دوريات، فرق (مثال: La Liga, Barcelona).\n"
            "أو اكتب <code>Choose for me</code> إذا لم يكن لديك أي تفضيلات."
        ),
        "payment_confirmed": "نقوم بتوليد تحليل ذكي، الرجاء الانتظار...⏳",
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
        "request_game_info": "Send the Game info",
        "either_teams_wrong": "Can't find one of the teams.",
        "analyze_game_ai_result": (
            "The closest match between <b>{}</b> and <b>{}</b>:\n\n"
            "• Date: <b>{}</b>\n"
            "• League: <b>{}</b>\n"
            "• Venue: <b>{}</b>\n"
            "• Teams: <b>{}</b>\n\n"
            "Want smart analysis, Press Pay."
        ),
        "no_upcoming_games": "There's no upcoming games between these teams.",
        "plz_wait": "Please Wait ⏳",
        "soon": "Coming Soon 🔜",
        "game_smart_analysis": "Smart Analysis for the game:\n\n{}",
        "send_voucher_odd_number": "How much is the voucher's odd number you want?",
        "choose_duration_type": "What is the voucher duration?",
        "send_duration_days": "Enter number of days. Time starts from now.\n\nHow many days?",
        "send_duration_hours": "You can enter up to 72 hours. Time starts from now.\n\nEnter number of hours:",
        "send_odds": "Enter the odds you want (e.g. 2.5):",
        "voucher_summary": (
            "Voucher Summary\n"
            "- Amount: {} AED\n"
            "- Duration: {}\n"
            "- Odds: {}\n"
            "- Preferences: {}\n"
            "- Price: {} AED\n\n"
            "Continue to Payment?"
        ),
        "voucher_canceled": "Voucher Canceled",
        "send_preferences": (
            "Please write your preferences for this voucher.\n"
            "You can mention leagues, teams, or countries (for example: La Liga, Barcelona).\n"
            "Or write <code>Choose for me</code> if you don’t have any preferences."
        ),
        "payment_confirmed": "Generating smart slips for you, please wait...⏳",
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
        "pay": "الدفع 💳",
        "duration_days": "أيام",
        "duration_hours": "ساعات",
        "confirm_payment": "المتابعة والدفع ✅",
        "cancel_voucher": "إلغاء ❌",
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
        "pay": "Pay 💳",
        "duration_days": "Days",
        "duration_hours": "Hours",
        "confirm_payment": "Continue to Payment ✅",
        "cancel_voucher": "Cancel ❌",
    },
}
