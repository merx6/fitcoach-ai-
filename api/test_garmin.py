#!/usr/bin/env python3
"""
FitCoach Garmin API - 本地测试脚本
用于在部署到 Vercel 前测试 API 功能
"""

import os
import sys
import json
from datetime import datetime, timedelta
from garminconnect import Garmin


def test_garmin_connection():
    """测试 Garmin 连接"""
    print("\n" + "="*60)
    print("FitCoach Garmin API - 本地测试")
    print("="*60 + "\n")

    # 从环境变量读取凭据
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        print("❌ 错误：请设置环境变量 GARMIN_EMAIL 和 GARMIN_PASSWORD")
        print("\n使用方法:")
        print("  Windows PowerShell:")
        print("    $env:GARMIN_EMAIL='your-email@example.com'")
        print("    $env:GARMIN_PASSWORD='your-password'")
        print("    python test_garmin.py")
        print("\n  Linux/Mac:")
        print("    export GARMIN_EMAIL='your-email@example.com'")
        print("    export GARMIN_PASSWORD='your-password'")
        print("    python test_garmin.py")
        return False

    try:
        print(f"📧 尝试登录 Garmin Connect...")
        print(f"   用户: {email}\n")

        # 初始化 Garmin 客户端
        client = Garmin(email, password)

        # 登录
        client.login()
        print("✅ 登录成功！\n")

        # 测试各个 API 端点
        print("="*60)
        print("测试数据获取:")
        print("="*60 + "\n")

        # 1. 用户资料
        print("1️⃣  获取用户资料...")
        user_profile = client.get_user_profile()
        if user_profile:
            print(f"   ✅ 用户名: {user_profile.get('fullName', 'N/A')}")
            print(f"   ✅ 昵称: {user_profile.get('displayName', 'N/A')}")
        else:
            print("   ❌ 获取失败")

        # 2. 设备信息
        print("\n2️⃣  获取设备信息...")
        devices = client.get_devices()
        if devices:
            print(f"   ✅ 设备数量: {len(devices)}")
            for i, device in enumerate(devices[:3], 1):
                device_name = device.get("deviceTypeName", "Unknown")
                print(f"      {i}. {device_name}")
        else:
            print("   ❌ 获取失败")

        # 3. 今日步数
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n3️⃣  获取今日步数 ({today})...")
        steps = client.get_steps_data(today)
        if steps:
            print(f"   ✅ 步数: {steps.get('totalSteps', 0)}")
        else:
            print("   ❌ 获取失败")

        # 4. HRV 数据
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\n4️⃣  获取 HRV 数据 ({yesterday} - {today})...")
        hrv_data = client.get_hrv_data(yesterday, today)
        if hrv_data:
            print(f"   ✅ HRV 数据: {json.dumps(hrv_data, ensure_ascii=False, indent=2)}")
        else:
            print("   ❌ 获取失败")

        # 5. 睡眠数据
        print(f"\n5️⃣  获取睡眠数据 ({today})...")
        sleep = client.get_sleep_data(today)
        if sleep:
            sleep_score = sleep.get("sleepScore", "N/A")
            print(f"   ✅ 睡眠评分: {sleep_score}")
        else:
            print("   ❌ 获取失败")

        # 6. 身体电量
        print(f"\n6️⃣  获取身体电量 ({today})...")
        body_battery = client.get_body_battery(today)
        if body_battery:
            print(f"   ✅ 身体电量: {json.dumps(body_battery, ensure_ascii=False, indent=2)}")
        else:
            print("   ❌ 获取失败")

        # 7. 压力数据
        print(f"\n7️⃣  获取压力数据 ({yesterday} - {today})...")
        stress = client.get_stress_data(yesterday, today)
        if stress:
            print(f"   ✅ 压力数据: {json.dumps(stress, ensure_ascii=False, indent=2)}")
        else:
            print("   ❌ 获取失败")

        # 8. 活动列表
        print(f"\n8️⃣  获取最近 5 次活动...")
        activities = client.get_activities(0, 5)
        if activities:
            print(f"   ✅ 活动数量: {len(activities)}")
            for i, act in enumerate(activities[:3], 1):
                act_name = act.get("activityName", "Unknown")
                act_type = act.get("activityType", {}).get("typeKey", "Unknown")
                print(f"      {i}. {act_name} ({act_type})")
        else:
            print("   ❌ 获取失败")

        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("\n可能的原因:")
        print("  1. Garmin 邮箱或密码错误")
        print("  2. Garmin 账号被锁定或需要验证")
        print("  3. 网络连接问题")
        print("  4. Garmin API 限制（请稍后重试）")
        print("\n建议:")
        print("  - 尝试在 Garmin Connect 网站手动登录验证")
        print("  - 检查网络连接")
        print("  - 稍后重试（API 可能有频率限制）")
        return False


if __name__ == "__main__":
    success = test_garmin_connection()
    sys.exit(0 if success else 1)
