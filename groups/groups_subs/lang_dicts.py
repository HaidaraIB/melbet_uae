from models.Language import Language

TEXTS = {
    Language.ARABIC: {
        "done": "تم ✅",
        "no_groups_yet": "لا يوجد لديك أي غروب تديره بعد",
        "choose_sub": (
            "لوحة تحكم اشتراكاتك:\n" "اضغط على أي غروب للتفاصيل/تجديد/تعطيل"
        ),
        "group_not_found": "لم يتم العثور على هذا الغروب",
        "activate_sub_success": "✅ تم تفعيل الاشتراك لهذا الغروب",
        "deactivate_sub_success": "❌ تم تعطيل الاشتراك لهذا الغروب",
        "pay_msg": (
            "للدفع أو تجديد اشتراك الغروب {}:\n"
            "<a href='{}'>ادفع الآن</a>\n"
            "بعد الدفع اضغط الزر أدناه"
        ),
        "sub_expire_notification": (
            "⏰ تنبيه: سينتهي اشتراك الغروب {} غدًا.\n"
            "يمكنك تجديد الاشتراك عبر الضغط على الزر أدناه"
        ),
        "group_sub_payment_confirmed": "✅ تم تفعيل الاشتراك لهذا الغروب لمدة شهر كامل",
        "use_in_groups": "استخدم هذا الأمر داخل الغروب الذي تريد تفعيله",
        "group_activate_success": "تم ربط الغروب (ID: <code>{}</code>) بحسابك. ستجد التفاصيل في لوحة التحكم الخاصة بك بالضغط على /groups_settings",
    },
    Language.ENGLISH: {
        "done": "Done ✅",
        "no_groups_yet": "You have no groups to manage",
        "choose_sub": (
            "Your group's subscriptions panel:\n"
            "Press any group for details/renew/disable subscription"
        ),
        "group_not_found": "Group not found",
        "activate_sub_success": "Subscription activated on this group ✅",
        "deactivate_sub_success": "Subscription deactivated on this group ❌",
        "pay_msg": (
            "To pay or renew your group subscription {}:\n"
            "<a href='{}'>Pay now</a>\n"
            "After payment press the button below"
        ),
        "sub_expire_notification": (
            "⏰ Note: Your group {} subscription will expire tomorrow:\n"
            "You can renew by pressing the button below"
        ),
        "group_sub_payment_confirmed": "✅ Subscription activated on this group for 1 month",
        "use_in_groups": "Use this command in a group chat",
        "group_activate_success": "Group (ID: <code>{}</code>) linked to your account, you can find details in its panel by pressing /groups_settings",
    },
}

BUTTONS = {
    Language.ARABIC: {
        "activate_sub": "🔓 تفعيل/تجديد شهر",
        "renew_sub": "💳 دفع/تجديد الاشتراك",
        "deactivate_sub": "❌ تعطيل الاشتراك",
        "confirm_payment": "✅ تم الدفع",
    },
    Language.ENGLISH: {
        "activate_sub": "🔓 Activate/Renew Subscription",
        "renew_sub": "💳 Pay/Renew Subscription",
        "deactivate_sub": "❌ Deactivate Subscription",
        "confirm_payment": "✅ Confirm Payment",
    },
}
