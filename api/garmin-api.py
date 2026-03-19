from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from urllib.parse import urlparse, parse_qs
from garminconnect import Garmin

# 加载 .env 文件
def load_env():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    print(f"[SERVER] Loading .env from: {env_file}")
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key.strip()] = value.strip()
        print(f"[SERVER] .env loaded successfully")
    else:
        print(f"[SERVER] WARNING: .env file not found at {env_file}")

load_env()

# Garmin 认证配置 - 从环境变量读取
GARMIN_EMAIL = os.environ.get("GARMIN_EMAIL", "")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD", "")
print(f"[SERVER] GARMIN_EMAIL: {GARMIN_EMAIL}")
print(f"[SERVER] GARMIN_PASSWORD: {'*' * len(GARMIN_PASSWORD) if GARMIN_PASSWORD else 'NOT SET'}")

# 缓存 Garmin 客户端实例（生产环境应该使用数据库或 Redis）
garmin_client = None


class GarminAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """设置 CORS 头，允许前端跨域调用"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self._set_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error(self, message, status=400):
        """发送错误响应"""
        self._send_json_response({
            "success": False,
            "error": message
        }, status)

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # 路由分发
        if path == '/api/health':
            self._handle_health_check()
        elif path == '/api/garmin/sync':
            self._handle_garmin_sync()
        elif path == '/api/garmin/status':
            self._handle_garmin_status(query_params)
        elif path == '/api/garmin/activities':
            self._handle_garmin_activities(query_params)
        elif path == '/api/garmin/hrv':
            self._handle_garmin_hrv(query_params)
        elif path == '/api/garmin/sleep':
            self._handle_garmin_sleep(query_params)
        else:
            self._send_error("API endpoint not found", 404)

    def _handle_health_check(self):
        """健康检查接口"""
        self._send_json_response({
            "success": True,
            "message": "FitCoach Garmin API is running",
            "garmin_configured": bool(GARMIN_EMAIL and GARMIN_PASSWORD)
        })

    def _init_garmin_client(self):
        """初始化 Garmin 客户端（带认证缓存）"""
        global garmin_client

        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            return None

        if garmin_client is None:
            try:
                garmin_client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
                # 登录获取 token
                garmin_client.login()
                print("[SUCCESS] Garmin login successful")
            except Exception as e:
                print(f"[ERROR] Garmin login failed: {e}")
                garmin_client = None

        return garmin_client

    def _handle_garmin_sync(self):
        """同步 Garmin 数据"""
        print("[SYNC] Starting Garmin sync...")
        client = self._init_garmin_client()
        if not client:
            print("[SYNC] Error: Garmin client not initialized")
            self._send_error("Garmin 未配置或登录失败，请检查环境变量")
            return

        try:
            print("[SYNC] Getting user profile...")
            # 获取用户资料
            user_profile = client.get_user_profile()
            print(f"[SYNC] User profile: {user_profile.get('fullName', 'Unknown')}")

            # 获取今日数据
            from datetime import datetime, timedelta
            today = datetime.now().strftime("%Y-%m-%d")

            # 获取活动数据
            print("[SYNC] Getting activities...")
            activities = client.get_activities(0, 10)  # 最近10次活动
            print(f"[SYNC] Activities: {len(activities) if activities else 0}")

            # 使用 get_user_summary 获取今日数据
            print("[SYNC] Getting daily summary...")
            summary = client.get_user_summary(today)
            print(f"[SYNC] Summary keys: {list(summary.keys()) if summary else 'None'}")

            # 获取最近的完整数据（今天可能没有完整数据）
            recent_data_date = today
            recent_summary = summary

            # 如果今天没有完整数据，尝试获取活动日期的数据
            if not summary or not (summary.get('includesWellnessData') or summary.get('includesActivityData')):
                if activities:
                    latest_activity = activities[0]
                    activity_date_str = latest_activity.get('startTimeLocal', '')
                    if activity_date_str:
                        recent_data_date = activity_date_str.split(' ')[0]
                        print(f"[SYNC] Trying activity date: {recent_data_date}")
                        recent_summary = client.get_user_summary(recent_data_date)

            # 获取设备信息
            print("[SYNC] Getting devices...")
            devices = client.get_devices()
            print(f"[SYNC] Devices: {len(devices) if devices else 0}")

            # 提取关键数据
            print(f"[SYNC] Extracting data from {recent_data_date}")

            # 从 user_summary 中提取数据
            hrv_value = None  # HRV 数据可能在单独的 API 中
            sleep_score = None  # 睡眠数据需要从 sleep API 获取
            body_battery = recent_summary.get('bodyBatteryMostRecentValue') if recent_summary else None
            stress_level = recent_summary.get('averageStressLevel') if recent_summary else None

            # 尝试获取睡眠数据
            try:
                sleep_data = client.get_sleep_data(recent_data_date)
                if sleep_data and 'dailySleepDTO' in sleep_data:
                    sleep_score = sleep_data['dailySleepDTO'].get('sleepScore')
            except:
                pass

            # 尝试获取 HRV 数据
            try:
                hrv_data = client.get_hrv_data(recent_data_date)
                if hrv_data and isinstance(hrv_data, dict):
                    hrv_value = hrv_data.get('lastNightAvg') if 'lastNightAvg' in hrv_data else None
            except:
                pass

            # 其他有用的数据
            total_steps = recent_summary.get('totalSteps') if recent_summary else None
            active_calories = recent_summary.get('activeKilocalories') if recent_summary else None
            total_distance = recent_summary.get('totalDistanceMeters') if recent_summary else None
            resting_hr = recent_summary.get('restingHeartRate') if recent_summary else None

            response_data = {
                "success": True,
                "lastSync": datetime.now().isoformat(),
                "dataDate": recent_data_date,
                "user": {
                    "name": user_profile.get("fullName", "Unknown"),
                    "displayName": user_profile.get("displayName", "Unknown"),
                },
                "devices": devices if devices else [],
                "data": {
                    "hrv": hrv_value,
                    "sleepScore": sleep_score,
                    "bodyBattery": body_battery,
                    "stressLevel": stress_level,
                    "totalSteps": total_steps,
                    "activeCalories": active_calories,
                    "totalDistance": round(total_distance / 1000, 2) if total_distance else None,  # 转换为公里
                    "restingHR": resting_hr,
                    "activitiesCount": len(activities) if activities else 0,
                }
            }

            print("[SYNC] Sync completed successfully")
            print(f"[SYNC] Body Battery: {body_battery}")
            print(f"[SYNC] Stress Level: {stress_level}")
            print(f"[SYNC] Total Steps: {total_steps}")
            self._send_json_response(response_data)

        except Exception as e:
            print(f"[SYNC] Error: {e}")
            import traceback
            traceback.print_exc()
            self._send_error(f"同步失败: {str(e)}", 500)

    def _handle_garmin_status(self, query_params):
        """获取 Garmin 设备状态和今日摘要"""
        client = self._init_garmin_client()
        if not client:
            self._send_error("Garmin 未配置")
            return

        try:
            from datetime import datetime, timedelta

            today = datetime.now().strftime("%Y-%m-%d")

            # 获取设备信息
            devices = client.get_devices()

            # 获取今日健康数据
            steps_data = client.get_steps_data(today)
            heart_rate = client.get_heart_rates(today, today)
            body_battery = client.get_body_battery(today)

            response = {
                "success": True,
                "devices": devices if devices else [],
                "today": {
                    "steps": steps_data.get("totalSteps", 0) if steps_data else 0,
                    "bodyBattery": self._extract_body_battery(body_battery) if body_battery else None,
                    "lastSync": datetime.now().isoformat()
                }
            }

            self._send_json_response(response)

        except Exception as e:
            self._send_error(f"获取状态失败: {str(e)}", 500)

    def _handle_garmin_activities(self, query_params):
        """获取活动列表"""
        client = self._init_garmin_client()
        if not client:
            self._send_error("Garmin 未配置")
            return

        try:
            limit = int(query_params.get("limit", [10])[0])
            start = int(query_params.get("start", [0])[0])

            activities = client.get_activities(start, limit)

            # 格式化活动数据
            formatted_activities = []
            for act in activities:
                formatted_activities.append({
                    "id": act.get("activityId"),
                    "type": act.get("activityType", {}).get("typeKey"),
                    "name": act.get("activityName"),
                    "startTime": act.get("startTimeLocal"),
                    "duration": act.get("duration", 0) / 60,  # 转换为分钟
                    "distance": act.get("distance", 0) / 1000,  # 转换为公里
                    "avgHeartRate": act.get("averageHR"),
                    "maxHeartRate": act.get("maxHR"),
                    "calories": act.get("calories"),
                })

            self._send_json_response({
                "success": True,
                "activities": formatted_activities,
                "total": len(formatted_activities)
            })

        except Exception as e:
            self._send_error(f"获取活动失败: {str(e)}", 500)

    def _handle_garmin_hrv(self, query_params):
        """获取 HRV 数据"""
        client = self._init_garmin_client()
        if not client:
            self._send_error("Garmin 未配置")
            return

        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")

            hrv_data = client.get_hrv_data(today)
            latest_hrv = self._extract_latest_hrv(hrv_data) if hrv_data else None

            self._send_json_response({
                "success": True,
                "hrv": latest_hrv,
                "date": today
            })

        except Exception as e:
            self._send_error(f"获取HRV失败: {str(e)}", 500)

    def _handle_garmin_sleep(self, query_params):
        """获取睡眠数据"""
        client = self._init_garmin_client()
        if not client:
            self._send_error("Garmin 未配置")
            return

        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")

            sleep_data = client.get_sleep_data(today)
            sleep_score = self._extract_sleep_score(sleep_data) if sleep_data else None

            self._send_json_response({
                "success": True,
                "sleepScore": sleep_score,
                "date": today
            })

        except Exception as e:
            self._send_error(f"获取睡眠数据失败: {str(e)}", 500)

    # ========== 辅助函数 ==========

    def _extract_latest_hrv(self, hrv_data):
        """从 HRV 数据中提取最新值"""
        if not hrv_data or not isinstance(hrv_data, dict):
            return None

        # garminconnect 返回的数据格式可能是 { "hrvSummary": { "lastNightAvg": 54 } }
        # 需要根据实际返回格式调整
        if "hrvSummary" in hrv_data:
            return hrv_data["hrvSummary"].get("lastNightAvg")

        # 或者其他可能的格式
        if "dailyAvgHrv" in hrv_data:
            return hrv_data["dailyAvgHrv"]

        return None

    def _extract_sleep_score(self, sleep_data):
        """从睡眠数据中提取睡眠评分"""
        if not sleep_data or not isinstance(sleep_data, dict):
            return None

        # 可能的格式
        if "sleepScore" in sleep_data:
            return sleep_data["sleepScore"]

        if "dailySleepDTO" in sleep_data:
            return sleep_data["dailySleepDTO"].get("sleepScore")

        return None

    def _extract_body_battery(self, body_battery_data):
        """从身体电量数据中提取最新值"""
        if not body_battery_data:
            return None

        # body_battery_data 是一个列表
        if isinstance(body_battery_data, list):
            if body_battery_data:
                # 返回最新的身体电量值
                return body_battery_data[-1].get("bodyBatteryValue") if isinstance(body_battery_data[-1], dict) else body_battery_data[-1]
            return None

        # 如果是字典格式（旧版本兼容）
        if isinstance(body_battery_data, dict):
            if "bodyBatteryValue" in body_battery_data:
                return body_battery_data["bodyBatteryValue"]
            if "lastBodyBattery" in body_battery_data:
                return body_battery_data["lastBodyBattery"]

        return None

    def _extract_avg_stress(self, stress_data):
        """从压力数据中提取平均值"""
        if not stress_data or not isinstance(stress_data, dict):
            return None

        # 可能的格式
        if "avgStressLevel" in stress_data:
            return stress_data["avgStressLevel"]

        if "stressLevel" in stress_data:
            return stress_data["stressLevel"]

        return None

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=3000):
    """启动开发服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, GarminAPIHandler)
    print(f"\n{'='*50}")
    print(f"FitCoach Garmin API Server")
    print(f"{'='*50}")
    print(f"[SERVER] Running on http://localhost:{port}")
    print(f"[API] Endpoints:")
    print(f"   - GET /api/health")
    print(f"   - GET /api/garmin/sync")
    print(f"   - GET /api/garmin/status")
    print(f"   - GET /api/garmin/activities")
    print(f"   - GET /api/garmin/hrv")
    print(f"   - GET /api/garmin/sleep")
    print(f"{'='*50}\n")
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
