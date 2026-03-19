/**
 * FitCoach AI - 自动化测试脚本
 * 在浏览器控制台运行此脚本进行功能验证
 */

// ========================
// 1. 核心模块测试
// ========================
const TestRunner = {
  results: [],

  assert(condition, testName, details = '') {
    const result = condition ? 'pass' : 'fail';
    this.results.push({ test: testName, details, result });
    console.log(`[${result === 'pass' ? '✓' : '✗'}] ${testName}${details ? ': ' + details : ''}`);
    return condition;
  },

  summary() {
    const pass = this.results.filter(r => r.result === 'pass').length;
    const fail = this.results.filter(r => r.result === 'fail').length;
    const total = this.results.length;
    console.log(`\n═══════════════════════════════════`);
    console.log(`测试完成: ${pass}/${total} 通过 (${Math.round(pass/total*100)}%)`);
    if (fail > 0) {
      console.log(`❌ 失败测试:`);
      this.results.filter(r => r.result === 'fail').forEach(r => console.log(`   - ${r.test}: ${r.details}`));
    }
    console.log(`═══════════════════════════════════\n`);
    return { pass, fail, total };
  }
};

// ========================
// 2. 页面导航测试
// ========================
function testNavigation() {
  console.log('📍 测试: 页面导航');
  const pages = ['dashboard', 'profile', 'plan', 'today', 'analysis', 'garmin', 'ai-chat'];
  pages.forEach(page => {
    navigate(page);
    const activePage = document.querySelector('.page.active');
    const activeNav = document.querySelector(`[data-page="${page}"]`);
    TestRunner.assert(
      activePage && activePage.id === `page-${page}`,
      `导航到 ${page}`,
      `页面ID: ${activePage?.id}, 导航高亮: ${activeNav?.classList.contains('active')}`
    );
  });
  navigate('dashboard'); // 返回首页
}

// ========================
// 3. 规则引擎测试
// ========================
function testHeartRateZones() {
  console.log('\n💓 测试: 心率区间计算 (Karvonen公式)');
  const zones = RuleEngine.calcHeartRateZones(58, 188);
  
  // 验证Z2区间 (60-70%)
  TestRunner.assert(zones.z2.min === 135, 'Z2下限', `预期135, 实际${zones.z2.min}`);
  TestRunner.assert(zones.z2.max === 150, 'Z2上限', `预期150, 实际${zones.z2.max}`);
  
  // 验证Z3区间 (70-80%)
  TestRunner.assert(zones.z3.min === 150, 'Z3下限', `预期150, 实际${zones.z3.min}`);
  TestRunner.assert(zones.z3.max === 166, 'Z3上限', `预期166, 实际${zones.z3.max}`);
  
  console.log('  计算结果:', zones);
}

function testTrainingReadiness() {
  console.log('\n📊 测试: 训练就绪度评估');
  const readiness = RuleEngine.assessTrainingReadiness({
    hrv: 54,
    sleepScore: 74,
    stressLevel: 32,
    bodyBattery: 86
  });
  
  TestRunner.assert(readiness.score > 0 && readiness.score <= 100, '评分范围', `评分${readiness.score}`);
  TestRunner.assert(['最佳', '良好', '一般', '建议休息'].includes(readiness.level), '等级有效', `等级${readiness.level}`);
  TestRunner.assert(readiness.color, '颜色返回', `颜色${readiness.color}`);
  
  console.log('  评估结果:', readiness);
}

function testPlanGeneration() {
  console.log('\n📅 测试: 4周计划生成');
  const zones = RuleEngine.calcHeartRateZones(58, 188);
  const plan = RuleEngine.generate4WeekPlan(UserProfile, zones);
  
  TestRunner.assert(Array.isArray(plan) && plan.length === 4, '计划数量', `${plan.length}周`);
  TestRunner.assert(plan.every(w => w.days && w.days.length === 7), '每周7天', '所有周份包含7天');
  TestRunner.assert(plan.every(w => w.week >= 1 && w.week <= 4), '周次编号', '1-4周');
  
  console.log('  计划预览:', plan.map(w => `第${w.week}周: ${w.days.length}天训练`));
}

// ========================
// 4. AI对话测试
// ========================
async function testAIChat() {
  console.log('\n🤖 测试: AI教练对话');
  
  const testCases = [
    { msg: '今天适合训练吗', expectedKeyword: 'HRV' },
    { msg: '膝盖疼怎么办', expectedKeyword: '膝盖' },
    { msg: '如何提高配速', expectedKeyword: '配速' },
    { msg: '分析本周数据', expectedKeyword: '分析' },
    { msg: '怎么备赛半马', expectedKeyword: '半马' },
  ];
  
  for (const tc of testCases) {
    const reply = await AICoach.generateResponse(tc.msg);
    TestRunner.assert(
      reply.includes(tc.expectedKeyword),
      `关键词匹配: "${tc.msg}"`,
      `包含"${tc.expectedKeyword}"`
    );
  }
  
  // 测试通用回复
  const genericReply = await AICoach.generateResponse('随便问点什么');
  TestRunner.assert(genericReply.length > 0, '通用回复', `长度${genericReply.length}字符`);
}

// ========================
// 5. 数据可视化测试
// ========================
function testCharts() {
  console.log('\n📈 测试: 数据可视化');
  
  navigate('analysis');
  
  const loadCanvas = document.getElementById('loadCanvas');
  const radarSvg = document.getElementById('radarSvg');
  
  TestRunner.assert(loadCanvas !== null, 'Canvas折线图存在', `width:${loadCanvas?.width}`);
  TestRunner.assert(radarSvg !== null, 'SVG雷达图存在', `viewBox:${radarSvg?.getAttribute('viewBox')}`);
  
  // 测试折线图绘制
  if (loadCanvas) {
    drawLoadChart();
    const ctx = loadCanvas.getContext('2d');
    TestRunner.assert(ctx !== null, 'Canvas上下文', '可获取2D上下文');
  }
  
  // 测试雷达图绘制
  if (radarSvg) {
    drawRadarChart();
    TestRunner.assert(radarSvg.children.length > 0, 'SVG内容', `${radarSvg.children.length}个子元素`);
  }
}

// ========================
// 6. 表单交互测试
// ========================
function testProfileForm() {
  console.log('\n📝 测试: 健康档案表单');
  
  navigate('profile');
  
  // 测试运动级别选择
  const levelOptions = document.querySelectorAll('.level-option');
  TestRunner.assert(levelOptions.length === 3, '运动级别选项', `${levelOptions.length}个`);
  
  if (levelOptions[1]) {
    levelOptions[1].click();
    TestRunner.assert(
      UserProfile.fitnessLevel === 'intermediate',
      '级别切换到中级',
      `当前值:${UserProfile.fitnessLevel}`
    );
  }
  
  // 测试标签切换
  const tags = document.querySelectorAll('.tag');
  const firstTag = tags[0];
  if (firstTag) {
    const isActive = firstTag.classList.contains('active');
    firstTag.click();
    TestRunner.assert(
      firstTag.classList.contains('active') !== isActive,
      '标签切换',
      `状态改变`
    );
  }
  
  // 测试强度滑杆
  const sliders = document.querySelectorAll('.intensity-range');
  if (sliders[0]) {
    sliders[0].value = 4;
    sliders[0].dispatchEvent(new Event('input'));
    const label = sliders[0].nextElementSibling;
    TestRunner.assert(label && label.textContent === '较强', '强度标签更新', `标签:${label?.textContent}`);
  }

  // 测试保存档案功能
  const oldName = UserProfile.name;
  const nameInput = document.querySelector('input[placeholder="姓名"]');
  if (nameInput) {
    nameInput.value = '张测试';
    saveProfile();
    TestRunner.assert(
      UserProfile.name === '张测试',
      '档案保存 - 用户名更新',
      `保存后:${UserProfile.name}`
    );

    // 恢复原值
    UserProfile.name = oldName;
    if (nameInput) nameInput.value = oldName;
  }

  // 测试BMI自动计算
  const heightInput = document.querySelector('input[placeholder="身高"]');
  const weightInput = document.querySelector('input[placeholder="体重"]');
  const bmiInput = document.querySelector('input[placeholder="BMI"]');

  if (heightInput && weightInput && bmiInput) {
    heightInput.value = 180;
    weightInput.value = 80;
    calculateBMI();
    const expectedBMI = (80 / ((180/100) ** 2)).toFixed(1);
    TestRunner.assert(
      bmiInput.value === expectedBMI,
      'BMI自动计算',
      `身高180cm体重80kg → BMI${bmiInput.value}`
    );
  }
}

// ========================
// 7. 实时训练测试
// ========================
function testLiveTraining() {
  console.log('\n⏱️ 测试: 今日训练实时数据');
  
  navigate('today');
  
  const liveElements = {
    HR: document.getElementById('liveHR'),
    Pace: document.getElementById('livePace'),
    Dist: document.getElementById('liveDist'),
    Time: document.getElementById('liveTime'),
    Cal: document.getElementById('liveCal'),
    Cadence: document.getElementById('liveCadence'),
  };
  
  for (const [key, el] of Object.entries(liveElements)) {
    TestRunner.assert(el !== null, `${key}显示元素`, `textContent:${el?.textContent}`);
  }
  
  // 测试暂停功能
  pauseTraining();
  TestRunner.assert(!trainingActive, '暂停训练', `状态:${trainingActive}`);
  pauseTraining(); // 继续
  TestRunner.assert(trainingActive, '继续训练', `状态:${trainingActive}`);
  
  // 测试强度面板
  adjustIntensity();
  const panel = document.getElementById('intensityPanel');
  TestRunner.assert(panel && panel.style.display === 'block', '强度面板显示', `display:${panel?.style.display}`);
  adjustIntensity(); // 隐藏
}

// ========================
// 8. Garmin同步测试
// ========================
function testGarminSync() {
  console.log('\n⌚ 测试: Garmin设备同步');
  
  navigate('garmin');
  
  const syncBtn = document.querySelector('.btn-sync');
  TestRunner.assert(syncBtn !== null, '同步按钮存在');
  
  // 注意: 实际同步会改变按钮状态，这里只测试函数存在
  TestRunner.assert(typeof syncGarmin === 'function', 'syncGarmin函数', '已定义');
  
  // 检查同步数据显示
  const syncItems = document.querySelectorAll('.sync-item');
  TestRunner.assert(syncItems.length === 6, '同步指标', `${syncItems.length}个指标`);
}

// ========================
// 主运行函数
// ========================
async function runAllTests() {
  console.log('═══════════════════════════════════');
  console.log('  FitCoach AI 功能自动化测试');
  console.log('═══════════════════════════════════\n');
  
  try {
    // 等待页面加载
    await new Promise(resolve => setTimeout(resolve, 500));
    
    testNavigation();
    testHeartRateZones();
    testTrainingReadiness();
    testPlanGeneration();
    testCharts();
    testProfileForm();
    testLiveTraining();
    testGarminSync();
    await testAIChat();
    
    return TestRunner.summary();
  } catch (error) {
    console.error('❌ 测试运行出错:', error);
    return { pass: 0, fail: 1, total: 1 };
  }
}

// 如果直接运行脚本
if (typeof window !== 'undefined') {
  window.runFitCoachTests = runAllTests;
  console.log('✅ 测试脚本已加载，运行 runFitCoachTests() 开始测试');
} else {
  module.exports = { runAllTests, TestRunner };
}
