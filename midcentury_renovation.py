# -*- coding: utf-8 -*-
"""
中古风装修视频生成器
风格：Mid-Century Modern（中古现代风）
户型：89方A高层 3室2厅1卫（沁瑄云上府）
时长：30秒 @30fps = 900帧
场景划分：
  0-5s   (0-149帧)   : 开场标题 + 户型图展示
  5-10s  (150-299帧) : 毛坯阶段（空白混凝土房间）
  10-16s (300-479帧) : 硬装施工动画（墙面、地板铺设）
  16-22s (480-659帧) : 主要家具落位（沙发、茶几、餐桌）
  22-27s (660-809帧) : 软装细节（挂画、绿植、灯具、地毯）
  27-30s (810-899帧) : 完成全景 + 结尾标题
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import os

# ─────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────
W, H = 1280, 720
FPS = 30
TOTAL_FRAMES = 900
OUT_PATH = r"c:/Users/yezhenzhen/WorkBuddy/20260318141233/midcentury_renovation.mp4"

# ── 中古风调色板 ──────────────────────────────
C_BG        = (245, 235, 220)   # 米白/奶油色
C_WALL      = (228, 215, 195)   # 暖米墙色
C_FLOOR     = (160, 120,  75)   # 柚木地板棕
C_FLOOR2    = (140, 100,  60)   # 地板深色条纹
C_CONCRETE  = (185, 180, 172)   # 毛坯混凝土
C_GOLD      = (195, 158,  80)   # 金铜色
C_TEAL      = ( 72, 148, 140)   # 孔雀蓝绿
C_MUSTARD   = (210, 165,  55)   # 芥末黄
C_RUST      = (180,  80,  50)   # 锈橙
C_DARK      = ( 42,  35,  28)   # 深咖/近黑
C_OLIVE     = ( 90, 110,  60)   # 橄榄绿
C_CREAM     = (253, 246, 230)   # 象牙白
C_SHADOW    = ( 30,  25,  20)   # 阴影

# PIL颜色（RGB）
PC_WALL      = (228, 215, 195)
PC_FLOOR     = (160, 120,  75)
PC_FLOOR2    = (140, 100,  60)   # 地板深色条纹
PC_CONCRETE  = (185, 180, 172)
PC_GOLD      = (195, 158,  80)
PC_TEAL      = ( 72, 148, 140)
PC_MUSTARD   = (210, 165,  55)
PC_RUST      = (180,  80,  50)
PC_DARK      = ( 42,  35,  28)
PC_OLIVE     = ( 90, 110,  60)
PC_CREAM     = (253, 246, 230)
PC_BG        = (245, 235, 220)
PC_SHADOW    = (100,  80,  60)

def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t

def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2

def alpha_composite(base_img, overlay_img, x, y):
    """将overlay贴到base上"""
    bw, bh = base_img.size
    ow, oh = overlay_img.size
    x1 = max(0, x); y1 = max(0, y)
    x2 = min(bw, x + ow); y2 = min(bh, y + oh)
    if x2 <= x1 or y2 <= y1:
        return
    ox1 = x1 - x; oy1 = y1 - y
    ox2 = ox1 + (x2 - x1); oy2 = oy1 + (y2 - y1)
    region = overlay_img.crop((ox1, oy1, ox2, oy2))
    if overlay_img.mode == 'RGBA':
        base_img.paste(region, (x1, y1), region)
    else:
        base_img.paste(region, (x1, y1))

def try_font(size):
    """加载字体，失败则用默认"""
    paths = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def try_font_en(size):
    paths = [
        r"C:\Windows\Fonts\georgia.ttf",
        r"C:\Windows\Fonts\times.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

# ─────────────────────────────────────────────
# 绘制函数
# ─────────────────────────────────────────────

def draw_floorplan_icon(draw, cx, cy, scale=1.0, alpha=1.0):
    """简化版户型图图标"""
    s = scale
    rooms = [
        (cx-120*s, cy-80*s, cx+20*s,  cy+20*s,  PC_TEAL,    "客餐厅"),
        (cx-120*s, cy-150*s,cx-20*s,  cy-80*s,  PC_MUSTARD, "厨房"),
        (cx+20*s,  cy-150*s,cx+120*s, cy-60*s,  PC_RUST,    "书房"),
        (cx-120*s, cy+20*s, cx-20*s,  cy+120*s, PC_OLIVE,   "主卧"),
        (cx-20*s,  cy+20*s, cx+80*s,  cy+120*s, (160,120,100),"次卧"),
        (cx+80*s,  cy-60*s, cx+140*s, cy+40*s,  (130,160,170),"卫"),
    ]
    for x1,y1,x2,y2,col,label in rooms:
        r,g,b = col
        fill = (int(r), int(g), int(b), int(180*alpha))
        draw.rectangle([x1,y1,x2,y2], fill=fill[:3], outline=PC_DARK, width=2)

def draw_room_shell(img, frame, phase_t):
    """绘制房间透视外壳（地板+两面墙）"""
    draw = ImageDraw.Draw(img)
    # 地板
    floor_pts = [
        (int(200 + lerp(0,0,phase_t)), int(H-50)),
        (int(W-200), int(H-50)),
        (int(W-300 + lerp(100,0,phase_t)), int(H//2+80)),
        (int(300 + lerp(-100,0,phase_t)), int(H//2+80)),
    ]
    draw.polygon(floor_pts, fill=PC_FLOOR)
    # 地板条纹
    for i in range(8):
        ty = (H//2+80) + i * ((H-50-(H//2+80))//8)
        draw.line([(200,ty),(W-200,ty)], fill=PC_FLOOR2, width=1)

    # 后墙
    back_pts = [
        (300, H//2+80), (W-300, H//2+80),
        (W-300, 60),    (300, 60)
    ]
    draw.polygon(back_pts, fill=PC_WALL)
    # 墙面装饰线
    draw.rectangle([305, 65, W-305, H//2+75], outline=(210,200,185), width=2)
    draw.rectangle([320, 80, W-320, H//2+60], outline=(210,200,185), width=1)

    # 左侧墙
    left_pts = [
        (200, H-50), (300, H//2+80),
        (300, 60),   (150, 60)
    ]
    draw.polygon(left_pts, fill=(215, 202, 182))

    # 右侧墙
    right_pts = [
        (W-200, H-50), (W-300, H//2+80),
        (W-300, 60),   (W-150, 60)
    ]
    draw.polygon(right_pts, fill=(220, 208, 188))

    # 天花板
    ceil_pts = [
        (150,60),(W-150,60),(W-300,30),(300,30)
    ]
    draw.polygon(ceil_pts, fill=(240, 232, 218))

def draw_concrete_room(img, t):
    """毛坯混凝土房间"""
    draw = ImageDraw.Draw(img)
    # 地板 - 混凝土
    floor_pts = [
        (200, H-50),(W-200, H-50),
        (W-300, H//2+80),(300, H//2+80),
    ]
    draw.polygon(floor_pts, fill=(175,170,162))
    # 地板裂缝
    for i in range(5):
        x1 = 250 + i*150; y1 = H-100
        x2 = x1 + 80; y2 = H//2+120
        draw.line([(x1,y1),(x2,y2)], fill=(155,150,142), width=1)

    back_pts = [
        (300, H//2+80),(W-300,H//2+80),
        (W-300,60),(300,60)
    ]
    draw.polygon(back_pts, fill=PC_CONCRETE)
    # 后墙混凝土纹理
    for i in range(12):
        y = 65 + i * ((H//2+75-65)//12)
        draw.line([(305,y),(W-305,y)], fill=(175,170,162), width=1)

    left_pts = [(200,H-50),(300,H//2+80),(300,60),(150,60)]
    draw.polygon(left_pts, fill=(170,165,158))
    right_pts = [(W-200,H-50),(W-300,H//2+80),(W-300,60),(W-150,60)]
    draw.polygon(right_pts, fill=(178,173,165))
    ceil_pts = [(150,60),(W-150,60),(W-300,30),(300,30)]
    draw.polygon(ceil_pts, fill=(190,185,178))

    # 裸露管线
    draw.line([(300,120),(W-300,120)], fill=(140,135,128), width=4)
    draw.ellipse([460,112,480,128], fill=(120,115,108))
    draw.ellipse([760,112,780,128], fill=(120,115,108))

def draw_sofa(draw, x, y, w, h, color=PC_TEAL, alpha=1.0):
    """绘制沙发（透视）"""
    # 沙发主体
    draw.rectangle([x, y, x+w, y+h], fill=color)
    # 沙发靠背
    draw.rectangle([x, y-h//3, x+w, y+10], fill=tuple(max(0,c-20) for c in color))
    # 沙发腿
    leg_col = PC_GOLD
    for lx in [x+10, x+w-15]:
        draw.rectangle([lx, y+h, lx+8, y+h+18], fill=leg_col)
    # 沙发扶手
    draw.rectangle([x-12, y-h//3+5, x+5, y+h], fill=tuple(max(0,c-10) for c in color))
    draw.rectangle([x+w-5, y-h//3+5, x+w+12, y+h], fill=tuple(max(0,c-10) for c in color))
    # 座垫分割线
    draw.line([(x+w//3, y),(x+w//3, y+h)], fill=tuple(max(0,c-30) for c in color), width=2)
    draw.line([(x+2*w//3, y),(x+2*w//3, y+h)], fill=tuple(max(0,c-30) for c in color), width=2)

def draw_coffee_table(draw, x, y, w, h):
    """茶几（中古风细腿）"""
    # 桌面
    draw.ellipse([x, y, x+w, y+h//3], fill=(180,140,85))
    draw.ellipse([x+3, y+3, x+w-3, y+h//3-3], fill=(195,155,95))
    # 腿
    leg_positions = [(x+w//4, y+h//3), (x+3*w//4, y+h//3)]
    for lx, ly in leg_positions:
        pts = [(lx,ly),(lx-6,ly+h*2//3),(lx-3,ly+h*2//3+5),(lx+3,ly+h*2//3+5),(lx+6,ly+h*2//3),(lx,ly)]
        draw.polygon(pts, fill=PC_GOLD)

def draw_armchair(draw, x, y):
    """单人椅"""
    w, h = 100, 70
    col = PC_MUSTARD
    draw.rectangle([x, y, x+w, y+h], fill=col)
    draw.rectangle([x, y-30, x+w, y+10], fill=tuple(max(0,c-20) for c in col))
    draw.rectangle([x-10, y-30, x+8, y+h], fill=tuple(max(0,c-10) for c in col))
    draw.rectangle([x+w-8, y-30, x+w+10, y+h], fill=tuple(max(0,c-10) for c in col))
    for lx in [x+8, x+w-16]:
        draw.rectangle([lx, y+h, lx+7, y+h+15], fill=PC_GOLD)

def draw_floor_lamp(draw, x, y):
    """落地灯（中古风）"""
    # 灯杆
    draw.line([(x, y), (x, y-180)], fill=PC_GOLD, width=4)
    # 灯罩
    pts = [(x-35, y-180),(x+35,y-180),(x+22,y-230),(x-22,y-230)]
    draw.polygon(pts, fill=PC_MUSTARD)
    draw.polygon(pts, outline=PC_DARK, width=2)
    # 底座
    draw.ellipse([x-20, y-12, x+20, y+8], fill=PC_GOLD)

def draw_plant(draw, x, y):
    """绿植（龟背竹风格）"""
    # 花盆
    pot_pts = [(x-18,y),(x+18,y),(x+12,y+35),(x-12,y+35)]
    draw.polygon(pot_pts, fill=PC_RUST)
    draw.ellipse([x-18,y-8,x+18,y+8], fill=(190,90,60))
    # 叶子
    leaf_data = [
        (x-5, y-20, x-45, y-70, PC_OLIVE),
        (x+5, y-20, x+50, y-65, (80,125,55)),
        (x-2, y-30, x-30, y-90, (70,115,50)),
        (x+3, y-25, x+35, y-80, PC_OLIVE),
        (x,   y-35, x-10, y-100,(75,120,52)),
    ]
    for x1,y1,x2,y2,col in leaf_data:
        draw.line([(x1,y1),(x2,y2)], fill=col, width=3)
        # 叶片
        mid_x = (x1+x2)//2; mid_y = (y1+y2)//2
        draw.ellipse([x2-18,y2-12,x2+18,y2+12], fill=col)

def draw_rug(draw, x, y, w, h):
    """地毯（几何图案）"""
    # 基础
    draw.ellipse([x,y,x+w,y+h], fill=(210,175,130))
    # 中古风几何边框
    for margin in [8, 18]:
        mx = x+margin; my = y+margin*h//w
        mw = x+w-margin; mh = y+h-margin*h//w
        draw.ellipse([mx,my,mw,mh], outline=PC_RUST, width=2)
    # 菱形中心图案
    cx = x + w//2; cy = y + h//2
    for i in range(3):
        r = 30 - i*8
        diamond = [(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)]
        draw.polygon(diamond, outline=PC_TEAL, width=2)

def draw_wall_art(draw, x, y, w, h):
    """中古风挂画（几何抽象）"""
    # 画框
    draw.rectangle([x-5,y-5,x+w+5,y+h+5], fill=(80,60,40))
    draw.rectangle([x,y,x+w,y+h], fill=PC_CREAM)
    # 画面内容 - 抽象几何
    cx = x + w//2; cy = y + h//2
    # 大圆
    draw.ellipse([cx-40,cy-40,cx+40,cy+40], fill=PC_TEAL)
    # 三角
    tri = [(cx-50,cy+30),(cx+50,cy+30),(cx,cy-45)]
    draw.polygon(tri, fill=PC_MUSTARD)
    # 小矩形
    draw.rectangle([cx-15,cy-12,cx+15,cy+12], fill=PC_RUST)
    # 线条装饰
    for i in range(4):
        draw.line([(x+15+i*20, y+8),(x+15+i*20, y+h-8)], fill=(200,185,160), width=1)

def draw_dining_set(draw, x, y):
    """餐桌椅"""
    # 圆形餐桌
    tw = 180; th = 80
    draw.ellipse([x,y,x+tw,y+th], fill=(175,135,80))
    draw.ellipse([x+5,y+5,x+tw-5,y+th-5], fill=(190,150,90))
    # 桌腿（锥形）
    cx = x+tw//2; cy = y+th
    for angle, r in [(210,55),(330,55),(90,40)]:
        rad = math.radians(angle)
        lx = int(cx + r*math.cos(rad)); ly = int(cy + r//2*math.sin(rad))
        draw.line([(cx,cy),(lx,ly+30)], fill=PC_GOLD, width=5)
    # 椅子
    chair_pos = [
        (x-60, y+th//2-25),
        (x+tw+10, y+th//2-25),
        (x+tw//2-25, y-55),
        (x+tw//2-25, y+th+10),
    ]
    for cx2,cy2 in chair_pos:
        draw.rectangle([cx2,cy2,cx2+50,cy2+35], fill=PC_RUST)
        draw.rectangle([cx2,cy2-20,cx2+50,cy2+5], fill=(165,70,42))
        for lx2 in [cx2+5, cx2+40]:
            draw.rectangle([lx2,cy2+35,lx2+5,cy2+50], fill=PC_GOLD)

def draw_pendant_light(draw, cx, y, r=35):
    """吊灯（球形）"""
    # 吊线
    draw.line([(cx,y-80),(cx,y-r)], fill=PC_GOLD, width=3)
    # 灯体
    draw.ellipse([cx-r,y-r,cx+r,y+r], fill=PC_MUSTARD)
    draw.ellipse([cx-r+4,y-r+4,cx+r-4,y+r-4], fill=(225,185,70))
    # 光晕效果（半透明圆）
    glow = Image.new('RGBA', (r*4, r*4), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    for gr in range(r*2, 0, -1):
        alpha = int(40 * (1 - gr/(r*2)))
        gd.ellipse([r*2-gr, r*2-gr, r*2+gr, r*2+gr], fill=(255,220,100,alpha))
    return glow, cx - r*2, y - r*2

def draw_title_card(img, title, subtitle, t):
    """标题卡（淡入淡出）"""
    draw = ImageDraw.Draw(img)
    alpha = ease_in_out(t)

    # 背景遮罩
    overlay = Image.new('RGBA', (W,H), (245,235,220,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0,0,W,H], fill=(245,235,220,int(220*alpha)))

    # 装饰线
    line_y = H//2 + 50
    lw = int(400 * alpha)
    od.line([(W//2-lw, line_y-50),(W//2+lw, line_y-50)], fill=(*PC_GOLD, int(255*alpha)), width=2)
    od.line([(W//2-lw, line_y+80),(W//2+lw, line_y+80)], fill=(*PC_GOLD, int(255*alpha)), width=2)

    img.paste(overlay, (0,0), overlay)
    draw = ImageDraw.Draw(img)

    font_big = try_font(72)
    font_sm  = try_font(28)
    font_en  = try_font_en(20)

    # 主标题
    tx = W//2; ty = H//2 - 20
    # 文字阴影
    draw.text((tx+3,ty+3), title, font=font_big, fill=(80,60,40), anchor="mm")
    draw.text((tx,ty), title, font=font_big, fill=PC_DARK, anchor="mm")

    # 副标题
    draw.text((tx, ty+70), subtitle, font=font_sm, fill=PC_TEAL, anchor="mm")

    # 英文点缀
    draw.text((tx, ty+110), "MID-CENTURY MODERN RENOVATION", font=font_en, fill=PC_GOLD, anchor="mm")

def draw_progress_bar(draw, frame, scene_name, color=PC_TEAL):
    """底部进度条 + 场景名"""
    progress = frame / TOTAL_FRAMES
    bar_w = int(W * progress)
    draw.rectangle([0, H-6, bar_w, H], fill=color)
    draw.rectangle([0, H-6, W, H], outline=PC_DARK, width=1)

    font = try_font(22)
    draw.text((20, H-35), scene_name, font=font, fill=PC_DARK)

    # 时间
    secs = frame // FPS
    font2 = try_font_en(18)
    draw.text((W-60, H-35), f"{secs:02d}s", font=font2, fill=PC_SHADOW)

def draw_scene_label(draw, text, alpha=1.0):
    """场景过渡标签"""
    font = try_font(36)
    x, y = W//2, 55
    draw.text((x+2, y+2), text, font=font, fill=(80,60,40), anchor="mm")
    draw.text((x, y), text, font=font, fill=PC_DARK, anchor="mm")

# ─────────────────────────────────────────────
# 场景渲染
# ─────────────────────────────────────────────

def render_scene_intro(frame, local_t):
    """0-5s: 开场 - 中古风标题"""
    img = Image.new('RGB', (W,H), PC_BG)
    draw = ImageDraw.Draw(img)

    # 背景纹理（轻微噪点感）
    for i in range(0, W, 60):
        draw.line([(i,0),(i,H)], fill=(240,230,215), width=1)
    for j in range(0, H, 60):
        draw.line([(0,j),(W,j)], fill=(240,230,215), width=1)

    # 中古风装饰框
    margin = 40
    t_frame = ease_in_out(min(local_t * 2, 1.0))
    frame_w = int((W - margin*2) * t_frame)
    # 四角装饰
    corner_size = 40
    for cx2, cy2, dx, dy in [
        (margin, margin, 1, 1),
        (W-margin, margin, -1, 1),
        (margin, H-margin, 1, -1),
        (W-margin, H-margin, -1, -1),
    ]:
        draw.line([(cx2, cy2),(cx2+dx*corner_size, cy2)], fill=PC_GOLD, width=3)
        draw.line([(cx2, cy2),(cx2, cy2+dy*corner_size)], fill=PC_GOLD, width=3)

    # 户型图轮廓（右侧小图）
    fp_alpha = ease_out(max(0, (local_t - 0.3) / 0.7))
    if fp_alpha > 0:
        fp_img = Image.new('RGBA', (W,H), (0,0,0,0))
        fp_draw = ImageDraw.Draw(fp_img)
        draw_floorplan_icon(fp_draw, W-200, H//2, scale=0.55, alpha=fp_alpha)
        img.paste(fp_img, (0,0), fp_img)
        draw = ImageDraw.Draw(img)

        font_sm = try_font(18)
        draw.text((W-200, H//2+130), "89㎡ A户型", font=font_sm, fill=PC_DARK, anchor="mm")
        draw.text((W-200, H//2+155), "3室 2厅 1卫", font=font_sm, fill=PC_TEAL, anchor="mm")

    # 主标题淡入
    title_alpha = ease_in_out(min(local_t / 0.5, 1.0))
    draw_title_card(img, "沁瑄云上府", "中古现代风 | 软装全案设计", title_alpha)

    return img

def render_scene_rough(frame, local_t):
    """5-10s: 毛坯房展示"""
    img = Image.new('RGB', (W,H), (190,185,178))
    draw = ImageDraw.Draw(img)

    # 淡入
    fade_in = ease_out(min(local_t * 3, 1.0))

    draw_concrete_room(img, local_t)
    draw = ImageDraw.Draw(img)

    # 标注尺寸（逐渐出现）
    if local_t > 0.3:
        label_alpha = ease_out((local_t-0.3)/0.7)
        font = try_font(20)
        annotations = [
            (W//2, H//2+40, "客餐厅 27㎡"),
            (320,  H//2-50, "厨房 5㎡"),
            (W//2+200, H//2-80, "书房 6.8㎡"),
            (280, H-150, "主卧 12.6㎡"),
            (W//2+50, H-150, "次卧 9㎡"),
        ]
        for ax, ay, text in annotations:
            draw.text((ax+1,ay+1), text, font=font, fill=(100,90,80), anchor="mm")
            draw.text((ax,ay), text, font=font, fill=PC_DARK, anchor="mm")

    # 场景标签
    label_t = ease_in_out(min(local_t * 4, 1.0))
    draw_scene_label(draw, "▌ 毛坯交付", label_t)
    draw_progress_bar(draw, frame, "毛坯阶段", (150, 145, 138))

    # 标注：测量线
    if local_t > 0.5:
        draw.line([(200,H-80),(W-200,H-80)], fill=PC_GOLD, width=2)
        draw.line([(200,H-90),(200,H-70)], fill=PC_GOLD, width=2)
        draw.line([(W-200,H-90),(W-200,H-70)], fill=PC_GOLD, width=2)
        font2 = try_font_en(18)
        draw.text((W//2, H-65), "5900mm", font=font2, fill=PC_GOLD, anchor="mm")

    return img

def render_scene_hardwork(frame, local_t):
    """10-16s: 硬装施工动画"""
    img = Image.new('RGB', (W,H), (190,185,178))
    draw_concrete_room(img, local_t)
    draw = ImageDraw.Draw(img)

    # 阶段1(0-0.4): 地板铺设
    floor_t = ease_in_out(min(local_t / 0.4, 1.0))
    # 铺地板动画（从左到右展开）
    floor_pts_full = [
        (200, H-50),(W-200, H-50),
        (W-300, H//2+80),(300, H//2+80),
    ]
    clip_x = int(200 + (W-400) * floor_t)
    floor_pts_clip = [
        (200, H-50),(clip_x, H-50),
        (int(300+(clip_x-200)*(W-600)/(W-400)), H//2+80),(300, H//2+80),
    ]
    if floor_t > 0:
        draw.polygon(floor_pts_clip, fill=PC_FLOOR)
        # 地板条纹
        for i in range(8):
            ty = (H//2+80) + i * ((H-50-(H//2+80))//8)
            x_end = min(clip_x, W-200)
            if x_end > 200:
                draw.line([(200,ty),(x_end,ty)], fill=PC_FLOOR2, width=1)

    # 阶段2(0.35-0.7): 墙面涂刷（后墙变色）
    wall_t = ease_in_out(max(0,(local_t-0.35)/0.35))
    wall_col = tuple(int(lerp(PC_CONCRETE[i], PC_WALL[i], wall_t)) for i in range(3))
    wall_clip_h = int((H//2+80-60) * wall_t)
    back_pts = [(300,H//2+80),(W-300,H//2+80),(W-300,60),(300,60)]
    draw.polygon(back_pts, fill=wall_col)
    # 墙刷痕迹（水平线）
    if 0 < wall_t < 1:
        brush_y = int((H//2+80) - wall_clip_h)
        draw.line([(305, brush_y),(W-305, brush_y)], fill=PC_GOLD, width=3)
        # 刷毛
        for bx in range(310, W-310, 15):
            draw.line([(bx, brush_y),(bx+8, brush_y+10)], fill=(200,190,170), width=2)

    # 阶段3(0.65-1.0): 左右墙处理
    side_t = ease_in_out(max(0,(local_t-0.65)/0.35))
    lwall_col = tuple(int(lerp(c, max(0,c-13), side_t)) for c in PC_WALL)
    left_pts = [(200,H-50),(300,H//2+80),(300,60),(150,60)]
    draw.polygon(left_pts, fill=lwall_col)
    right_pts = [(W-200,H-50),(W-300,H//2+80),(W-300,60),(W-150,60)]
    draw.polygon(right_pts, fill=tuple(int(c+5) for c in lwall_col))
    ceil_pts = [(150,60),(W-150,60),(W-300,30),(300,30)]
    draw.polygon(ceil_pts, fill=(242,235,220))

    # 装饰踢脚线（最后出现）
    if local_t > 0.8:
        skirting_t = (local_t-0.8)/0.2
        draw.line([(200,H-52),(int(200+(W-400)*skirting_t),H-52)], fill=PC_CREAM, width=4)

    draw_scene_label(draw, "▌ 硬装施工", ease_in_out(min(local_t*4,1.0)))
    draw_progress_bar(draw, frame, "地板 · 墙面 · 吊顶", (100, 120, 140))

    # 工具图标（简单文字标注）
    font_icon = try_font(30)
    icons_alpha = 1.0 - ease_out(max(0,local_t-0.85)/0.15)
    if icons_alpha > 0.1:
        draw.text((80, 80), "[工具]", font=font_icon, fill=PC_DARK)

    return img

def render_scene_furniture(frame, local_t):
    """16-22s: 主要家具落位"""
    img = Image.new('RGB', (W,H), PC_BG)
    draw_room_shell(img, frame, 1.0)
    draw = ImageDraw.Draw(img)

    # 地毯 (0-0.25)
    rug_t = ease_out(min(local_t/0.25, 1.0))
    if rug_t > 0:
        rug_y_offset = int(lerp(60, 0, rug_t))
        draw_rug(draw, 320, H-230+rug_y_offset, 420, 130)

    # 沙发 (0.2-0.5)
    sofa_t = ease_out(max(0,(local_t-0.2)/0.3))
    if sofa_t > 0:
        sofa_x_offset = int(lerp(-200, 0, sofa_t))
        draw_sofa(draw, 280+sofa_x_offset, H-280, 360, 90, PC_TEAL)

    # 茶几 (0.4-0.6)
    table_t = ease_out(max(0,(local_t-0.4)/0.2))
    if table_t > 0:
        tbl_y_offset = int(lerp(-30, 0, table_t))
        draw_coffee_table(draw, 450, H-200+tbl_y_offset, 180, 80)

    # 单人椅 (0.55-0.75)
    chair_t = ease_out(max(0,(local_t-0.55)/0.2))
    if chair_t > 0:
        ch_x_offset = int(lerp(200, 0, chair_t))
        draw_armchair(draw, 730+ch_x_offset, H-250)

    # 落地灯 (0.7-0.85)
    lamp_t = ease_out(max(0,(local_t-0.7)/0.15))
    if lamp_t > 0:
        lamp_y_offset = int(lerp(-40, 0, lamp_t))
        draw_floor_lamp(draw, 250, H-50+lamp_y_offset)

    # 餐桌 (0.8-1.0) - 左侧
    dining_t = ease_out(max(0,(local_t-0.8)/0.2))
    if dining_t > 0:
        d_x_offset = int(lerp(-150, 0, dining_t))
        # 简化：只画餐桌（视角限制）
        dtx = 850+d_x_offset
        dty = H-250
        draw.ellipse([dtx,dty,dtx+140,dty+60], fill=(180,140,85))
        draw.ellipse([dtx+5,dty+5,dtx+135,dty+55], fill=(195,155,95))
        for lx2 in [dtx+25,dtx+110]:
            draw.rectangle([lx2,dty+55,lx2+8,dty+85], fill=PC_GOLD)

    draw_scene_label(draw, "▌ 家具落位", ease_in_out(min(local_t*4,1.0)))
    draw_progress_bar(draw, frame, "沙发 · 茶几 · 餐桌", tuple(c//2 for c in PC_TEAL))

    return img

def render_scene_softdeco(frame, local_t):
    """22-27s: 软装细节"""
    img = Image.new('RGB', (W,H), PC_BG)
    draw_room_shell(img, frame, 1.0)
    draw = ImageDraw.Draw(img)

    # 基础家具（已放好）
    draw_rug(draw, 320, H-230, 420, 130)
    draw_sofa(draw, 280, H-280, 360, 90, PC_TEAL)
    draw_coffee_table(draw, 450, H-200, 180, 80)
    draw_armchair(draw, 730, H-250)
    draw_floor_lamp(draw, 250, H-50)

    # 挂画 (0-0.25)
    art_t = ease_out(min(local_t/0.25, 1.0))
    if art_t > 0:
        art_y_offset = int(lerp(-30, 0, art_t))
        draw_wall_art(draw, W//2-100, 100+art_y_offset, 200, 140)

    # 绿植 (0.2-0.45)
    plant_t = ease_out(max(0,(local_t-0.2)/0.25))
    if plant_t > 0:
        plant_scale = lerp(0, 1, plant_t)
        p_img = Image.new('RGBA', (W,H), (0,0,0,0))
        pd = ImageDraw.Draw(p_img)
        # 主植物
        draw_plant(pd, 870, H-90)
        # 小植物（右侧）
        draw_plant(pd, 960, H-105)
        img.paste(p_img, (0,0), p_img)
        draw = ImageDraw.Draw(img)

    # 吊灯 (0.35-0.55)
    light_t = ease_out(max(0,(local_t-0.35)/0.2))
    if light_t > 0:
        glow, gx, gy = draw_pendant_light(draw, W//2, H//2-80)
        glow_alpha = int(255 * light_t)
        r2,g2,b2,a2 = glow.split()
        a2 = a2.point(lambda x: x * light_t)
        glow.putalpha(a2)
        img.paste(glow, (gx, gy), glow)
        draw = ImageDraw.Draw(img)
        draw_pendant_light(draw, W//2, H//2-80)

    # 小摆件 (0.5-0.7): 茶几上的书、蜡烛
    decor_t = ease_out(max(0,(local_t-0.5)/0.2))
    if decor_t > 0:
        # 书本堆叠
        for i, col in enumerate([(PC_TEAL),(PC_RUST),(PC_MUSTARD)]):
            bx = 480 + i*18; by = H-205 - i*5
            draw.rectangle([bx, by, bx+40, by+8+i*2], fill=col)
        # 花瓶
        draw.ellipse([570, H-218, 590, H-190], fill=(165,130,80))
        draw.ellipse([573, H-235, 587, H-215], fill=(175,140,88))
        # 小花
        for petal in range(5):
            ang = math.radians(petal*72)
            px = int(581 + 7*math.cos(ang)); py = int(H-242 + 5*math.sin(ang))
            draw.ellipse([px-4,py-3,px+4,py+3], fill=PC_RUST)
        draw.ellipse([578,H-244,584,H-238], fill=PC_MUSTARD)

    # 抱枕 (0.65-0.85)
    pillow_t = ease_out(max(0,(local_t-0.65)/0.2))
    if pillow_t > 0:
        # 沙发抱枕
        for px, col in [(340, PC_MUSTARD),(420,(230,150,80)),(500,PC_RUST)]:
            draw.rounded_rectangle([px, H-292, px+58, H-242], radius=8, fill=col)
            # 抱枕图案
            cx2 = px+29; cy2 = H-267
            draw.line([(cx2-15,cy2),(cx2+15,cy2)], fill=tuple(max(0,c-30) for c in col), width=2)
            draw.line([(cx2,cy2-12),(cx2,cy2+12)], fill=tuple(max(0,c-30) for c in col), width=2)

    # 窗帘 (0.8-1.0) - 左右两侧
    curtain_t = ease_out(max(0,(local_t-0.8)/0.2))
    if curtain_t > 0:
        # 左窗帘
        ct_w = int(50 * curtain_t)
        draw.rectangle([150, 30, 150+ct_w, H//2+75], fill=PC_RUST)
        # 右窗帘
        draw.rectangle([W-150-ct_w, 30, W-150, H//2+75], fill=PC_RUST)
        # 帘杆
        draw.line([(145,30),(W-145,30)], fill=PC_GOLD, width=4)
        draw.ellipse([142,24,158,40], fill=PC_GOLD)
        draw.ellipse([W-158,24,W-142,40], fill=PC_GOLD)

    draw_scene_label(draw, "▌ 软装陈设", ease_in_out(min(local_t*4,1.0)))
    draw_progress_bar(draw, frame, "挂画 · 绿植 · 灯具 · 抱枕", tuple(c//2 for c in PC_RUST))

    return img

def render_scene_final(frame, local_t):
    """27-30s: 完成全景"""
    img = Image.new('RGB', (W,H), PC_BG)
    draw_room_shell(img, frame, 1.0)
    draw = ImageDraw.Draw(img)

    # 完整场景
    draw_rug(draw, 320, H-230, 420, 130)
    draw_sofa(draw, 280, H-280, 360, 90, PC_TEAL)
    draw_coffee_table(draw, 450, H-200, 180, 80)
    draw_armchair(draw, 730, H-250)
    draw_floor_lamp(draw, 250, H-50)
    draw_wall_art(draw, W//2-100, 100, 200, 140)

    # 绿植
    p_img = Image.new('RGBA', (W,H), (0,0,0,0))
    pd = ImageDraw.Draw(p_img)
    draw_plant(pd, 870, H-90)
    draw_plant(pd, 960, H-105)
    img.paste(p_img, (0,0), p_img)
    draw = ImageDraw.Draw(img)

    # 吊灯
    glow, gx, gy = draw_pendant_light(draw, W//2, H//2-80)
    img.paste(glow, (gx, gy), glow)
    draw = ImageDraw.Draw(img)
    draw_pendant_light(draw, W//2, H//2-80)

    # 抱枕
    for px, col in [(340, PC_MUSTARD),(420,(230,150,80)),(500,PC_RUST)]:
        draw.rounded_rectangle([px, H-292, px+58, H-242], radius=8, fill=col)

    # 茶几摆件
    for i, col in enumerate([PC_TEAL,PC_RUST,PC_MUSTARD]):
        bx = 480+i*18; by = H-205-i*5
        draw.rectangle([bx,by,bx+40,by+8+i*2], fill=col)
    draw.ellipse([570,H-218,590,H-190], fill=(165,130,80))

    # 窗帘
    draw.rectangle([150,30,200,H//2+75], fill=PC_RUST)
    draw.rectangle([W-200,30,W-150,H//2+75], fill=PC_RUST)
    draw.line([(145,30),(W-145,30)], fill=PC_GOLD, width=4)
    draw.ellipse([142,24,158,40], fill=PC_GOLD)
    draw.ellipse([W-158,24,W-142,40], fill=PC_GOLD)

    # 阳光效果（从窗帘间射入）
    sun_alpha = int(60 * ease_in_out(min(local_t/0.3,1.0)))
    sun_overlay = Image.new('RGBA', (W,H), (0,0,0,0))
    sd = ImageDraw.Draw(sun_overlay)
    for ray in range(3):
        rx = 200 + ray*5
        ray_pts = [(rx,30),(rx+200,H//2+60),(rx+240,H//2+60),(rx+40,30)]
        sd.polygon(ray_pts, fill=(255,240,180,sun_alpha-ray*15))
    img.paste(sun_overlay,(0,0),sun_overlay)
    draw = ImageDraw.Draw(img)

    # 结尾文字（淡入）
    end_t = ease_in_out(max(0,(local_t-0.5)/0.5))
    if end_t > 0.05:
        font_big = try_font(48)
        font_sm  = try_font(24)
        font_en  = try_font_en(18)
        # 文字板
        panel = Image.new('RGBA', (500,200), (0,0,0,0))
        pd2 = ImageDraw.Draw(panel)
        pd2.rectangle([0,0,500,200], fill=(245,235,220,int(220*end_t)))
        pd2.line([(20,10),(480,10)], fill=(*PC_GOLD, int(255*end_t)), width=2)
        pd2.line([(20,190),(480,190)], fill=(*PC_GOLD, int(255*end_t)), width=2)
        img.paste(panel, (W//2-250, H-280), panel)
        draw = ImageDraw.Draw(img)
        draw.text((W//2, H-230), "中古现代风 · 软装完成", font=font_big, fill=PC_DARK, anchor="mm")
        draw.text((W//2, H-175), "89㎡ 3室2厅 | 设计风格：Mid-Century Modern", font=font_sm, fill=PC_TEAL, anchor="mm")
        draw.text((W//2, H-145), "温暖 · 自然 · 复古 · 精致", font=font_en, fill=PC_GOLD, anchor="mm")

    draw_progress_bar(draw, frame, "软装完成 [OK]", tuple(c//2 for c in PC_OLIVE))

    return img

# ─────────────────────────────────────────────
# 主渲染循环
# ─────────────────────────────────────────────

def render_frame(frame):
    t_total = frame / TOTAL_FRAMES

    if frame < 150:          # 0-5s
        local_t = frame / 149.0
        img = render_scene_intro(frame, local_t)
    elif frame < 300:        # 5-10s
        local_t = (frame-150) / 149.0
        img = render_scene_rough(frame, local_t)
    elif frame < 480:        # 10-16s
        local_t = (frame-300) / 179.0
        img = render_scene_hardwork(frame, local_t)
    elif frame < 660:        # 16-22s
        local_t = (frame-480) / 179.0
        img = render_scene_furniture(frame, local_t)
    elif frame < 810:        # 22-27s
        local_t = (frame-660) / 149.0
        img = render_scene_softdeco(frame, local_t)
    else:                    # 27-30s
        local_t = (frame-810) / 89.0
        img = render_scene_final(frame, local_t)

    # 场景间过渡（淡化）
    transition_frames = 15
    scene_boundaries = [150, 300, 480, 660, 810]
    for boundary in scene_boundaries:
        dist = abs(frame - boundary)
        if dist < transition_frames:
            fade_factor = dist / transition_frames
            fade_overlay = Image.new('RGB', (W,H), PC_BG)
            img = Image.blend(fade_overlay, img, fade_factor)

    # 全局暗角效果
    vignette = Image.new('RGBA', (W,H), (0,0,0,0))
    vd = ImageDraw.Draw(vignette)
    for r in range(50, 0, -1):
        alpha_v = int(80 * (1 - r/50)**2)
        margin_v = r * 7
        if margin_v < W//2 and margin_v < H//2:
            vd.rectangle([margin_v, margin_v, W-margin_v, H-margin_v],
                         outline=(0,0,0,alpha_v), width=1)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, vignette)
    img = img.convert('RGB')

    return img

def main():
    print("[START] 开始生成中古风装修视频...")
    print(f"   分辨率: {W}x{H}  帧率: {FPS}fps  总帧数: {TOTAL_FRAMES}")
    print(f"   输出: {OUT_PATH}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(OUT_PATH, fourcc, FPS, (W, H))

    if not writer.isOpened():
        print("[ERROR] VideoWriter 无法打开，请检查 OpenCV 安装")
        return

    for f in range(TOTAL_FRAMES):
        if f % 30 == 0:
            pct = f * 100 // TOTAL_FRAMES
            bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
            print(f"\r   [{bar}] {pct:3d}%  frame {f:4d}/{TOTAL_FRAMES}  ({f//FPS}s)", end="", flush=True)

        frame_img = render_frame(f)
        frame_np = np.array(frame_img)
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

    writer.release()
    print(f"\n[DONE] 视频生成完成！")
    print(f"   文件路径: {OUT_PATH}")

    # 检查文件大小
    if os.path.exists(OUT_PATH):
        size_mb = os.path.getsize(OUT_PATH) / (1024*1024)
        print(f"   文件大小: {size_mb:.1f} MB")

if __name__ == "__main__":
    main()
