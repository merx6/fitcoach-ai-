/* =====================================================
   FitCoach AI — Application Logic
   规则引擎 + AI大模型结合的运动教练核心逻辑
   ===================================================== */

'use strict';

// ─────────────────────────────────────────
// 1. 用户数据模型
// ─────────────────────────────────────────
const UserProfile = {
  name: '张明',
  age: 32,
  gender: 'male',
  height: 175,        // cm
  weight: 72,         // kg
  restHR: 58,         // 静息心率 bpm
  maxHR: 188,         // 最大心率 bpm
  vo2max: 46,         // ml/kg/min
  bodyFat: 18,        // %
  fitnessLevel: 'intermediate',
  goals: ['endurance', 'fat_loss'],
  trainingDays: 4,
  sessionDuration: 45, // min
  healthNotes: '轻度膝关节不适，避免下坡跑步',
  sports: {
    running: { enabled: true, intensity: 3, pace: '5:30' },
    cycling: { enabled: true, intensity: 3, power: 180 },
    swimming: { enabled: true, intensity: 2, pace: '2:10' },
  },
};

// Garmin 同步数据
const GarminData = {
  hrv: 54,
  sleepScore: 74,
  stressLevel: 32,
  bodyBattery: 86,
  recoveryAdvisor: 14,   // 建议恢复时间(h)
  trainingStatus: '高峰',
  lastSync: new Date(),
};

// ─────────────────────────────────────────
// 2. 规则引擎 — 训练强度计算
// ─────────────────────────────────────────
const RuleEngine = {
  /**
   * 计算心率区间 (Karvonen 公式)
   * Zone 1: 50-60%  Zone 2: 60-70%  Zone 3: 70-80%
   * Zone 4: 80-90%  Zone 5: 90-100%
   */
  calcHeartRateZones(restHR, maxHR) {
    const reserve = maxHR - restHR;
    return {
      z1: { min: Math.round(restHR + reserve * 0.50), max: Math.round(restHR + reserve * 0.60), name: 'Z1 轻松' },
      z2: { min: Math.round(restHR + reserve * 0.60), max: Math.round(restHR + reserve * 0.70), name: 'Z2 有氧' },
      z3: { min: Math.round(restHR + reserve * 0.70), max: Math.round(restHR + reserve * 0.80), name: 'Z3 阈值' },
      z4: { min: Math.round(restHR + reserve * 0.80), max: Math.round(restHR + reserve * 0.90), name: 'Z4 无氧' },
      z5: { min: Math.round(restHR + reserve * 0.90), max: maxHR, name: 'Z5 极限' },
    };
  },

  /**
   * 根据恢复状态评估今日训练适宜性
   */
  assessTrainingReadiness(garmin) {
    let score = 0;
    let messages = [];

    // HRV 评分 (>50ms 良好)
    if (garmin.hrv >= 60) { score += 30; messages.push('HRV 优秀，神经系统恢复良好'); }
    else if (garmin.hrv >= 45) { score += 20; messages.push('HRV 正常，可正常训练'); }
    else { score += 5; messages.push('⚠️ HRV 偏低，建议降低训练强度'); }

    // 睡眠评分
    if (garmin.sleepScore >= 80) { score += 25; }
    else if (garmin.sleepScore >= 65) { score += 15; messages.push('睡眠质量一般，注意补充精力'); }
    else { score += 5; messages.push('⚠️ 睡眠不足，今日建议轻松训练'); }

    // 压力指数
    if (garmin.stressLevel <= 25) { score += 25; }
    else if (garmin.stressLevel <= 50) { score += 15; }
    else { score += 5; messages.push('⚠️ 压力较高，注意心率控制'); }

    // 身体电量
    if (garmin.bodyBattery >= 75) { score += 20; }
    else if (garmin.bodyBattery >= 50) { score += 12; }
    else { score += 3; messages.push('⚠️ 身体电量不足，建议充分休息'); }

    const level = score >= 75 ? '最佳' : score >= 55 ? '良好' : score >= 35 ? '一般' : '建议休息';
    const color = score >= 75 ? '#10b981' : score >= 55 ? '#06b6d4' : score >= 35 ? '#f59e0b' : '#ef4444';
    return { score, level, color, messages };
  },

  /**
   * 生成每日训练计划单元
   */
  generateDaySession(sport, fitnessLevel, goal, zones, dayType) {
    const templates = {
      running: {
        easy: {
          name: '轻松跑', duration: 30, zone: 'z2',
          desc: `${zones.z2.min}-${zones.z2.max} bpm · 配速 6:00/km`,
          icon: '🏃'
        },
        aerobic: {
          name: '有氧跑', duration: 45, zone: 'z2',
          desc: `${zones.z2.min}-${zones.z2.max} bpm · 配速 5:30/km`,
          icon: '🏃'
        },
        tempo: {
          name: '节奏跑', duration: 40, zone: 'z3',
          desc: `${zones.z3.min}-${zones.z3.max} bpm · 配速 4:55/km`,
          icon: '🏃'
        },
        long: {
          name: '长距离跑', duration: 60, zone: 'z2',
          desc: `${zones.z2.min}-${zones.z2.max} bpm · 配速 6:00/km`,
          icon: '🏃'
        },
      },
      cycling: {
        easy: {
          name: '骑行恢复', duration: 40, zone: 'z1',
          desc: `功率 120-150W · ${zones.z1.min}-${zones.z1.max} bpm`,
          icon: '🚴'
        },
        aerobic: {
          name: '有氧骑行', duration: 60, zone: 'z2',
          desc: `功率 160-185W · ${zones.z2.min}-${zones.z2.max} bpm`,
          icon: '🚴'
        },
        interval: {
          name: '骑行间歇', duration: 50, zone: 'z4',
          desc: `5×3min高强度 + 3min恢复`,
          icon: '🚴'
        },
      },
      swimming: {
        easy: {
          name: '游泳轻松', duration: 35, zone: 'z2',
          desc: `1200m · 混合泳 · 2:20/100m`,
          icon: '🏊'
        },
        endurance: {
          name: '游泳耐力', duration: 45, zone: 'z2',
          desc: `1800m · 自由泳 · 2:10/100m`,
          icon: '🏊'
        },
        drill: {
          name: '技术专项', duration: 40, zone: 'z1',
          desc: `1000m + 泳姿技术练习`,
          icon: '🏊'
        },
      },
    };

    return templates[sport] && templates[sport][dayType]
      ? templates[sport][dayType]
      : { name: '训练', duration: 45, desc: '按计划进行', icon: '💪' };
  },

  /**
   * 4周渐进式计划生成
   */
  generate4WeekPlan(profile, zones) {
    const weeks = [];
    const sportCycle = ['running', 'cycling', 'rest', 'running', 'swimming', 'running', 'rest'];

    for (let w = 0; w < 4; w++) {
      const intensityFactor = 1 + w * 0.1; // 每周增加10%
      const weekDays = [];

      sportCycle.forEach((sport, d) => {
        if (sport === 'rest') {
          weekDays.push({ sport: 'rest', name: d === 2 ? '主动恢复' : '完全休息', icon: '😴', duration: 0, desc: d === 2 ? '拉伸 + 泡沫轴 20min' : '充分恢复' });
          return;
        }
        // 周末长距离跑
        const dayType = d === 0 ? 'easy' : d === 3 ? 'aerobic' : d === 4 ? 'endurance' : d === 5 ? 'long' : 'easy';
        const session = this.generateDaySession(sport, profile.fitnessLevel, profile.goals, zones, dayType);
        weekDays.push({ ...session, weekIntensity: Math.round(session.duration * intensityFactor) + 'min' });
      });

      const weekNames = ['适应期', '建立期', '强化期', '巩固期'];
      weeks.push({ week: w + 1, name: weekNames[w], days: weekDays, totalLoad: Math.round(180 * intensityFactor) });
    }
    return weeks;
  },
};

// ─────────────────────────────────────────
// 3. AI 教练模拟引擎 (规则 + 模板)
// ─────────────────────────────────────────
const AICoach = {
  zones: RuleEngine.calcHeartRateZones(UserProfile.restHR, UserProfile.maxHR),

  // 关键词匹配表
  knowledgeBase: [
    {
      keywords: ['今天', '训练', '适合', '状态', '身体'],
      handler: () => {
        const r = RuleEngine.assessTrainingReadiness(GarminData);
        return `根据你今天的 Garmin 数据分析：\n\n• HRV ${GarminData.hrv}ms — ${GarminData.hrv >= 50 ? '✅ 良好' : '⚠️ 偏低'}\n• 睡眠评分 ${GarminData.sleepScore}分 — ${GarminData.sleepScore >= 75 ? '✅ 充足' : '⚠️ 一般'}\n• 身体电量 ${GarminData.bodyBattery}% — 充沛\n• 压力指数 ${GarminData.stressLevel} — 低压状态\n\n综合评分：**${r.score}分 / ${r.level}**\n\n${r.messages.length ? r.messages.join('\n') : ''}\n\n✅ 今天非常适合按计划进行有氧骑行训练！建议心率控制在 ${AICoach.zones.z2.min}-${AICoach.zones.z2.max} bpm。`;
      }
    },
    {
      keywords: ['膝盖', '膝关节', '不舒服', '疼', '受伤'],
      handler: () => `关于你的膝关节不适，我来给你一些专业建议：\n\n**今天训练调整方案：**\n• 改为游泳或骑行（零冲击力运动）\n• 如坚持跑步，避免下坡，选择平坦路面\n• 配速降低10%，减少地面冲击\n\n**日常保护建议：**\n1. 训练前做好充分热身（10-15min）\n2. 每次跑步后冰敷膝盖5-10min\n3. 加强股四头肌和臀大肌力量训练\n4. 考虑使用压缩护膝\n5. 增加泡沫轴放松IT Band\n\n⚠️ 如果疼痛持续3天以上，建议及时就医检查。\n\n我已自动调整本周计划，增加游泳比例，减少跑量约20%。`
    },
    {
      keywords: ['配速', '提速', '跑步', '速度', '变快'],
      handler: () => `提升跑步配速的科学方法：\n\n**当前水平：** 5:28/km（良好基础）\n**8周目标：** 5:00/km\n\n**关键训练组合（80/20原则）：**\n\n🟢 **Z2有氧跑（80%训练量）**\n→ 慢比你以为的还要慢，配速 6:00-6:30/km\n→ 建立有氧基础，这是提速的核心！\n\n🔵 **节奏跑（10%）**\n→ 每周1次，配速约4:50/km，20-25min\n→ 提升乳酸阈值\n\n🔴 **间歇跑（10%）**\n→ 每周1次，400m × 6-8组，配速4:30/km\n→ 提升最大摄氧量\n\n**8周进阶计划：**\n第1-2周：强化Z2基础 → 第3-4周：加入节奏跑 → 第5-6周：引入间歇 → 第7-8周：整合测试\n\n需要我把这个计划详细到每日吗？`
    },
    {
      keywords: ['分析', '本周', '数据', '表现'],
      handler: () => `**本周训练数据分析（AI 解读）**\n\n📊 **训练量**\n• 已完成3次，总时长 2h 05min\n• 本周目标完成度：60%（目标5次）\n\n❤️ **心率分析**\n• Z2有氧占比 52% → ✅ 接近80/20目标\n• Z3阈值占比 28% → 略高，注意控制\n\n📈 **能力变化（对比上周）**\n• 跑步均配速：5:28 → 5:24（+4 sec/km ↑）\n• 平均心率：145bpm → 142bpm（心率漂移改善 ↑）\n• VO₂Max估算：45.5 → 46.2（+1.5% ↑）\n\n💡 **AI 洞察**\n有氧效率持续提升，心率下降而配速提升，说明心肺适应性正在改善。按当前趋势，预计4周后配速可突破5:10/km。\n\n**本周建议：** 今日训练完成后，本周剩余2次（周六骑行60min + 今日跑步），建议优先完成周六的骑行。`
    },
    {
      keywords: ['半马', '半程马拉松', '21', '备赛'],
      handler: () => `**半程马拉松备赛计划（12周）**\n\n你的当前配速 5:28/km，半马完赛时间预估约 **1:55-2:00**。\n\n**目标设定：**\n• 保守目标：顺利完赛\n• 进阶目标：1:50以内（需配速提至5:12/km）\n\n**12周计划框架：**\n\n🏗️ **第1-4周：基础建设**\n• 周跑量 35-45km，80%Z2配速\n• 每周1次长跑（60-90min）\n\n⚡ **第5-8周：专项强化**\n• 周跑量 45-55km\n• 引入马拉松配速训练（半马配速跑20-30min）\n• 每周长跑逐步延至1:45-2:00\n\n🎯 **第9-11周：赛前冲刺**\n• 最大跑量周（约55km）\n• 模拟比赛场景训练\n\n🧘 **第12周：减量期**\n• 跑量削减60%，保持强度\n• 赛前3天完全休息\n\n⚠️ **特别提醒：** 考虑你的膝关节情况，建议提前采购支撑性好的跑鞋，适当增加力量训练保护膝盖。\n\n需要我生成详细的每周计划吗？`
    },
    {
      keywords: ['恢复', '拉伸', '训练后'],
      handler: () => `**训练后恢复方案（今日 45min 跑步后）**\n\n⏱️ **立即恢复（训练后5min内）**\n• 缓步走 5min，心率降至 120bpm 以下\n\n🧘 **拉伸放松（15-20min）**\n1. 髂腰肌拉伸 × 各 30sec\n2. 股四头肌拉伸 × 各 30sec\n3. 腘绳肌拉伸 × 各 30sec\n4. 小腿腓肠肌拉伸 × 各 30sec\n5. IT Band 泡沫轴滚压 × 各 60sec ⬅️ 对你的膝盖尤为重要！\n\n🥤 **营养补充**\n• 训练后30分钟内：摄入 20-25g 蛋白质 + 碳水\n• 推荐：香蕉 + 酸奶，或蛋白棒\n• 充分补水：训练体重每减少1kg补水 1000ml\n\n😴 **睡眠**\n• 今晚争取 7-8小时\n• 睡前避免强光刺激，有助于HRV恢复\n\n明天你的 Garmin HRV 数据如果 ≥50ms，说明恢复良好，可以正常训练。`
    },
    {
      keywords: ['计划', '制定', '4周', '6周', '8周'],
      handler: () => `我来为你制定一份个性化 4 周训练计划 🎯\n\n**基于你的档案分析：**\n• 级别：中级运动员（规律训练 1-2年）\n• 目标：提升耐力 + 减脂\n• 限制：膝关节轻微不适\n• Garmin 数据：恢复状态良好\n\n**计划原则：**\n✅ 80/20 训练法（80%低强度 + 20%高强度）\n✅ 三项交叉训练（跑/骑/游）减少重复性伤害\n✅ 每周训练量增幅≤10%\n✅ 避免下坡跑，保护膝盖\n\n计划已更新到【训练计划】页面，你可以：\n→ 点击左侧「训练计划」查看完整日历\n→ 点击「调整计划」来修改偏好\n\n需要我根据特定比赛日期来反推计划吗？`
    },
  ],

  // 通用回复模板
  genericReplies: [
    '好问题！根据你的身体数据，我建议在训练前先确认 HRV 是否正常（≥45ms）。你可以通过 Garmin 设备查看今日数据，我会据此给出更精准的建议。',
    '这个问题需要结合你的长期训练数据来分析。总体来说，以你目前中级水平，遵循80/20训练原则最为有效——80%的训练保持在有氧区（Z2），20%才是高强度。',
    '根据运动科学，你描述的情况在耐力训练者中很常见。关键是要倾听身体信号，不要过度训练。你的恢复状态数据显示一切正常，继续保持当前训练节奏即可。',
    '我注意到你的训练数据显示出积极趋势！坚持下去，按当前进度，8周内你的有氧能力（VO₂Max）有望提升5-8%。记住，一致性比强度更重要。',
  ],

  /**
   * 处理用户问题，返回 AI 回复
   */
  async generateResponse(userMessage) {
    // 模拟 API 延迟
    await new Promise(r => setTimeout(r, 800 + Math.random() * 1200));

    const msg = userMessage.toLowerCase();

    // 遍历知识库匹配
    for (const entry of this.knowledgeBase) {
      if (entry.keywords.some(k => msg.includes(k))) {
        return entry.handler();
      }
    }

    // 随机通用回复
    return this.genericReplies[Math.floor(Math.random() * this.genericReplies.length)];
  },
};

// ─────────────────────────────────────────
// 4. 页面导航
// ─────────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const pageEl = document.getElementById('page-' + page);
  const navEl = document.querySelector(`[data-page="${page}"]`);

  if (pageEl) pageEl.classList.add('active');
  if (navEl) navEl.classList.add('active');

  // 触发对应页面的初始化
  if (page === 'analysis') initAnalysisCharts();
  if (page === 'today') startLiveDataSimulation();
  if (page === 'dashboard') initRadar();
  if (page === 'profile') fillProfileForm();
}

// ─────────────────────────────────────────
// 5. 健康档案交互
// ─────────────────────────────────────────
function fillProfileForm() {
  // 填充基本信息输入框
  const inputs = document.querySelectorAll('#page-profile .form-input');

  inputs.forEach(input => {
    const label = input.previousElementSibling?.textContent?.trim();
    if (!label) return;

    // 根据标签填充对应的 UserProfile 数据（使用 includes 匹配部分文本）
    if (label.includes('姓名')) input.value = UserProfile.name;
    if (label.includes('年龄')) input.value = UserProfile.age;
    if (label.includes('身高')) input.value = UserProfile.height;
    if (label.includes('体重')) input.value = UserProfile.weight;
    if (label.includes('静息心率')) input.value = UserProfile.restHR;
    if (label.includes('最大心率')) input.value = UserProfile.maxHR;
    if (label.includes('VO₂Max')) input.value = UserProfile.vo2max;
    if (label.includes('体脂率')) input.value = UserProfile.bodyFat;
    if (label.includes('注意事项')) input.value = UserProfile.healthNotes;
  });

  // 更新训练目标标签
  document.querySelectorAll('#goalTags .tag').forEach(tag => {
    const text = tag.textContent.trim();
    tag.classList.remove('active');

    if (text === '减脂塑形' && UserProfile.goals.includes('fat_loss')) tag.classList.add('active');
    if (text === '提升耐力' && UserProfile.goals.includes('endurance')) tag.classList.add('active');
    if (text === '增肌力量' && UserProfile.goals.includes('strength')) tag.classList.add('active');
    if (text === '备战比赛' && UserProfile.goals.includes('competition')) tag.classList.add('active');
    if (text === '健康维护' && UserProfile.goals.includes('health')) tag.classList.add('active');
    if (text === '压力减压' && UserProfile.goals.includes('stress_relief')) tag.classList.add('active');
  });

  // 更新运动级别选择器
  document.querySelectorAll('.level-option').forEach(option => {
    option.classList.remove('active');
    if (option.dataset.level === UserProfile.fitnessLevel) {
      option.classList.add('active');
    }
  });

  // 更新运动偏好（复选框和滑杆）
  const sportPrefItems = document.querySelectorAll('.sport-pref-item');
  const sports = ['running', 'cycling', 'swimming'];

  sportPrefItems.forEach((item, index) => {
    if (index >= sports.length) return;
    const sport = sports[index];
    const checkbox = item.querySelector('input[type="checkbox"]');
    const range = item.querySelector('.intensity-range');

    if (UserProfile.sports[sport]) {
      if (checkbox) checkbox.checked = UserProfile.sports[sport].enabled;
      if (range) {
        range.value = UserProfile.sports[sport].intensity;
        // 触发 input 事件更新标签
        range.dispatchEvent(new Event('input'));
      }
    }
  });

  console.log('健康档案表单已填充:', UserProfile);
}

function selectLevel(el, level) {
  document.querySelectorAll('.level-option').forEach(o => o.classList.remove('active'));
  el.classList.add('active');
  UserProfile.fitnessLevel = level;
}

function toggleTag(el) {
  el.classList.toggle('active');
}

function updateIntensity(input) {
  const labels = ['', '很轻松', '轻松', '中等', '较强', '很强'];
  input.nextElementSibling.textContent = labels[input.value];
}

// BMI 自动计算
function calculateBMI() {
  const heightInput = document.querySelector('input[type="number"][placeholder*="身高"]');
  const weightInput = document.querySelector('input[type="number"][placeholder*="体重"]');
  const bmiInput = document.querySelector('input[placeholder*="BMI"]');
  
  if (heightInput && weightInput && bmiInput) {
    const height = parseFloat(heightInput.value) / 100; // 转换为米
    const weight = parseFloat(weightInput.value);
    
    if (height > 0 && weight > 0) {
      const bmi = (weight / (height * height)).toFixed(1);
      bmiInput.value = bmi;
    }
  }
}

// 监听身高体重变化
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const heightInput = document.querySelector('input[type="number"][placeholder*="身高"]');
    const weightInput = document.querySelector('input[type="number"][placeholder*="体重"]');
    
    if (heightInput) heightInput.addEventListener('input', calculateBMI);
    if (weightInput) weightInput.addEventListener('input', calculateBMI);
    
    // 初始计算一次
    calculateBMI();
  }, 100);
});

function saveProfile() {
  // 获取表单数据
  const inputs = document.querySelectorAll('#page-profile .form-input');

  // 更新基本信息
  inputs.forEach(input => {
    const label = input.previousElementSibling?.textContent;
    const value = input.value;

    // 更新 UserProfile
    if (label === '姓名') UserProfile.name = value;
    if (label === '年龄') UserProfile.age = parseInt(value) || 32;
    if (label === '身高') UserProfile.height = parseInt(value) || 175;
    if (label === '体重') UserProfile.weight = parseInt(value) || 72;
    if (label === '静息心率') UserProfile.restHR = parseInt(value) || 58;
    if (label === '最大心率') UserProfile.maxHR = parseInt(value) || 188;
    if (label === 'VO₂Max (预估)') UserProfile.vo2max = parseInt(value) || 46;
    if (label === '体脂率 (%)') UserProfile.bodyFat = parseInt(value) || 18;
    if (label.includes('注意事项')) UserProfile.healthNotes = value;
  });

  // 获取训练目标
  const activeGoals = [];
  document.querySelectorAll('#goalTags .tag.active').forEach(tag => {
    const text = tag.textContent.trim();
    if (text === '减脂塑形') activeGoals.push('fat_loss');
    if (text === '提升耐力') activeGoals.push('endurance');
    if (text === '增肌力量') activeGoals.push('strength');
    if (text === '备战比赛') activeGoals.push('competition');
    if (text === '健康维护') activeGoals.push('health');
    if (text === '压力减压') activeGoals.push('stress_relief');
  });
  UserProfile.goals = activeGoals;

  // 获取每周训练天数和时长
  const selects = document.querySelectorAll('#page-profile select');
  if (selects.length >= 2) {
    // 第一个select是训练天数
    const daysOption = selects[0].selectedOptions[0]?.textContent;
    UserProfile.trainingDays = parseInt(daysOption) || 4;

    // 第二个select是训练时长
    const durationOption = selects[1]?.selectedOptions[0]?.textContent;
    const durationMatch = durationOption?.match(/(\d+)/);
    if (durationMatch) {
      UserProfile.sessionDuration = parseInt(durationMatch[1]) || 45;
    }
  }

  // 获取运动偏好（强度和开关状态）
  const sportPrefItems = document.querySelectorAll('.sport-pref-item');
  const sports = ['running', 'cycling', 'swimming'];

  sportPrefItems.forEach((item, index) => {
    if (index >= sports.length) return;
    const sport = sports[index];
    const checkbox = item.querySelector('input[type="checkbox"]');
    const range = item.querySelector('.intensity-range');

    if (UserProfile.sports[sport]) {
      UserProfile.sports[sport].enabled = checkbox?.checked ?? true;
      UserProfile.sports[sport].intensity = parseInt(range?.value) || 3;
    }
  });

  // 更新心率区间
  const zones = RuleEngine.calcHeartRateZones(UserProfile.restHR, UserProfile.maxHR);
  AICoach.zones = zones;

  // 重新计算训练就绪度
  const readiness = RuleEngine.assessTrainingReadiness(GarminData);

  console.log('档案已更新:', UserProfile);
  console.log('新心率区间:', zones);
  console.log('训练就绪度:', readiness);

  // 保存到本地存储
  saveToLocalStorage();

  // 全局更新所有页面的用户信息（名字、头像等）
  updateAllUserInfo();

  showToast('✓ 健康档案已保存，AI 已重新分析训练计划');
}

// ─────────────────────────────────────────
// 6. 训练计划交互
// ─────────────────────────────────────────
function switchWeek(btn, week) {
  document.querySelectorAll('.week-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.plan-week').forEach(w => w.classList.remove('active'));
  const weekEl = document.getElementById('week-' + week);
  if (weekEl) weekEl.classList.add('active');
  // 其他周次若无内容则生成提示
}

function generatePlan() {
  showToast('🤖 AI 正在根据最新 Garmin 数据重新生成计划...');
  setTimeout(() => showToast('✓ 新训练计划已生成！'), 2000);
}

function showPlanDetail() {
  showToast('计划详情功能即将上线');
}

// ─────────────────────────────────────────
// 7. 今日训练实时数据模拟
// ─────────────────────────────────────────
let liveTimer = null;
let trainingActive = false;
let trainingSeconds = 18 * 60 + 32;

function startLiveDataSimulation() {
  if (liveTimer) return;
  trainingActive = true;

  liveTimer = setInterval(() => {
    if (!trainingActive) return;

    trainingSeconds++;
    const mins = String(Math.floor(trainingSeconds / 60)).padStart(2, '0');
    const secs = String(trainingSeconds % 60).padStart(2, '0');
    safeSet('liveTime', `${mins}:${secs}`);

    // 心率随机波动
    const hrBase = 142;
    const hr = hrBase + Math.round((Math.random() - 0.5) * 8);
    safeSet('liveHR', hr);

    // 距离递增
    const dist = (3.2 + trainingSeconds / 3600 * 10.8).toFixed(2);
    safeSet('liveDist', dist);

    // 热量
    const cal = Math.round(187 + (trainingSeconds - 18 * 60 - 32) * 0.28 * 1.5);
    safeSet('liveCal', cal);

    // 步频波动
    const cadence = 172 + Math.round((Math.random() - 0.5) * 6);
    safeSet('liveCadence', cadence);

    // 配速
    const paceBase = 328; // 5:28 = 328sec/km
    const paceVar = Math.round((Math.random() - 0.5) * 12);
    const paceTotal = paceBase + paceVar;
    safeSet('livePace', `${Math.floor(paceTotal / 60)}:${String(paceTotal % 60).padStart(2, '0')}`);

  }, 1000);
}

function safeSet(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function pauseTraining() {
  trainingActive = !trainingActive;
  const btn = document.querySelector('.ctrl-btn.pause');
  if (btn) btn.innerHTML = trainingActive
    ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> 暂停'
    : '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg> 继续';
  showToast(trainingActive ? '训练已继续' : '训练已暂停');
}

function stopTraining() {
  trainingActive = false;
  if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
  showToast('✓ 训练结束！本次训练已保存，正在同步到 Garmin...');
  setTimeout(() => navigate('analysis'), 1800);
}

function adjustIntensity() {
  const panel = document.getElementById('intensityPanel');
  if (panel) {
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  }
}

function applyIntensity(el, label) {
  document.querySelectorAll('.intensity-opt').forEach(o => o.classList.remove('active-opt'));
  el.classList.add('active-opt');
  showToast(`✓ 已调整强度：${label}`);

  // 更新建议列表
  const adviceList = document.getElementById('realtimeAdvice');
  if (adviceList && label !== '保持现状') {
    const newAdvice = document.createElement('div');
    newAdvice.className = 'advice-item green';
    newAdvice.innerHTML = `<div class="advice-icon">✓</div><div class="advice-text">强度已${label}，新配速建议生效</div>`;
    adviceList.insertBefore(newAdvice, adviceList.firstChild);
  }
}

// ─────────────────────────────────────────
// 8. 数据分析图表 (Canvas)
// ─────────────────────────────────────────
function initAnalysisCharts() {
  drawLoadChart();
  drawRadarChart();
}

function drawLoadChart() {
  const canvas = document.getElementById('loadCanvas');
  if (!canvas) return;
  canvas.width = canvas.offsetWidth || 800;
  canvas.height = 200;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const pad = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;

  // 模拟数据
  const actualData = [45, 52, 0, 65, 40, 70, 0, 75, 60, 0, 80, 55, 70, 85];
  const planData   = [50, 55, 0, 60, 45, 65, 0, 70, 65, 0, 75, 60, 70, 80];
  const days = ['3/6','3/7','3/8','3/9','3/10','3/11','3/12','3/13','3/14','3/15','3/16','3/17','3/18','今天'];
  const maxVal = 100;
  const n = actualData.length;

  ctx.clearRect(0, 0, W, H);

  // 网格
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + chartH - (chartH / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(pad.left + chartW, y); ctx.stroke();
    ctx.fillStyle = '#4a6080'; ctx.font = '11px Inter'; ctx.textAlign = 'right';
    ctx.fillText(Math.round(maxVal / 4 * i), pad.left - 5, y + 4);
  }

  function drawLine(data, color, fill) {
    const pts = data.map((v, i) => ({
      x: pad.left + (chartW / (n - 1)) * i,
      y: pad.top + chartH - (v / maxVal) * chartH,
    }));

    if (fill) {
      const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
      grad.addColorStop(0, color + '40');
      grad.addColorStop(1, color + '00');
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pad.top + chartH);
      pts.forEach(p => ctx.lineTo(p.x, p.y));
      ctx.lineTo(pts[pts.length - 1].x, pad.top + chartH);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
    }

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.stroke();

    // 最后一点高亮
    const last = pts[pts.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = color; ctx.fill();
  }

  drawLine(planData, '#06b6d4', false);
  drawLine(actualData, '#6366f1', true);

  // X轴标签
  ctx.fillStyle = '#4a6080'; ctx.font = '10px Inter'; ctx.textAlign = 'center';
  days.filter((_, i) => i % 2 === 0).forEach((d, idx) => {
    const i = idx * 2;
    ctx.fillText(d, pad.left + (chartW / (n - 1)) * i, H - 8);
  });
}

function drawRadarChart() {
  const svg = document.getElementById('radarSvg');
  if (!svg) return;

  const cx = 150, cy = 150, r = 100;
  const axes = ['有氧耐力', '跑步效率', '骑行能力', '游泳能力', '恢复能力', '运动经济性'];
  const current = [0.80, 0.72, 0.60, 0.55, 0.86, 0.70];
  const target  = [0.90, 0.85, 0.75, 0.70, 0.90, 0.80];
  const n = axes.length;

  function getPoint(i, val) {
    const angle = (Math.PI * 2 / n) * i - Math.PI / 2;
    return { x: cx + Math.cos(angle) * r * val, y: cy + Math.sin(angle) * r * val };
  }

  let html = '';

  // 背景网格
  [0.2, 0.4, 0.6, 0.8, 1.0].forEach(scale => {
    const pts = Array.from({ length: n }, (_, i) => {
      const p = getPoint(i, scale);
      return `${p.x},${p.y}`;
    }).join(' ');
    html += `<polygon points="${pts}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>`;
  });

  // 轴线
  Array.from({ length: n }, (_, i) => {
    const p = getPoint(i, 1);
    html += `<line x1="${cx}" y1="${cy}" x2="${p.x}" y2="${p.y}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>`;
  });

  // 目标区域
  const targetPts = Array.from({ length: n }, (_, i) => {
    const p = getPoint(i, target[i]);
    return `${p.x},${p.y}`;
  }).join(' ');
  html += `<polygon points="${targetPts}" fill="rgba(6,182,212,0.1)" stroke="rgba(6,182,212,0.4)" stroke-width="1.5"/>`;

  // 当前能力
  const currentPts = Array.from({ length: n }, (_, i) => {
    const p = getPoint(i, current[i]);
    return `${p.x},${p.y}`;
  }).join(' ');
  html += `<polygon points="${currentPts}" fill="rgba(99,102,241,0.25)" stroke="#6366f1" stroke-width="2"/>`;

  // 顶点圆点
  current.forEach((val, i) => {
    const p = getPoint(i, val);
    html += `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#6366f1"/>`;
  });

  // 标签
  axes.forEach((label, i) => {
    const p = getPoint(i, 1.22);
    const anchor = p.x < cx - 5 ? 'end' : p.x > cx + 5 ? 'start' : 'middle';
    html += `<text x="${p.x}" y="${p.y}" text-anchor="${anchor}" fill="#94a3b8" font-size="11" font-family="Inter">${label}</text>`;
  });

  svg.innerHTML = html;
}

function selectRange(btn, range) {
  document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  drawLoadChart();
  showToast(`已切换至 ${range === '7d' ? '7天' : range === '30d' ? '30天' : '90天'} 视图`);
}

function initRadar() {
  drawRadarChart();
}

// ─────────────────────────────────────────
// 9. Garmin 同步（真实 API）
// ─────────────────────────────────────────

// Garmin API 基础 URL
// 注意：Vercel 部署到 GitHub Pages 后，会因跨域问题无法直接访问后端 API
// 推荐的解决方案：
// 1. 将前端也部署到 Vercel（与 API 同域）
// 2. 或者配置 Vercel API 使用 CORS 允许 GitHub Pages 访问
const GARMIN_API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:3000'  // 本地开发：连接本地 Python 服务器
  : 'https://fitcoach-garmin-api.vercel.app'; // 生产环境：连接 Vercel API

async function syncGarmin() {
  const btn = document.querySelector('.btn-sync');
  if (btn) {
    btn.innerHTML = '<svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg> 同步中...';
    btn.disabled = true;
  }

  try {
    const response = await fetch(`${GARMIN_API_BASE}/api/garmin/sync`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (data.success) {
      // 更新 GarminData
      if (data.data.hrv !== null) GarminData.hrv = data.data.hrv;
      if (data.data.sleepScore !== null) GarminData.sleepScore = data.data.sleepScore;
      if (data.data.bodyBattery !== null) GarminData.bodyBattery = data.data.bodyBattery;
      if (data.data.stressLevel !== null) GarminData.stressLevel = data.data.stressLevel;

      GarminData.lastSync = new Date(data.lastSync);

      // 更新 UI 显示
      updateGarminUI();
      showToast(`✓ Garmin 数据同步完成！更新了 ${data.data.activitiesCount} 条活动记录`);
    } else {
      throw new Error(data.error || '同步失败');
    }

  } catch (error) {
    console.error('Garmin 同步失败:', error);
    showToast('✗ 同步失败：' + error.message + ' (请检查后端服务是否启动)');
  } finally {
    if (btn) {
      btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg> 立即同步';
      btn.disabled = false;
    }
  }
}

function updateGarminUI() {
  // 更新 Garmin 页面的数据显示
  const hrvEl = document.getElementById('garminHRV');
  const sleepEl = document.getElementById('garminSleep');
  const batteryEl = document.getElementById('garminBattery');
  const stressEl = document.getElementById('garminStress');
  const lastSyncEl = document.getElementById('lastSyncTime');

  // 更新数值
  if (hrvEl) hrvEl.textContent = GarminData.hrv + ' ms';
  if (sleepEl) sleepEl.textContent = GarminData.sleepScore + ' 分';
  if (batteryEl) batteryEl.textContent = GarminData.bodyBattery + '%';
  if (stressEl) stressEl.textContent = GarminData.stressLevel;
  if (lastSyncEl) lastSyncEl.textContent = formatLastSync(GarminData.lastSync);

  // 更新状态标签和颜色
  updateStatusElement('hrvStatus', GarminData.hrv, {
    good: GarminData.hrv >= 50,
    ok: GarminData.hrv >= 45,
    warn: GarminData.hrv < 45,
    labels: { good: '优秀', ok: '良好', warn: '偏低' }
  });

  updateStatusElement('sleepStatus', GarminData.sleepScore, {
    good: GarminData.sleepScore >= 80,
    ok: GarminData.sleepScore >= 65,
    warn: GarminData.sleepScore < 65,
    labels: { good: '充足', ok: '一般', warn: '不足' }
  });

  updateStatusElement('batteryStatus', GarminData.bodyBattery, {
    good: GarminData.bodyBattery >= 75,
    ok: GarminData.bodyBattery >= 50,
    warn: GarminData.bodyBattery < 50,
    labels: { good: '充沛', ok: '尚可', warn: '不足' }
  });

  updateStatusElement('stressStatus', GarminData.stressLevel, {
    good: GarminData.stressLevel <= 25,
    ok: GarminData.stressLevel <= 50,
    warn: GarminData.stressLevel > 50,
    labels: { good: '低压', ok: '适中', warn: '高压' }
  });
}

function updateStatusElement(elementId, value, thresholds) {
  const el = document.getElementById(elementId);
  if (!el) return;

  // 移除所有状态类
  el.classList.remove('good', 'ok', 'warn');

  // 添加对应的类
  if (thresholds.good) {
    el.classList.add('good');
    el.textContent = thresholds.labels.good;
  } else if (thresholds.ok) {
    el.classList.add('ok');
    el.textContent = thresholds.labels.ok;
  } else {
    el.classList.add('warn');
    el.textContent = thresholds.labels.warn;
  }
}

function formatLastSync(date) {
  if (!date) return '从未同步';
  const now = new Date();
  const diff = Math.floor((now - date) / 1000); // 秒

  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
  return date.toLocaleDateString('zh-CN');
}

// ─────────────────────────────────────────
// 10. AI Chat 功能
// ─────────────────────────────────────────
function handleChatInput(e) {
  if (e.key === 'Enter') sendChat();
}

function handleDashboardAiInput(e) {
  if (e.key === 'Enter') handleDashboardAiSend();
}

function handleDashboardAiSend() {
  const input = document.getElementById('dashboardAiInput');
  if (!input || !input.value.trim()) return;
  const msg = input.value.trim();
  input.value = '';
  addDashboardMessage(msg);
}

async function addDashboardMessage(msg) {
  const container = document.querySelector('.ai-messages');
  if (!container) return;

  // 添加用户消息
  const userDiv = document.createElement('div');
  userDiv.className = 'ai-msg';
  userDiv.style.flexDirection = 'row-reverse';
  userDiv.innerHTML = `<div class="ai-bubble" style="background:rgba(99,102,241,.12);border-color:rgba(99,102,241,.25);border-radius:10px 0 10px 10px;color:var(--text-primary)">${escapeHtml(msg)}</div>`;
  container.appendChild(userDiv);

  // 打字指示
  const typingDiv = document.createElement('div');
  typingDiv.className = 'ai-msg';
  typingDiv.innerHTML = `<div class="ai-avatar">AI</div><div class="ai-bubble"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>`;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  const reply = await AICoach.generateResponse(msg);
  typingDiv.remove();

  const replyDiv = document.createElement('div');
  replyDiv.className = 'ai-msg';
  replyDiv.innerHTML = `<div class="ai-avatar">AI</div><div class="ai-bubble">${formatAIReply(reply)}</div>`;
  container.appendChild(replyDiv);
  container.scrollTop = container.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  if (!input || !input.value.trim()) return;
  const msg = input.value.trim();
  input.value = '';
  await addChatMessage(msg);
}

function sendQuickPrompt(prompt) {
  const input = document.getElementById('chatInput');
  if (input) input.value = prompt;
  sendChat();
}

async function addChatMessage(userMsg) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  // 用户消息
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-msg user-msg';
  userDiv.innerHTML = `
    <div class="chat-avatar user-chat-avatar">我</div>
    <div class="chat-bubble user-chat-bubble">${escapeHtml(userMsg)}</div>`;
  container.appendChild(userDiv);

  // 打字动画
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-msg ai-msg-chat';
  typingDiv.innerHTML = `
    <div class="chat-avatar ai-chat-avatar">AI</div>
    <div class="chat-bubble ai-chat-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
      </div>
    </div>`;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  const reply = await AICoach.generateResponse(userMsg);
  typingDiv.remove();

  const aiDiv = document.createElement('div');
  aiDiv.className = 'chat-msg ai-msg-chat';
  aiDiv.innerHTML = `
    <div class="chat-avatar ai-chat-avatar">AI</div>
    <div class="chat-bubble ai-chat-bubble">${formatAIReply(reply)}</div>`;
  container.appendChild(aiDiv);
  container.scrollTop = container.scrollHeight;
}

// ─────────────────────────────────────────
// 11. 工具函数
// ─────────────────────────────────────────
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2800);
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatAIReply(text) {
  // Markdown 简单解析
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(99,102,241,.15);padding:1px 5px;border-radius:3px;font-size:.9em">$1</code>')
    .replace(/\n/g, '<br>');
}

// ─────────────────────────────────────────
// 12. 初始化
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // 先从本地存储加载数据
  const loaded = loadFromLocalStorage();
  if (loaded) {
    console.log('已加载本地保存的数据');
  } else {
    console.log('使用默认数据');
  }

  // 初始化心率区间
  const zones = RuleEngine.calcHeartRateZones(UserProfile.restHR, UserProfile.maxHR);
  AICoach.zones = zones;
  console.log('心率区间:', zones);

  // 初始化训练状态评估
  const readiness = RuleEngine.assessTrainingReadiness(GarminData);
  console.log('今日训练就绪度:', readiness);

  // 初始化用户信息显示
  setTimeout(() => updateAllUserInfo(), 50);

  // 初始化健康档案表单
  setTimeout(() => fillProfileForm(), 50);

  // 初始化 Garmin UI
  setTimeout(() => updateGarminUI(), 50);

  // 渲染雷达图
  setTimeout(() => drawRadarChart(), 100);

  // 窗口resize重绘
  window.addEventListener('resize', () => {
    const active = document.querySelector('.page.active');
    if (active && active.id === 'page-analysis') drawLoadChart();
  });

  showToast('FitCoach AI 已就绪，已同步 Garmin 数据 🏃');
});

// ─────────────────────────────────────────
// 13. 移动端菜单切换
// ─────────────────────────────────────────
function toggleMobileMenu() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.classList.toggle('active');
  }
}

// ─────────────────────────────────────────
// 14. 本地存储管理
// ─────────────────────────────────────────
function saveToLocalStorage() {
  try {
    const data = {
      userProfile: UserProfile,
      timestamp: Date.now()
    };
    localStorage.setItem('fitcoach_data', JSON.stringify(data));
    console.log('数据已保存到本地存储');
  } catch (error) {
    console.error('保存到本地存储失败:', error);
  }
}

function loadFromLocalStorage() {
  try {
    const saved = localStorage.getItem('fitcoach_data');
    if (saved) {
      const data = JSON.parse(saved);
      console.log('从本地存储加载数据:', data.userProfile);

      // 合并保存的数据到 UserProfile
      Object.assign(UserProfile, data.userProfile);

      return true;
    }
    return false;
  } catch (error) {
    console.error('从本地存储加载失败:', error);
    return false;
  }
}

function clearLocalStorage() {
  localStorage.removeItem('fitcoach_data');
  console.log('本地存储已清空');
  showToast('✓ 已重置为默认设置');
}

// ─────────────────────────────────────────
// 15. 全局更新用户信息
// ─────────────────────────────────────────
function updateAllUserInfo() {
  const name = UserProfile.name;
  const avatarChar = name ? name.charAt(0).toUpperCase() : '张';

  // 更新侧边栏头像和名字
  const userAvatar = document.querySelector('.user-avatar');
  const userName = document.querySelector('.user-name');
  if (userAvatar) userAvatar.textContent = avatarChar;
  if (userName) userName.textContent = name;

  // 更新首页标题
  const dashboardTitle = document.querySelector('#page-dashboard h1');
  if (dashboardTitle) {
    dashboardTitle.textContent = `早上好，${name} 👋`;
  }

  // 更新健康档案页面的姓名输入框
  const profileNameInput = document.querySelector('#page-profile input[placeholder="姓名"]');
  if (profileNameInput) {
    profileNameInput.value = name;
  }

  console.log('用户信息已全局更新:', { name, avatar: avatarChar });
}

