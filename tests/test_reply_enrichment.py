from main import format_reply_message, format_reply_with_team_points


def test_format_reply_message_includes_category_alert_block():
    analysis = {
        "risk_score": 8,
        "category": "假投資詐騙",
        "expert_warning": "請勿匯款",
        "category_alert": {
            "canonical_name": "假投資詐騙",
            "statistics": {
                "recent_case_count": 10,
                "total_loss_amount": 2000000,
                "average_loss_amount": 200000,
            },
            "case": {
                "title": "投資群組詐騙",
                "summary": "以保證獲利誘導入金。",
                "loss_range": "10 萬至 200 萬元",
            },
        },
    }

    reply = format_reply_message(analysis)

    assert "防詐補充提醒" in reply
    assert "近期通報案件：約 10 件" in reply
    assert "案例參考｜投資群組詐騙" in reply


def test_format_reply_with_team_points_includes_category_alert_block():
    analysis = {
        "risk_score": 9,
        "category": "假投資詐騙",
        "expert_warning": "請勿點擊連結",
        "category_alert": {
            "canonical_name": "假投資詐騙",
            "statistics": {
                "recent_case_count": 8,
                "total_loss_amount": 1600000,
                "average_loss_amount": 200000,
            },
            "case": {
                "title": "假平台出金卡關",
                "summary": "先給小額獲利，再要求補保證金。",
                "loss_range": "5 萬至 150 萬元",
            },
        },
    }
    team_result = {
        "success": True,
        "points_earned": 18,
        "is_duplicate": False,
        "multiplier_applied": True,
    }

    reply = format_reply_with_team_points(analysis, team_result)

    assert "防詐補充提醒" in reply
    assert "假平台出金卡關" in reply
    assert "18 積分" in reply
