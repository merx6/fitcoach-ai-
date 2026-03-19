# Garmin API 调试指南

## 🚀 快速开始

### 本地测试（推荐先测试）

#### 步骤 1：安装依赖

```bash
pip install garminconnect
```

#### 步骤 2：设置环境变量

**Windows PowerShell:**
```powershell
$env:GARMIN_EMAIL='your-email@example.com'
$env:GARMIN_PASSWORD='your-password'
```

**Linux/Mac:**
```bash
export GARMIN_EMAIL='your-email@example.com'
export GARMIN_PASSWORD='your-password'
```

#### 步骤 3：运行测试脚本

```bash
cd api
python test_garmin.py
```

如果测试成功，你会看到类似这样的输出：

```
✅ 登录成功！

1️⃣  获取用户资料...
   ✅ 用户名: John Doe
   ✅ 昵称: John

2️⃣  获取设备信息...
   ✅ 设备数量: 1
      1. fēnix 7

3️⃣  获取今日步数 (2025-03-19)...
   ✅ 步数: 8234

...
```

#### 步骤 4：启动本地服务器

```bash
# Windows
start.bat

# Linux/Mac
python garmin-api.py
```

服务器启动后，访问 `http://localhost:3000/api/health` 测试连接。

### 在浏览器中测试

1. 打开 `index.html`（本地文件）
2. 点击左侧导航的 "Garmin"
3. 点击 "立即同步" 按钮
4. 观察数据是否更新

## 🐛 常见问题排查

### 问题 1：Python 脚本运行时 ImportError

**错误信息:**
```
ModuleNotFoundError: No module named 'garminconnect'
```

**解决方法:**
```bash
pip install garminconnect
```

### 问题 2：登录失败

**错误信息:**
```
❌ Garmin 登录失败: AuthenticationException
```

**可能原因:**
1. 邮箱或密码错误
2. 账号被锁定（多次输入错误密码）
3. Garmin 需要二次验证

**解决方法:**
1. 先在 Garmin Connect 网站（https://connect.garmin.com）手动登录验证
2. 确认环境变量中的邮箱密码正确
3. 如果账号被锁定，等待解锁后再试

### 问题 3：API 返回空数据

**现象:**
```
✅ 登录成功！
...
❌ 获取失败
```

**可能原因:**
1. 当天没有数据（如首次使用）
2. Garmin 账号没有绑定设备
3. 数据同步延迟

**解决方法:**
1. 确认 Garmin Connect 网站上有数据
2. 尝试获取昨天的数据
3. 确认设备已正确同步

### 问题 4：前端跨域错误 (CORS)

**错误信息（浏览器控制台）:**
```
Access to XMLHttpRequest at 'http://localhost:3000/api/garmin/sync' from origin 'null' has been blocked by CORS policy
```

**原因:** 本地文件访问 HTTP API 时会被浏览器阻止

**解决方法:**
1. 使用本地 HTTP 服务器（而不是直接打开 HTML 文件）：
   ```bash
   # Python
   python -m http.server 8000
   # 然后访问 http://localhost:8000
   ```

2. 或者使用 `http://localhost:3000` 的 API 服务器自带的前端（如果有的话）

### 问题 5：Vercel 部署后无法连接

**现象:**
- 本地测试成功
- 部署到 Vercel 后 API 返回错误

**排查步骤:**

1. **检查环境变量是否设置:**
   - 登录 Vercel Dashboard
   - 项目 → Settings → Environment Variables
   - 确认 `GARMIN_EMAIL` 和 `GARMIN_PASSWORD` 已设置

2. **查看 Vercel 日志:**
   - 项目 → Deployments → 最新部署 → Logs
   - 查看是否有错误信息

3. **检查域名:**
   - 确认前端 `app.js` 中的 `GARMIN_API_BASE` 指向正确的 Vercel URL
   - 例如：`https://fitcoach-garmin-api.vercel.app`

4. **测试 API 健康检查:**
   - 访问 `https://你的-Vercel-URL/api/health`
   - 应该返回：`{"success":true, "garmin_configured":true}`

## 📊 API 端点测试

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:3000/api/health

# 同步数据
curl http://localhost:3000/api/garmin/sync

# 获取活动
curl http://localhost:3000/api/garmin/activities?limit=5
```

### 使用浏览器测试

直接在浏览器地址栏输入：
```
http://localhost:3000/api/health
```

## 🔍 日志查看

### 查看服务器日志

运行 `python garmin-api.py` 时，所有日志会输出到终端。

### 查看前端日志

1. 打开浏览器开发者工具（F12）
2. 切换到 "Console" 标签
3. 查看是否有错误信息

## 📝 调试技巧

1. **使用 Python 测试脚本**
   - `python test_garmin.py` 会测试所有 API 端点
   - 快速定位问题所在

2. **打印调试信息**
   - 在 `garmin-api.py` 中添加 `print()` 语句
   - 查看数据流

3. **检查 Garmin Connect 网站**
   - 确认数据是否正常显示
   - 排除数据源问题

4. **使用模拟数据**
   - 先用模拟数据验证前端逻辑
   - 再接入真实 API

## 🆘 获取帮助

如果以上方法都无法解决问题：

1. 检查 [garminconnect](https://github.com/cyberjunky/python-garminconnect) 官方文档
2. 查看 Garmin Connect API 限制
3. 提交 Issue 并附上错误日志

## ✅ 验证清单

在部署到生产环境前，确认以下各项：

- [ ] 本地测试脚本运行成功
- [ ] 所有 API 端点返回正确数据
- [ ] 前端可以正常调用 API
- [ ] 环境变量正确设置（不要硬编码密码）
- [ ] CORS 配置正确
- [ ] 错误处理完善
- [ ] Git 仓库中没有 `.env` 文件（已在 `.gitignore` 中）
