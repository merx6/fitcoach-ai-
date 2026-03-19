# Garmin 数据集成部署指南

## 📋 概述

本指南帮助你将 FitCoach AI 与 Garmin Connect 连接，实现真实的健康数据同步。

## 🏗️ 架构说明

```
┌─────────────────┐      HTTP/HTTPS      ┌─────────────────────┐
│  FitCoach 前端   │ ◄───────────────────► │  Garmin API 后端    │
│ (GitHub Pages)   │                       │  (Vercel Serverless)│
└─────────────────┘                       └──────────┬──────────┘
                                                      │
                                                      │ Garmin Connect API
                                                      ▼
                                              ┌───────────────┐
                                              │ Garmin Cloud  │
                                              └───────────────┘
```

## 📦 项目结构

```
fitcoach-ai-/
├── api/                          # Garmin API 后端
│   ├── garmin-api.py             # Python API 服务
│   ├── package.json              # Vercel 配置
│   ├── requirements.txt          # Python 依赖
│   └── vercel.json               # 部署配置
├── index.html                    # 前端页面
├── app.js                        # 前端逻辑
└── style.css                     # 前端样式
```

## 🚀 部署步骤

### 第 1 步：安装 Vercel CLI

```bash
npm install -g vercel
```

### 第 2 步：准备 Garmin 账号

1. 注册 Garmin 账号（如果没有）
2. 确保可以在 Garmin Connect 网站正常登录
3. 记录邮箱和密码（用于 API 认证）

### 第 3 步：配置环境变量

在 `api/garmin-api.py` 中，通过 Vercel 环境变量配置：

```bash
# 方法 1：通过 Vercel Dashboard
# 1. 访问 https://vercel.com/dashboard
# 2. 选择你的项目
# 3. Settings → Environment Variables
# 4. 添加以下变量：
#    - GARMIN_EMAIL: 你的 Garmin 邮箱
#    - GARMIN_PASSWORD: 你的 Garmin 密码

# 方法 2：通过 CLI
vercel env add GARMIN_EMAIL
vercel env add GARMIN_PASSWORD
```

### 第 4 步：部署到 Vercel

```bash
# 进入 api 目录
cd api

# 登录 Vercel（首次部署）
vercel login

# 部署
vercel --prod
```

部署成功后，你会得到一个 URL，例如：
```
https://fitcoach-garmin-api.vercel.app
```

### 第 5 步：更新前端 API 地址

在 `app.js` 中，修改 `GARMIN_API_BASE`：

```javascript
// 找到第 760 行左右
const GARMIN_API_BASE = 'https://fitcoach-garmin-api.vercel.app'; // 替换为你的 Vercel URL
```

### 第 6 步：推送前端更新

```bash
# 提交代码
git add .
git commit -m "feat: 集成 Garmin API"
git push origin main
```

## 🧪 本地测试

### 启动本地 API 服务器

```bash
# 安装 Python 依赖
pip install garminconnect

# 设置环境变量（Windows PowerShell）
$env:GARMIN_EMAIL = "your-email@example.com"
$env:GARMIN_PASSWORD = "your-password"

# 启动服务器
cd api
python garmin-api.py
```

服务器会在 `http://localhost:3000` 启动。

### 测试 API 端点

```bash
# 健康检查
curl http://localhost:3000/api/health

# 同步数据
curl http://localhost:3000/api/garmin/sync

# 获取活动
curl http://localhost:3000/api/garmin/activities?limit=5
```

## 🔒 安全注意事项

1. **不要在代码中硬编码密码**
   - 使用 Vercel 环境变量
   - 不要提交 `.env` 文件到 Git

2. **使用专用邮箱**
   - 建议为 FitCoach 创建专用的 Garmin 账号
   - 避免使用主账号

3. **定期更换密码**
   - 定期更换 Garmin 密码
   - 更新 Vercel 环境变量

## 📊 API 端点说明

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/garmin/sync` | GET | 同步所有数据 |
| `/api/garmin/status` | GET | 获取设备状态 |
| `/api/garmin/activities` | GET | 获取活动列表 |
| `/api/garmin/hrv` | GET | 获取 HRV 数据 |
| `/api/garmin/sleep` | GET | 获取睡眠数据 |

## 🐛 常见问题

### Q1: 部署后 API 返回 404
**原因**: Vercel 路由配置问题
**解决**: 检查 `vercel.json` 中的 `routes` 配置

### Q2: Garmin 登录失败
**原因**: 密码错误或账号被锁定
**解决**:
- 在 Garmin Connect 网站手动登录验证
- 检查环境变量是否正确设置

### Q3: 跨域错误 (CORS)
**原因**: 后端没有设置 CORS 头
**解决**: 检查 `garmin-api.py` 中的 `_set_cors_headers` 函数

### Q4: 前端无法连接后端
**原因**: API URL 配置错误
**解决**: 确保 `GARMIN_API_BASE` 指向正确的 Vercel URL

## 📈 下一步优化

1. **添加错误重试机制**
   - API 失败时自动重试
   - 离线缓存数据

2. **实时数据同步**
   - 使用 WebSocket 实现实时更新
   - 设置定时自动同步

3. **多用户支持**
   - 添加用户认证
   - 每个用户独立的 Garmin 账号

4. **数据可视化增强**
   - 添加更多图表
   - 导出数据报告

## 📞 支持

如有问题，请提交 Issue 或联系开发者。
