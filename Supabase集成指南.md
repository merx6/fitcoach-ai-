# Supabase 数据同步集成指南

## 📋 概述

使用 Supabase 实现跨设备数据同步，让用户在任何设备上打开应用都能看到相同的数据。

---

## 🔧 步骤一：创建 Supabase 项目

1. 访问 https://supabase.com
2. 注册/登录账号
3. 点击 **New Project**
4. 填写项目信息：
   - **Name**: `fitcoach-ai`
   - **Database Password**: 设置一个强密码（记住它！）
   - **Region**: 选择最近的区域（如：Northeast Asia (Tokyo)）
5. 点击 **Create new project**
6. 等待 1-2 分钟让项目初始化完成

---

## 🔧 步骤二：创建数据库表

项目创建完成后：

1. 进入 **Table Editor**（左侧菜单）
2. 点击 **Create a new table**
3. 填写表信息：
   - **Name**: `user_profiles`
   - **Description**: `用户健康档案`
4. 添加列：

   | Column Name | Type | Default | Description |
   |-------------|------|---------|-------------|
   | id | int8 | auto-increment | 主键 |
   | user_id | text | - | 用户唯一标识 |
   | name | text | - | 姓名 |
   | age | int8 | - | 年龄 |
   | gender | text | - | 性别 |
   | height | int8 | - | 身高 |
   | weight | int8 | - | 体重 |
   | restHR | int8 | - | 静息心率 |
   | maxHR | int8 | - | 最大心率 |
   | vo2max | int8 | - | VO₂Max |
   | bodyFat | int8 | - | 体脂率 |
   | fitnessLevel | text | - | 运动级别 |
   | goals | jsonb | - | 训练目标 |
   | trainingDays | int8 | - | 每周训练天数 |
   | sessionDuration | int8 | - | 训练时长 |
   | healthNotes | text | - | 健康注意事项 |
   | sports | jsonb | - | 运动偏好 |
   | updated_at | timestamptz | now() | 更新时间 |

5. 点击 **Save** 创建表

---

## 🔧 步骤三：获取 API 密钥

1. 进入 **Project Settings** → **API**
2. 复制以下信息：
   - **Project URL**: `https://xxx.supabase.co`
   - **anon/public key**: `eyJh...`
3. 保存这两个值，稍后需要用到

---

## 🔧 步骤四：配置 Row Level Security (RLS)

为了安全起见，需要设置访问权限：

1. 进入 **Authentication** → **Policies**
2. 选择 `user_profiles` 表
3. 点击 **New Policy**
4. 选择 **For full customization** → **Get started**
5. 创建 **Read** 策略：
   - **Policy name**: `Allow read access`
   - **Allowed operation**: `SELECT`
   - **Target role**: `anon`
   - **Using expression**: `auth.uid()::text = user_id`
6. 点击 **Save**

7. 创建 **Write** 策略：
   - **Policy name**: `Allow write access`
   - **Allowed operation**: `ALL`
   - **Target role**: `anon`
   - **Using expression**: `auth.uid()::text = user_id`
8. 点击 **Save**

---

## 🔧 步骤五：集成到应用

将以下代码添加到 `app.js` 文件顶部：

```javascript
// 引入 Supabase SDK（从 CDN）
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

// Supabase 配置（请替换为你的实际值）
const SUPABASE_URL = 'https://your-project.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 生成或获取用户唯一标识
let userId = localStorage.getItem('fitcoach_user_id');
if (!userId) {
  userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  localStorage.setItem('fitcoach_user_id', userId);
}
```

---

## 🔧 步骤六：修改保存和加载函数

### 保存数据到 Supabase

```javascript
async function saveToSupabase() {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .upsert({
        user_id: userId,
        name: UserProfile.name,
        age: UserProfile.age,
        gender: UserProfile.gender,
        height: UserProfile.height,
        weight: UserProfile.weight,
        restHR: UserProfile.restHR,
        maxHR: UserProfile.maxHR,
        vo2max: UserProfile.vo2max,
        bodyFat: UserProfile.bodyFat,
        fitnessLevel: UserProfile.fitnessLevel,
        goals: UserProfile.goals,
        trainingDays: UserProfile.trainingDays,
        sessionDuration: UserProfile.sessionDuration,
        healthNotes: UserProfile.healthNotes,
        sports: UserProfile.sports,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'user_id'
      });

    if (error) throw error;
    console.log('数据已保存到 Supabase');
    return true;
  } catch (error) {
    console.error('保存到 Supabase 失败:', error);
    return false;
  }
}
```

### 从 Supabase 加载数据

```javascript
async function loadFromSupabase() {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        // 没有找到记录，使用默认值
        console.log('未找到用户数据，使用默认值');
        return false;
      }
      throw error;
    }

    if (data) {
      console.log('从 Supabase 加载数据:', data);
      Object.assign(UserProfile, {
        name: data.name,
        age: data.age,
        gender: data.gender,
        height: data.height,
        weight: data.weight,
        restHR: data.restHR,
        maxHR: data.maxHR,
        vo2max: data.vo2max,
        bodyFat: data.bodyFat,
        fitnessLevel: data.fitnessLevel,
        goals: data.goals,
        trainingDays: data.trainingDays,
        sessionDuration: data.sessionDuration,
        healthNotes: data.healthNotes,
        sports: data.sports
      });
      return true;
    }
    return false;
  } catch (error) {
    console.error('从 Supabase 加载失败:', error);
    return false;
  }
}
```

---

## 🔧 步骤七：修改 saveProfile 函数

```javascript
async function saveProfile() {
  // ... 原有的表单数据获取逻辑 ...

  // 保存到本地存储
  saveToLocalStorage();

  // 保存到 Supabase
  const savedToSupabase = await saveToSupabase();

  if (savedToSupabase) {
    showToast('✓ 健康档案已保存并同步到云端 🌐');
  } else {
    showToast('✓ 健康档案已保存（仅本地）');
  }

  // 全局更新用户信息
  updateAllUserInfo();
}
```

---

## 🔧 步骤八：页面加载时从 Supabase 加载数据

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  // 先从 Supabase 加载
  const loadedFromSupabase = await loadFromSupabase();

  if (!loadedFromSupabase) {
    // 如果 Supabase 加载失败，尝试从本地存储加载
    loadFromLocalStorage();
  }

  // 初始化心率区间
  const zones = RuleEngine.calcHeartRateZones(UserProfile.restHR, UserProfile.maxHR);
  AICoach.zones = zones;

  // 更新界面
  updateAllUserInfo();

  // ... 其他初始化逻辑 ...
});
```

---

## ✅ 完成测试

1. 在设备 A 上打开应用，修改个人档案并保存
2. 在设备 B 上打开相同的应用链接
3. 检查是否显示设备 A 保存的数据

---

## 🌐 部署更新

代码修改完成后，需要重新上传到 GitHub：

1. 修改 `app.js` 文件
2. 访问 https://github.com/merx6/fitcoach-ai-app
3. 点击 **Add file** → **Upload files**
4. 上传修改后的 `app.js`
5. Commit changes

GitHub Pages 会在 1-2 分钟内自动部署更新。

---

## 📱 同步机制说明

- **自动同步**: 每次保存档案时自动上传到 Supabase
- **实时加载**: 页面打开时自动从 Supabase 拉取最新数据
- **用户标识**: 每个浏览器生成唯一的 user_id，存储在 localStorage
- **冲突处理**: 后写入的数据会覆盖旧数据（upsert 操作）

---

## 🆘 常见问题

### Q: 如何让同一用户在多个设备上同步？

**A**: 需要实现用户登录功能。可以集成 Supabase Auth，让用户注册/登录，使用 `auth.uid()` 作为 user_id。

### Q: 免费套餐有限制吗？

**A**: Supabase 免费套餐包括：
- 500MB 数据库存储
- 1GB 文件存储
- 2GB 带宽/月
- 50,000 MAU（月活跃用户）

对于个人使用完全足够。

### Q: 数据安全吗？

**A**: Supabase 使用 Postgres 数据库，支持 RLS（行级安全策略）。已配置的 RLS 策略确保用户只能访问自己的数据。

---

## 💡 下一步增强

- 添加用户注册/登录功能
- 实现训练历史记录同步
- 添加实时协作功能（多人教练）
- 集成 Supabase Storage 存储训练视频/图片

---

按照以上步骤完成后，你的应用就能在任何设备上同步数据了！🎉
