#作者：欧阳丞珈 星耀高中2028届理8班 | AI assisted | 有多重结局 请不要使用编译器运行 用Windows原生终端以获得最好体验 | Elden Ring 原游戏改编

import time
import sys
import random



from colorama import init, Fore, Style

init(autoreset=True)


# ============================================================
# print
# ============================================================
SKIP_PAUSE = False
TEXT_SPEED = 1.0     # 全局速度倍率：1.0=默认，0.5=快，2.0=慢
SKIP_ALL   = False   # True 时所有文字瞬间显示

def slow(text, speed=0.035):
    if SKIP_ALL:
        print(text)
        return
    actual = speed * TEXT_SPEED
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(actual)
    print()

def sl(text, speed=0.035):
    slow(text, speed)

def pause(sec=0.8):
    if SKIP_PAUSE:
        print("skiped")
    else:
        time.sleep(sec)

def bar():
    sl("─" * 56, 0.003)

def double_bar():
    sl("═" * 56, 0.003)

# ============================================================
# 颜色
# ============================================================
C_RESET  = Style.RESET_ALL
C_DIM    = Style.DIM
C_GRAY   = Fore.LIGHTBLACK_EX
C_BLUE   = Fore.LIGHTBLUE_EX
C_YELLOW = Fore.LIGHTYELLOW_EX
C_RED    = Fore.LIGHTRED_EX
C_PURPLE = Fore.LIGHTMAGENTA_EX
C_GREEN  = Fore.LIGHTGREEN_EX
C_CYAN   = Fore.LIGHTCYAN_EX

C_DARK_GREEN = Fore.GREEN
# 战技 type → 颜色
TYPE_COLORS = {
    "damage":     C_GRAY,
    "guard":      C_BLUE,
    "fixed":      C_YELLOW,
    "fixed_only": C_YELLOW,
    "burn":       C_RED,
    "reduce_max": C_PURPLE,
    "heal":       C_GREEN,
}
ENDING_COLORS = {
    "癫火之王":                     C_YELLOW,
    "放置「完美律法的修复卢恩」":   C_YELLOW,   # 黄金律法
    "放置「死王子的修复卢恩」":     C_BLUE,     # 死亡/深海
    "放置「忌讳诅咒的修复卢恩」":   C_PURPLE,   # 食粪者诅咒
    "召唤菈妮":                     C_CYAN,     # 群星/月光
    "不放置 大卢恩":                C_GRAY,     # 衰颓/腐朽
}
# ============================================================
# battle
# ============================================================
player_max_hp = 100
player_hp     = 100
player_max_fp = 40
player_fp     = 30
player_atk    = 12
flask         = 3
max_flask     = 3
mimic_tear    = False    # 仿身泪滴，可在死后复活一次
not_being_counter = False #百智爵士线 重击不再失败
every_battle_mimic_tear = True #每回合的mimictear

# ============================================================
# storyline value
# ============================================================
order = 0
stars = 0
frenzy = 0
ranni_route = False
married_ranni = False
gold_needle_used = False
melina_alive = True
have_perfect_rune = False   # 律法时代
have_death_rune   = False   # 潜藏者当道
have_dung_rune    = False   # 绝望赐福
greck_no_heal     = False   # 是否已获得葛瑞克秘密
radahn_bonus = False  # 拉塔恩战skip

##
#Tips
##
dead_count = 0


# ============================================================
# skills
# ============================================================
# 每把战技: {name, cost, type, ...}
#   type "damage"       : 伤害 = atk + rand(lo, hi)
#   type "guard"        : 伤害 = atk + rand(lo, hi)，下回合受伤减免 20%
#   type "fixed"        : 固定伤害，敌人易伤 2 回合
#   type "burn"         : 伤害 = atk + rand(lo, hi)，敌人燃烧 3 回合
#   type "reduce_max"   : 敌人最大 HP -（本战内）
#   type "heal"         : 回自身 HP，清除所有负面状态
skills = [
    {"name": "剑技", "cost": 10, "type": "damage", "lo": 8, "hi": 15,
     "desc": "基础斩击。伤害随攻击力提升。"},
]


# ============================================================
# battle status
# ============================================================
burn_turns       = 0    # 敌人燃烧剩余回合
enemy_vulnerable = 0    # 敌人易伤剩余回合
player_guard     = 0    # 玩家下次受伤减免（接肢斩专用）


# ============================================================
# Revive
# ============================================================
def revive_at_grace():
    """褪色者死亡后，在赐福处复活。HP/FP/圣杯瓶恢复。"""
    global player_hp, player_fp, flask, player_max_hp
    global every_battle_mimic_tear
    global dead_count

    dead_count += 1

    print()
    sl("  你倒下了。视野变黑。", 0.3)
    pause(0.8)
    sl("  黑暗中，一簇金色的光芒浮现。", 0.05)
    sl("  ——那是赐福。那是双指的指引。", 0.05)
    pause(0.6)
    sl("  你睁开眼。又回到了赐福处。", 0.05)
    sl("  褪色者不会真正死去。但死亡依然……痛苦。", 0.2)
    pause(0.5)
    player_hp = player_max_hp
    player_fp = player_max_fp
    every_battle_mimic_tear = True
    fill_flask()
    sl(f"  ▶ HP/FP 已恢复，圣杯瓶 x{flask}。", 0.04)
    if dead_count % 3 == 0:
        sl("Tips:敌人的攻击似乎有一定规律，在特定时候使用防御可能有奇效。",0.04)
    print()


# ============================================================
# fill_flask and damage
# ============================================================
def fill_flask():
    global flask
    flask = max_flask

def deal_damage(dmg):
    """对敌人造成伤害，自动应用易伤加成。返回实际伤害值。"""
    global enemy_hp, enemy_vulnerable
    if enemy_vulnerable > 0:
        dmg = int(dmg * 1.3)
    enemy_hp -= dmg
    return dmg
# ============================================================
# 战斗全局状态
# ============================================================
enemy_name      = ""
enemy_hp        = 0
enemy_max_hp    = 0
enemy_atk       = 0
enemy_phase2    = False     # 是否已进入第二阶段（打印过提示）
defend_next     = False     # 玩家本回合是否防御
original_max_hp = 0         # 战斗前的 player_max_hp（curse 恢复用）
original_atk = 0
dummy_mode = False
# ============================================================
# player_round
# ============================================================
def player_round():
    """
    执行一次玩家回合。
    返回 True  = 玩家成功行动，可进入敌人回合
    返回 False = 输入无效 / 资源不足 / 从战技菜单返回（外层 continue 重来）
    """
    global enemy_hp, defend_next, player_hp, player_fp, flask
    global burn_turns, enemy_vulnerable, player_guard
    global enemy_max_hp

    print()
    print(f"  ┌─ 你  {C_RED}HP {player_hp}/{player_max_hp}{C_RESET}  "
          f"{C_CYAN}FP {player_fp}/{player_max_fp}{C_RESET}  "
          f"{C_YELLOW}圣杯瓶 x{flask}/{max_flask}{C_RESET}")
    print(f"  └─ {C_RED}{enemy_name}  HP {enemy_hp}/{enemy_max_hp}{C_RESET}")
    print()
    if not not_being_counter:
        print("  [1] 轻击        [2] 重击(有概率失败)")
    else:
        print("  [1] 轻击        [2] 重击(必中)")
    print("  [3] 战技        [4] 防御(伤害减免)")
    print("  [5] 圣杯瓶")
    choice = input("> ").strip()
    print()

    if choice == "1":
        dmg = random.randint(player_atk - 3, player_atk + 3)
        dmg = deal_damage(dmg)
        sl(f"  你挥剑轻击，造成 {dmg} 点伤害。", 0.03)

    elif choice == "2":
        if random.random() < 0.25 and not not_being_counter:
            sl("  你起手过慢——敌人抓住了机会！", 0.03)
            counter = int(random.randint(enemy_atk - 3, enemy_atk + 3) * 1.5)
            player_hp -= counter
            sl(f"  {enemy_name} 反击，造成 {counter} 点伤害。", 0.03)
        else:
            dmg = player_atk + 9
            dmg = deal_damage(dmg)
            sl(f"  你挥出重击，造成 {dmg} 点伤害。", 0.03)

    elif choice == "3":
        # ---------- 战技二级菜单 ----------
        if not skills:
            sl("  你还没有掌握任何战技。", 0.03)
            return False

        print("  选择战技：")
        for i, sk in enumerate(skills, 1):
            color = TYPE_COLORS.get(sk["type"], "")
            print(f"    [{i}] {color}{sk['name']}{C_RESET}  {C_CYAN}(FP {sk['cost']}){C_RESET}")
            print(f"        {C_DIM}{sk['desc']}{C_RESET}")
        print("    [0] 返回")
        sub = input("> ").strip()

        if sub == "0":
            return False

        if not sub.isdigit() or not (1 <= int(sub) <= len(skills)):
            sl("  无效输入。", 0.03)
            return False

        sk = skills[int(sub) - 1]

        if player_fp < sk["cost"]:
            sl(f"  FP 不足（需要 {sk['cost']} FP）。", 0.03)
            return False

        player_fp -= sk["cost"]
        s_type = sk["type"]

        if s_type == "damage":
            dmg = random.randint(player_atk + sk["lo"], player_atk + sk["hi"])
            dmg = deal_damage(dmg)
            sl(f"  你燃起战技——{sk['name']}，斩出 {dmg} 点伤害！", 0.04)

        elif s_type == "guard":
            dmg = random.randint(player_atk + sk["lo"], player_atk + sk["hi"])
            dmg = deal_damage(dmg)
            player_guard = 1
            sl(f"  你燃起战技——{sk['name']}，斩出 {dmg} 点伤害！", 0.04)
            sl("  接肢在你周身织成护盾（下次受伤减免）。", 0.03)

        elif s_type == "fixed":
            dmg = sk["lo"]   # 用 lo 字段存固定值
            dmg = deal_damage(dmg)
            enemy_vulnerable = 2
            sl(f"  你拉开碎星之弓——{sk['name']}，贯穿 {dmg} 点伤害！", 0.04)
            sl("  碎星之力撕开了敌人的防御（易伤 2 回合）。", 0.03)

        elif s_type == "burn":
            dmg = random.randint(player_atk + sk["lo"], player_atk + sk["hi"])
            dmg = deal_damage(dmg)
            burn_turns = 3
            sl(f"  你燃起战技——{sk['name']}，斩出 {dmg} 点伤害！", 0.04)
            sl("  灰灭火焰附着在敌人身上（燃烧 3 回合）。", 0.03)


        elif s_type == "reduce_max":

            enemy_max_hp -= sk["lo"]
            if enemy_hp > enemy_max_hp:
                enemy_hp = enemy_max_hp
            sl(f"  你唤出命定之死——{sk['name']}。", 0.04)
            sl(f"  敌人的生命上限被削去了 {sk['lo']}。", 0.03)
            sl("  你仍然可以行动。",0.07)
            return False
        elif s_type == "heal":
            player_hp = min(player_max_hp, player_hp + sk['lo'])
            # 清除负面状态（这里目前只有 player_guard 反向效果，保留扩展位）
            sl(f"  你诵出黄金祷言——{sk['name']}。", 0.04)
            sl(f"  金色的光芒笼罩全身，恢复 {sk['lo']} HP。", 0.03)
            sl("  你仍然可以行动。", 0.07)
            return False
        elif s_type == "fixed_only":
            dmg = sk["lo"]
            dmg = deal_damage(dmg)
            sl(f"  你祭出——{sk['name']}，贯穿 {dmg} 点伤害！", 0.04)
    elif choice == "4":
        defend_next = True
        sl("  你举盾防御，稳住重心。", 0.03)


    elif choice == "5":

        # flask second menu

        if flask > 0:
            print(f"  选择圣杯瓶:(当前剩余 {flask} / {max_flask})")
            print("  [0]退出")
            print("  [1]红露滴圣杯瓶(恢复HP)        [2]蓝露滴圣杯瓶(恢复FP)")
            flask_choice = input(" >").strip()
            if flask_choice == "0":
                return False
            elif flask_choice == "1":
                player_hp = min(player_max_hp, int(player_hp + (player_max_hp * 0.4)))
                flask -= 1
                sl(f"  你饮下圣杯瓶，恢复 {int(player_max_hp*0.4)} HP。", 0.03)
                return False
            elif flask_choice == "2":
                flask -= 1
                player_fp = min(player_max_fp, player_fp + 30)
                sl("  你饮下圣杯瓶，恢复 30 FP。", 0.03)
                return False
            else:
                sl("  无效输入。", 0.03)
                return False
        else:
            sl("  圣杯瓶已空。", 0.03)
            return False

    return True


# ============================================================
# enemy_round
# ============================================================
def enemy_round(special):
    """
    执行一次敌人回合。
    special 返回值:
      "telegraph"        : 第 n-1 回合预告，只打印，不攻击
      "lethal_hit"       : 第 n 回合发动，检查 defend_next
      "radahn_lethal_hit": 拉塔恩版本
      其他              : 普通 special 效果
    """
    global enemy_hp, player_hp, player_atk, player_max_hp, defend_next
    global burn_turns, enemy_vulnerable, player_guard
    global enemy_phase2

    print()
    if dummy_mode:
        print("  （训练假人纹丝不动。）")
        print()
        pause(0.2)
        return
    # ---- 燃烧结算 ----
    if burn_turns > 0:
        enemy_hp -= 20
        burn_turns -= 1
        sl(f"  灰灭火焰在 {enemy_name} 身上灼烧——20 点伤害。", 0.03)
        if enemy_hp <= 0:
            return

    # ---- 二阶段判定 ----
    if not enemy_phase2 and enemy_hp < enemy_max_hp * 0.5:
        enemy_phase2 = True
        sl(f"  ⚠  {enemy_name} 的气息变了——攻击变得更加凶狠！", 0.05)

    # 二阶段 ATK +4
    current_atk = enemy_atk + (4 if enemy_phase2 else 0)

    # 基础伤害
    dmg = random.randint(current_atk - 3, current_atk + 4)
    # 易伤（敌人受伤，不是伤害加成）——这里是敌人攻击玩家，不受影响

    if special:
        triggered, desc, effect = special(enemy_hp, enemy_max_hp)

        if triggered:

            # ============ 预告回合 ============
            if effect == "telegraph":
                sl(f"  ⚠  {desc}", 0.05)
                pause(0.4)
                #sl("  ——下一击，将是致命的。", 0.05)
                defend_next = False
                return   # 不打玩家

            # ============ 发动致命一击 ============
            elif effect == "lethal_hit":
                sl(f"  {desc}", 0.05)
                pause(0.3)
                base = player_max_hp
                if defend_next:
                    dmg = int(base * 0.25)
                    sl("  你架住了这一击——巨大的冲击让你后退数步，但你还站着。", 0.04)
                    defend_next = False
                else:
                    dmg = base
                    sl("  你没有准备——这一击直接贯穿了你的防御。", 0.04)

            elif effect == "radahn_lethal_hit":
                sl(f"  {desc}", 0.05)
                pause(0.3)
                base = int(player_max_hp / 1.7)
                if defend_next:
                    dmg = int(base * 0.5)
                    sl("  你架住了引力漩涡——身体被扯得生疼，但没有被吸进去。", 0.04)
                    defend_next = False
                else:
                    dmg = base
                    sl("  你被引力漩涡扯向拉塔恩——", 0.04)

            # ============ 普通 special ============
            else:
                sl(f"  {desc}", 0.04)
                pause(0.3)

                if effect == "damage_boost":
                    dmg = random.randint(current_atk + 5, current_atk + 12)
                elif effect == "heal":
                    heal = random.randint(15, 25)
                    enemy_hp = min(enemy_max_hp, enemy_hp + heal)
                    sl(f"  {enemy_name} 恢复了 {heal} 点生命。", 0.03)
                    return
                elif effect == "multi":
                    dmg = random.randint(current_atk - 2, current_atk + 2) * 2
                elif effect == "curse":
                    loss = round(player_max_hp * 0.2)
                    actual_cost = player_max_hp - max(50, player_max_hp - loss)
                    player_max_hp = max(50, player_max_hp - loss)
                    if player_hp > player_max_hp:
                        player_hp = player_max_hp
                    sl(f"  命定之死侵蚀了你——生命上限 -{actual_cost}。", 0.03)
                elif effect == "weaken":
                    player_atk = max(6, player_atk - 2)
                    sl("  星辰的重压碾过你的身体——攻击力 -2。", 0.03)
                elif effect == "skip":
                    sl("  你看穿了一切……（获得额外回合）", 0.05)
                    return

    # ---- 防御结算 ----
    if defend_next:
        dmg = int(dmg / 5)
        defend_next = False

    # ---- 接肢斩护盾减免 ----
    if player_guard > 0:
        dmg = int(dmg * 0.8)
        sl("「接肢斩」生效 —— 伤害减免 20%")
        player_guard = 0

    # ---- 易伤回合数递减 ----
    if enemy_vulnerable > 0:
        enemy_vulnerable -= 1

    dmg = int(dmg)
    player_hp -= dmg
    sl(f"  {enemy_name} 攻击，造成 {dmg} 点伤害。", 0.03)
    print()
    pause(0.3)


# ============================================================
# battle
# ============================================================
def battle(name, hp, atk, intro_lines, win_lines, special=None):
    """
    完整的一场战斗。
    返回 True=胜利 / False=死亡（外层 while not win 循环重打）
    """
    global enemy_name, enemy_hp, enemy_max_hp, enemy_atk, enemy_phase2
    global defend_next, original_max_hp, original_atk
    global player_hp, player_fp, player_max_hp, player_atk, mimic_tear
    global burn_turns, enemy_vulnerable, player_guard
    global every_battle_mimic_tear
    enemy_name      = name
    enemy_hp        = hp
    enemy_max_hp    = hp
    enemy_atk       = atk
    enemy_phase2    = False
    defend_next     = False
    original_max_hp = player_max_hp
    original_atk    = player_atk       # ← 记录原始攻击力（weaken 恢复用）
    burn_turns      = 0
    enemy_vulnerable = 0
    player_guard    = 0
    every_battle_mimic_tear = True

    for line in intro_lines:
        sl(line, 0.05)
    print()
    pause(0.6)

    # 外层 while True：仿身泪滴复活时回到这里继续战斗
    while True:
        # 战斗主循环
        while player_hp > 0 and enemy_hp > 0:
            if not player_round():
                continue
            if enemy_hp <= 0:
                break
            enemy_round(special)

        print()
        pause(0.5)

        # 恢复被 curse 削减的 max_hp 和 weaken 削弱的 atk
        player_max_hp = original_max_hp
        player_atk    = original_atk
        if player_hp > player_max_hp:
            player_hp = player_max_hp

        # 清空战斗状态
        burn_turns = 0
        enemy_vulnerable = 0
        player_guard = 0

        if player_hp > 0:
            # 胜利
            for line in win_lines:
                sl(line, 0.05)
                pause(0.4)
            fill_flask()
            return True

        # 玩家死亡，检查仿身泪滴
        if mimic_tear and every_battle_mimic_tear:
            sl("  银色的泪滴从召魂铃中涌出，替你承受了致命一击。", 0.04)
            player_hp = player_max_hp // 2
            every_battle_mimic_tear = False
            continue    # 继续这场战斗（敌人 HP 不清空）

        # 真死亡
        revive_at_grace()
        return False


# ============================================================
#   test
# ============================================================


# ============================================================
# 训练假人
# ============================================================
def show_skill_damage():
    """速查：列出所有战技在当前攻击力下的伤害范围"""
    print()
    print("=" * 56)
    print("  战技伤害速查")
    print("=" * 56)
    print(f"  当前攻击力：{player_atk}")
    print(f"  当前 FP：{player_fp}/{player_max_fp}")
    print()

    for sk in skills:
        t = sk["type"]
        lo, hi = sk["lo"], sk["hi"]

        if t == "damage":
            dmg_text = f"{player_atk + lo} ~ {player_atk + hi}"
        elif t == "guard":
            dmg_text = f"{player_atk + lo} ~ {player_atk + hi}  (附带护盾)"
        elif t == "burn":
            dmg_text = f"{player_atk + lo} ~ {player_atk + hi}  + 燃烧 3×20"
        elif t == "fixed":
            dmg_text = f"固定 {lo}"
        elif t == "fixed_only":
            dmg_text = f"固定 {lo}"
        elif t == "reduce_max":
            dmg_text = f"削减敌人上限 {lo}"
        elif t == "heal":
            dmg_text = f"恢复 {lo} HP"
        else:
            dmg_text = "?"

        print(f"  {sk['name']:<8} FP {sk['cost']:<3} → {dmg_text}")

    print()
    # 轻击 / 重击
    print(f"  轻击       —   → {player_atk - 3} ~ {player_atk + 3}")
    print(f"  重击       —   → 固定 {player_atk + 9}  (25% 概率失败)")
    print()
    print("=" * 56)


def train_dummy():
    """训练假人：无限血量，不反击，可自由测试所有攻击"""
    global dummy_mode, player_hp, player_fp

    print()
    print("=" * 56)
    print("  训练假人")
    print("=" * 56)
    print("  HP 99999，永不反击。")
    print("  可自由使用轻击 / 重击 / 所有战技 / 圣杯瓶。")
    print("  输入 'q' 无法退出——只能把假人打死（不现实）或用 Ctrl+C。")
    print("=" * 56)
    print()

    player_hp = player_max_hp
    player_fp = player_max_fp
    dummy_mode = True

    try:
        battle(
            "训练假人", 99999, 0,
            intro_lines=[
                "一具木桩立在空地中央。",
                "桩身上缠着几圈铁链，顶部挂着一块小木牌：",
                "「试招用。打不坏。」"
            ],
            win_lines=[
                "（假人……居然真的被你打碎了。）",
                "（这不太应该发生。）"
            ],
        )
    finally:
        dummy_mode = False
        print()
        print("  （训练结束。）")


# ============================================================
# Game START   !!!!!
# ============================================================

print(f"{C_DARK_GREEN}{'═' * 56}{C_RESET}")
print()
print(f"{' ' * 19}{C_YELLOW}《艾尔登法环》{C_RESET}")
print()
print(f"{C_DARK_GREEN}{'═' * 56}{C_RESET}")
print()
pause(0.8)


print("请选择文字速度：")
print("  [1] 快    [2] 中    [3] 慢    [4] 关闭打字机效果")
_spd = input("> ").strip()
while _spd not in ("1", "2", "3", "4","testbot","skip"):
    print("无效输入，请重新选择。")
    _spd = input("> ").strip()
if _spd == "1":
    TEXT_SPEED = 0.5
elif _spd == "2":
    TEXT_SPEED = 1.0
elif _spd == "3":
    TEXT_SPEED = 2.0
elif _spd == "4":
    SKIP_ALL = True
elif _spd == "testbot":
    SKIP_PAUSE = True
    SKIP_ALL = True
    show_skill_damage()
    train_dummy()
elif _spd == "skip":
    SKIP_PAUSE = True
    SKIP_ALL = True
print()
pause(0.5)


# ============================================================
# 序幕
# ============================================================
sl("黑幕。远处传来一声低沉的钟鸣，像从地底极深处升起，震得空气微微发颤。", 0.05)
pause(0.6)
sl("迷雾中，一片荒芜的大地在黑暗中缓缓浮现。", 0.05)
sl("枯死的树木以扭曲的姿态矗立，断裂的兵器半埋在泥土里。", 0.05)
sl("远处，一棵巨大到不可想象的金色树木矗立在地平线上，", 0.05)
sl("它的光芒穿透云层，却照不亮脚下的土地。", 0.05)
print()
pause(0.8)

sl("苍老、疲惫、仿佛念诵了千年的声音在黑暗中响起：", 0.05)
print()
pause(0.5)
sl("「……落叶捎来讯息：」", 0.06)
pause(0.5)
sl("停顿。风声。像有什么东西在雾中缓慢移动。", 0.05)
print()
pause(0.4)
sl("「在雾的彼端，我们的故乡‘交界地’，", 0.06)
sl("  那伟大的艾尔登法环已经破碎──」", 0.06)
print()
pause(1.0)

sl("一片荒芜的战场掠过黑暗。", 0.05)
sl("破碎的铠甲、折断的旗帜、半埋在泥土中的巨大兵器。", 0.05)
sl("有些兵器比人还高，有些铠甲中还有枯骨。没有人来收殓他们。", 0.05)
print()
pause(0.8)

sl("「‘永恒女王’玛莉卡销声匿迹，", 0.06)
sl("  在黑刀阴谋之夜，‘黄金’葛德文最先失去性命。」", 0.06)
print()
pause(0.8)

sl("一座被月光笼罩的城堡从黑暗中浮现。", 0.05)
sl("城墙上的旗帜被撕碎，城门大开。", 0.05)
sl("城堡深处，一名金发男子的身影倒在血泊中，", 0.05)
sl("手中紧握着一把断裂的短剑。", 0.05)
sl("他的身体已经开始被某种黑色的、像墨水一样的东西侵蚀。", 0.05)
print()
pause(0.8)

sl("「玛莉卡之子──诸位半神拿到艾尔登法环的碎片，", 0.06)
sl("  却因为那股力量堕入歧途、陷入疯狂、引发碎片战争……」", 0.06)
print()
pause(0.8)

sl("燃烧的城堡。咆哮的巨龙在天空中盘旋，翅膀遮住了月光。", 0.05)
sl("荒原上，两个巨大的身影对峙着。", 0.05)
sl("一个举着一对弯刀，刀身上缠绕着紫色的引力魔法。", 0.05)
sl("另一个被红色的光笼罩，空气中弥漫着腐败的气味。", 0.05)
print()
pause(0.8)

sl("「在那场无王存在的战争最后──", 0.06)
sl("  无上意志放逐了他们。」", 0.06)
print()
pause(1.0)

sl("一切暗下。片刻的寂静。", 0.05)
sl("然后，一簇金色的微光从黑暗中浮现，像一颗刚刚诞生的星辰。", 0.05)
print()
pause(0.6)

sl("「噢，所以啊，褪色者啊──", 0.06)
sl("  依旧无法永眠的死者啊。」", 0.06)
print()
pause(0.8)

sl("金色微光逐渐扩散，照亮了数张模糊的面孔。", 0.05)
print()
pause(0.4)
sl("一个蓄着胡须的魁梧战士，铠甲上布满战斗的裂痕，双眼中燃烧着不甘。", 0.05)
sl("一个戴着金色面具的静止身影，面朝黄金树的方向，一动不动。", 0.05)
sl("一个披着兜帽的女性，她的眼睛温柔而疲惫，像看过太多死亡。", 0.05)
sl("一个戴着绞刑架头盔的扭曲人影，身上缠绕着生锈的锁链。", 0.05)
sl("一个手持法杖的老者，眼睛被一层白色的膜覆盖，", 0.05)
sl("却在黑暗中准确地转向微光的方向。", 0.05)
print()
pause(0.8)

sl("「那许久以前我们失去的赐福，正在出声呼唤。", 0.06)
sl("  ‘蛮荒地王者’荷莱·露、", 0.06)
sl("  光耀金面具、", 0.06)
sl("  ‘死眠少女’菲雅、", 0.06)
sl("  受尽唾弃的食粪者、", 0.06)
sl("  ‘百智爵士’基甸·奥夫尼尔。」", 0.06)
print()
pause(0.8)

sl("面孔一一消散在黑暗中。", 0.05)
sl("只剩下那簇微光在缓缓旋转，像在等待什么。", 0.05)
print()
pause(0.6)

sl("「……那失去的赐福又再一次，", 0.06)
sl("  回到默默无名的褪色者身上。」", 0.06)
print()
pause(0.6)

sl("微光坠入黑暗，像一颗坠落的星辰。", 0.05)
print()
pause(0.6)

sl("「朝雾的彼端前进，抵达交界地，", 0.06)
sl("  觐见艾尔登法环──", 0.06)
sl("  当上艾尔登之王吧。」", 0.06)
print()
pause(1.2)

sl("钟声最后一次响起，余音在黑暗中回荡，渐渐消散。", 0.05)
pause(1.0)
print()

sl("狭小的石室。积水没踝，水面倒映着墙壁上早已熄灭的火把残影。", 0.05)
sl("空气里弥漫着潮湿的石腥与铁锈味。", 0.05)
sl("褪色者的尸体靠在墙边，铠甲上还残留着上一次死亡时的裂痕。", 0.05)
sl("石壁上刻满了无名者的名字，有些已经被青苔吞没。", 0.05)
pause(0.6)
sl("一簇金色的微光从石室顶端的裂缝中落下，缓缓飘向尸体。", 0.05)
print()
pause(0.6)

sl("那个声音再次响起，比之前更轻，像风穿过枯枝：", 0.05)
print()
pause(0.4)
sl("「战斗、死亡——这永无止尽的诅咒，", 0.06)
sl("  却是催生英雄与王者的唯一温床。", 0.06)
sl("  为了我们所有人……", 0.06)
sl("  展现艾尔登法环吧。」", 0.06)
print()
pause(0.8)

sl("褪色者睁开眼。第一口呼吸灌入肺中，像溺水者被拖上岸。", 0.05)
sl("石室墙壁上浮现出一行被苔藓半掩的刻字，笔画古老而扭曲：", 0.05)
print()
pause(0.4)
sl("「即使引导早已破碎，也请你当上艾尔登之王。」", 0.07)
print()
pause(0.8)

sl("褪色者撑着潮湿的石壁站起，铠甲上的水珠滴落，", 0.05)
sl("在积水中荡开一圈圈涟漪。", 0.05)
sl("石室尽头的门半开着，门外是深不见底的黑暗。", 0.05)
sl("远处，一声接一声的钟鸣仍在继续。那是‘双指’在等待。", 0.05)
print()
pause(0.6)
sl("褪色者踏出了第一步。", 0.08)
print()
input("按回车继续……")


# ============================================================
# 第一幕 · 宁姆格福
# ============================================================
print()
bar()
sl("【第一幕 · 宁姆格福】", 0.06)
bar()
print()

sl("褪色者穿过狭窄的石廊，脚下是湿滑的碎石与断裂的骸骨。", 0.05)
sl("石壁上刻满了无名者的名字，有些已经被青苔吞没。", 0.05)
pause(0.5)
sl("转过最后一个弯道，光线突然涌了进来。", 0.05)
print()
pause(0.5)

sl("——那是一整片天空。", 0.07)
print()
pause(0.6)

sl("宁姆格福的草原在晨雾中铺展开去，", 0.05)
sl("草叶上凝结的露水反射着微光，像撒了一地的碎银。", 0.05)
sl("远处，黄金树的光芒穿透云层，", 0.05)
sl("金色的枝干如同撑起天穹的巨柱，柔和的光晕洒在整片大地上。", 0.05)
print()
pause(0.8)

sl("草坡上，一座残破的石碑半埋在泥土里，上面模糊地刻着：", 0.05)
sl("「宁姆格福——第一片迎接褪色者的土地。」", 0.06)
print()
pause(0.6)

sl("微风拂过，草浪起伏，远处隐约传来羊群的铃铛声。", 0.05)
sl("但在这宁静之下，褪色者能感觉到大地深处有一种低沉的震颤——", 0.05)
sl("像是什么巨大的东西正在缓慢地转动，", 0.05)
sl("又像是某种根须在泥土中挣扎。", 0.05)
print()
pause(0.6)
sl("空气中有一种干燥的、金属般的味道。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第一幕 · 废弃营地岔路
# ============================================================
print()
sl("草坡下方有一座半塌的营地。", 0.05)
sl("篝火已经熄灭，帐篷布在风中起伏。", 0.05)
sl("一具穿着破甲的尸体倒在营火旁，手里还握着一把生锈的短剑。", 0.05)
print()
pause(0.5)
sl("[1] 搜刮营地。", 0.01)
sl("[2] 直接前进。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你翻开帐篷，在一只木箱中找到了一枚「黄金种子」。", 0.05)
    sl("金黄的种子上流转着微弱的赐福光芒。", 0.05)
    max_flask += 1
    pause(0.4)
    sl(f"▶ 圣杯瓶上限 +1（当前 x{max_flask}）。", 0.04)
    if random.random() < 0.5:
        sl("几只流浪的猎犬从帐篷后窜出，扑向你。", 0.05)
        pause(0.4)
        sl("你反应过来，挥剑击退了它们。",0.05)
        sl("所幸，你没有受伤。",0.05)
    else:
        sl("几只流浪的猎犬从帐篷后窜出，扑向你。", 0.05)
        pause(0.4)
        sl("你挥剑击退了它们，但手臂上多了一道伤口。", 0.05)
        dmg = random.randint(5, 12)
        player_hp -= dmg
        sl(f"▶ 你受了 {dmg} 点伤（HP {player_hp}/{player_max_hp}）。", 0.04)
else:
    sl("你径直走向草原深处。", 0.05)
    sl("风吹过废弃的营火，灰烬升腾起来，像一个未说出口的名字。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第一幕 · 关卡前方 · 梅琳娜
# ============================================================
print()
sl("褪色者沿着草坡向下，经过几处废弃的营火与半塌的帐篷。", 0.05)
sl("营火中还有余烬在闪烁，但周围不见人影。", 0.05)
sl("帐篷上绣着一个褪色的徽记——两棵树干交缠的图案，黄金树的旧徽。", 0.05)
print()
pause(0.6)

sl("前方，一座巨大的石门矗立在峡谷之间。风暴关卡。", 0.05)
sl("门两侧的石柱上攀满了枯死的藤蔓，", 0.05)
sl("藤蔓间垂挂着早已风干的旗帜碎片。", 0.05)
print()
pause(0.5)

sl("关卡前方的赐福处，金光从地面缓缓升起，像一簇不会熄灭的火焰。", 0.05)
sl("一名披着灰色斗篷的少女从雾中现身。", 0.05)
sl("她的斗篷边缘磨损严重，兜帽下露出一缕暗褐色的长发。", 0.05)
sl("她的左眼紧闭，右眼呈黯淡的金色，像是蒙了一层灰。", 0.05)
sl("她赤着双脚，脚踝上有一圈浅浅的、已经愈合的疤痕。", 0.05)
print()
pause(0.8)

sl("梅琳娜：「你好。穿越雾前来的人啊。」", 0.04)
pause(0.4)
sl("她的声音很轻，像怕惊扰了周围的空气。", 0.05)
pause(0.4)
sl("梅琳娜：「我的名字是梅琳娜……想要和你谈个条件。」", 0.04)
sl("她走到赐福旁，伸出手，在金色的光芒上方停留了片刻。", 0.05)
pause(0.4)
sl("梅琳娜：「你知道指头女巫吗？", 0.04)
sl("  她们是侍奉双指、帮助和引导褪色者的人。", 0.04)
sl("  ……但现在的你，没有女巫在身边。", 0.04)
sl("  我可以代替她们的职务。我能够将卢恩化作你的力量。」", 0.04)
pause(0.4)
sl("她抬起头，那只黯淡的金色眼睛直视着褪色者。", 0.05)
sl("梅琳娜：「只要你渴求艾尔登法环，这件事肯定对你有帮助。", 0.04)
sl("  ……所以，希望你能帮忙——带我到黄金树的树脚。」", 0.04)
print()
pause(0.5)
sl("[1] 「我接受。」", 0.01)
sl("[2] 「我拒绝。」", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("梅琳娜：「……这样就算谈成了。」", 0.04)
    pause(0.5)
    sl("她伸出手，轻轻碰触褪色者的手背。", 0.05)
    sl("一簇微小的金光在两人之间闪烁，像是两颗星辰短暂地交会。", 0.05)
    pause(0.5)
    sl("梅琳娜：「一下子就好，让我碰触你……", 0.04)
    sl("  来，告诉我吧——你的意志，你渴望的力量，你心中的准则。」", 0.04)
    pause(0.4)
    sl("她的手指微微颤抖了一下，但很快收回。", 0.05)
    sl("梅琳娜：「……这样就结束了。", 0.04)
    sl("  这簇小巧的金光，是黄金树的赐福。", 0.04)
    sl("  你应该看得见吧？赐福的指引——引导使命所在的光芒。」", 0.04)
    print()
    pause(0.5)
    sl("▶ 获得：灵马哨笛。梅琳娜成为你的同伴。", 0.04)
    print()
    pause(0.4)
    sl("梅琳娜：「需要长距离移动时，就使用那枚戒指吧。", 0.04)
    sl("  那能够呼唤名为托雷特的骏马灵魂。", 0.04)
    sl("  我……会在这里等你。」", 0.04)
    pause(0.5)
    sl("她坐回赐福旁，双手抱膝，斗篷裹紧身体。", 0.05)
    sl("她的目光望向远处黄金树的方向，", 0.05)
    sl("那只黯淡的金色眼睛里，映着遥远的光。", 0.05)
else:
    sl("梅琳娜：「……我明白了。心有疑念，我也不勉强。」", 0.04)
    pause(0.5)
    sl("她的身影消散在雾中，像从未出现过一样。", 0.05)
    sl("赐福旁只留下一枚小小的金色光点，在空气中缓缓旋转。", 0.05)
    print()
    pause(0.6)
    sl("褪色者站了很久。风从峡谷中吹出，带着远处某种巨大生物的低吼。", 0.05)
    pause(0.5)
    sl("最终，褪色者还是走回了赐福旁。", 0.05)
    print()
    pause(0.5)
    sl("梅琳娜（重新出现，语气平静）：「……这样就算谈成了。」", 0.04)
    sl("她伸出手，轻轻碰触褪色者的手背。", 0.05)
    sl("一簇微小的金光在两人之间闪烁。", 0.05)
    pause(0.4)
    sl("梅琳娜：「一下就好，让我碰触你……", 0.04)
    sl("  告诉我吧——你的意志，你渴望的力量，你心中的准则。」", 0.04)
    pause(0.4)
    sl("梅琳娜：「……这样就结束了。", 0.04)
    sl("  这簇小巧的金光，是黄金树的赐福。", 0.04)
    sl("  你应该看得见吧？赐福的指引。」", 0.04)
    print()
    pause(0.5)
    sl("▶ 获得：灵马哨笛。", 0.04)
    print()
    pause(0.4)
    sl("梅琳娜：「需要长距离移动时，就使用那枚戒指吧。", 0.04)
    sl("  那能够呼唤名为托雷特的骏马灵魂。」", 0.04)
    pause(0.5)
    sl("她坐回赐福旁，目光望向远处黄金树的方向。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第一幕 · 艾雷教堂 · 夜晚 · 蕾娜
# ============================================================
print()
bar()
sl("【艾雷教堂 · 夜晚】", 0.06)
bar()
print()

sl("夜幕降临。宁姆格福的星空极其清澈——", 0.05)
sl("褪色者意识到，这是千年来第一次，", 0.05)
sl("黄金树的光芒在夜晚被云层遮蔽。星辰显露出来。", 0.05)
print()
pause(0.6)

sl("艾雷教堂的废墟矗立在草原边缘。", 0.05)
sl("石墙倒塌了一半，但拱门依然完好。", 0.05)
sl("教堂内部，破碎的彩绘玻璃散落一地，在月光下闪烁着微弱的光芒。", 0.05)
print()
pause(0.6)

sl("一位戴着宽檐帽的魔女坐在教堂矮墙上。", 0.05)
sl("她的帽子压得很低，遮住了大半张脸，", 0.05)
sl("只能看见一截苍白的下巴和一缕雪白的长发。", 0.05)
sl("她的坐姿极其从容，像是已经在那里等了很久。", 0.05)
print()
pause(0.8)

sl("蕾娜：「……褪色者啊，来这里吧。", 0.04)
sl("  能不能过来聊个几句？」", 0.04)
pause(0.5)
sl("她抬起头。褪色者看到了一张年轻却带着不属于年轻之物的沉静的面孔。", 0.05)
sl("她的眼睛是深蓝色的，像冬夜的湖泊。", 0.05)
pause(0.4)
sl("蕾娜：「初次见面啊，褪色者。我是魔女蕾娜。", 0.04)
sl("  听说有褪色者骑着灵马，让我花了点时间去找……看来就是你啊。」", 0.04)
pause(0.4)
sl("她轻轻笑了一下。", 0.05)
sl("蕾娜：「那名为托雷特的灵马——你能召唤它，没错吧？", 0.04)
sl("  ……嗯，答得好。」", 0.04)
pause(0.5)
sl("她从斗篷中取出一枚小小的铃铛，递给褪色者。", 0.05)
sl("铃铛表面刻着古老的符文，在月光下泛着银蓝色的光。", 0.05)
pause(0.4)
sl("蕾娜：「有物品要转交给你。这是托雷特的前主人托给我的。", 0.04)
sl("  那物品叫作召魂铃。没有回归黄金树的骨灰，能从中召唤出灵魂。", 0.04)
sl("  而那灵魂会暂时认你为主人，重现生前战斗的模样。」", 0.04)
print()
pause(0.5)
sl("[1] 追问她的身份。", 0.01)
sl("[2] 收下物品，沉默离开。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("蕾娜：「……褪色者啊，打扰你了。", 0.04)
    sl("  我想不会再见面了，仔细品尝交界地的滋味吧。」", 0.04)
    pause(0.5)
    sl("她站起身，从矮墙上跃下。", 0.05)
    sl("她的动作极轻，落地时几乎没有声音。", 0.05)
    pause(0.4)
    sl("蕾娜：「……我很期待啊……」", 0.04)
    pause(0.4)
    sl("她走向教堂的拱门，身影在月光中拉长。", 0.05)
    sl("蕾娜：「你们褪色者会服从双指到什么时候？」", 0.04)
    pause(0.5)
    sl("她的声音中带着一种冰冷的东西。", 0.05)
    sl("不是敌意，而是一种比敌意更深的……厌倦。", 0.06)
    sl("像是看过了太多重复的结局，连愤怒都消磨殆尽。", 0.05)
    pause(0.4)
    sl("她消失在了夜色中。", 0.05)
else:
    sl("蕾娜：「……哎，照你的意思使用吧。」", 0.04)
    pause(0.5)
    sl("她将铃铛放在矮墙上，起身离开。", 0.05)
    sl("她的身影融入教堂外的黑暗中，像一滴墨落入深水。", 0.05)
print()
pause(0.5)
sl("褪色者获得「召魂铃」与「离群野狼的骨灰」。", 0.04)
print()
pause(0.6)
sl("旁白（褪色者内心）：", 0.05)
sl("「那魔女……她的眼睛。", 0.05)
sl("  像是看过太多东西之后，就再也无法被打动了。」", 0.05)
print()
pause(0.8)
sl("那晚，褪色者在赐福旁入睡。", 0.05)
sl("梦中，有一颗蓝色的星辰从夜空中坠落，", 0.05)
sl("落在了一片从未见过的土地上。", 0.05)
sl("那里有永不消融的冰雪，和一座被月光笼罩的高塔。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 史东薇尔城
# ============================================================
print()
bar()
sl("【第二幕 · 史东薇尔城】", 0.06)
bar()
print()

sl("史东薇尔城矗立在宁姆格福东部的悬崖之上。", 0.05)
sl("城墙由巨大的灰色石块砌成，石缝中长满了暗绿色的苔藓与带刺的藤蔓。", 0.05)
sl("整座城堡像一只趴伏在崖壁上的巨兽，", 0.05)
sl("周身插满了断裂的箭矢与破碎的旗帜。", 0.05)
print()
pause(0.7)

sl("城内，风穿过坍塌的走廊，发出低沉的呜咽。", 0.05)
sl("地板上散落着无数尸骸——有士兵，有贵族，", 0.05)
sl("还有某种长着翅膀的畸形生物。", 0.05)
sl("空气中弥漫着腐臭与铁锈混合的气味。", 0.05)
print()
pause(0.6)

sl("褪色者一路向上，穿过接肢贵族盘踞的大厅、", 0.05)
sl("鹰身女妖筑巢的塔楼、以及被巨大手掌雕像守卫的城墙。", 0.05)
print()
pause(0.6)

# ---- 史东薇尔城岔路 ----
sl("穿过接肢贵族的大厅后，前方分出两条路。", 0.05)
sl("左侧是一段向上的螺旋楼梯，右侧是一扇半开的铁门。", 0.05)
sl("楼梯的扶手上挂着几卷被血浸透的绷带。", 0.05)
sl("铁门后传来金属碰撞的回声，像是有人在里面翻找什么。", 0.05)
print()
pause(0.5)
sl("[1] 上螺旋楼梯。", 0.01)
sl("[2] 推开铁门。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("楼梯顶端是一间藏书室。", 0.05)
    sl("书架已经大半倒塌，发霉的羊皮纸散落一地。", 0.05)
    sl("在一张被虫蛀的木桌上，你找到了一本保存尚好的笔记。", 0.05)
    pause(0.5)
    sl("翻开它——是关于「接肢」的解剖研究。", 0.05)
    sl("「葛瑞克的接肢并非单纯的嫁接，而是通过某种古老的黄金律法仪轨，", 0.05)
    sl("  将他人的生命力转为己用。若切断其核心接肢，他将无法再生。」", 0.05)
    print()
    pause(0.5)
    greck_no_heal = True
    sl("▶ 获得「葛瑞克的秘密」——本战中葛瑞克不会再使用濒死再生。", 0.04)
else:
    sl("铁门后是一间兵器库。", 0.05)
    sl("货架上还剩下几件尚未锈透的武器。", 0.05)
    sl("你在一只木箱中找到了一瓶尚未开封的圣杯瓶。", 0.05)
    max_flask += 1
    pause(0.4)
    sl(f"▶ 圣杯瓶上限 +1（当前 x{max_flask}）。", 0.04)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 接肢葛瑞克战
# ============================================================
def greck_special(hp, max_hp):
    """
    葛瑞克特殊机制：
      血量低于 50% → telegraph（n-1 回合预告）
      下一回合    → lethal_hit（满血伤害，玩家需防御）
      血量低于 30% → 再生（若已获秘密则改为"skip"）
    """
    # 初始化状态
    if not hasattr(greck_special, "turn"):
        greck_special.turn = 0

    greck_special.turn += 1
    if not hasattr(greck_special, "state"):
        greck_special.state = "idle"   # idle / telegraphing / done

    # ---- n 回合：释放 lethal ----
    if greck_special.state == "telegraphing":
        greck_special.state = "done"
        return True, "葛瑞克发出那记致命的一击——所有接肢同时砸下！", "lethal_hit"

    # ---- n-1 回合：预告 ----
    if hp < max_hp * 0.5 and greck_special.state == "idle":
        greck_special.state = "telegraphing"
        return True, "葛瑞克举起所有接肢，鲜血在断臂处沸腾——", "telegraph"

    # ---- 常规：濒死再生 ----
    if hp < max_hp * 0.3 and greck_special.turn % 3 == 0:
        if not greck_no_heal:
            return True, "葛瑞克用接肢护住要害，伤口蠕动、愈合……", "heal"
        else:
            return True, "葛瑞克试图再生，但核心接肢已被你切断—— 「葛瑞克的秘密」生效。 " , "skip"

    return False, "", ""


print()
sl("最终，在城堡最高处的残破王座前——", 0.05)
sl("「接肢」葛瑞克从王座上站起。", 0.06)
print()
pause(0.5)

sl("他的身体巨大而畸形，无数只手臂从他的躯干中伸出——", 0.05)
sl("有士兵的、有贵族的、有野兽的。", 0.05)
sl("每一只手臂都在抽搐，像是各自拥有独立的意志。", 0.05)
sl("他的头上戴着一顶歪斜的王冠，那张肿胀的脸上挂着一个扭曲的笑。", 0.05)
print()
pause(0.6)

win = False
while not win:
    # 重打时重置葛瑞克状态
    if hasattr(greck_special, "state"):
        del greck_special.state

    win = battle(
        "接肢 葛瑞克", 170, 15,
        intro_lines=[
            "葛瑞克从王座上站起，接肢在躯干上蠕动。",
            "「我……是葛瑞克！黄金一族的末裔！」",
            "「褪色者……你休想……通过这里！」"
        ],
        win_lines=[
            "葛瑞克跪倒在地。接肢一根根脱落，像秋天的枯叶。",
            "「我……是……王……」",
            "他的身体化为金色的光点消散。",
            "褪色者从他体内拾起一颗巨大的卢恩——「葛瑞克的大卢恩」。"
        ],
        special=greck_special
    )

player_hp = player_max_hp
player_fp = player_max_fp
fill_flask()
player_atk += 2

# 学会「接肢斩」
skills.append({
    "name": "接肢斩", "cost": 15, "type": "guard",
    "lo": 25, "hi": 25,
    "desc": "高伤斩击。并在周身织成护盾，减免下一次伤害。"
})
print()
sl("史东薇尔的风从断裂的城墙吹入，翻动着地上的旗帜。", 0.05)
sl("黄金一族的力量，早已只剩下这些畸形的残影。", 0.06)
print()
sl("▶ 力量提升。攻击力 +2，HP/FP/圣杯瓶已恢复。", 0.04)
sl("▶ 领悟战技「接肢斩」——高伤斩击，附带护盾（下次受伤减免 20%）。", 0.04)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 圆桌厅堂
# ============================================================
print()
bar()
sl("【圆桌厅堂】", 0.06)
bar()
print()

sl("褪色者在赐福处休息时，身体被一团柔和的蓝光包裹。", 0.05)
sl("当光芒散去，褪色者发现自己站在一个完全不同的地方——", 0.05)
sl("一座圆形的厅堂，穹顶极高，", 0.05)
sl("墙壁上排列着无数紧闭的门扉。", 0.05)
sl("中央是一张巨大的圆桌，桌上刻着复杂的纹路，", 0.05)
sl("像星图，又像血管。", 0.05)
print()
pause(0.7)

sl("厅堂里弥漫着淡淡的烛蜡气味与旧羊皮纸的涩味。", 0.05)
print()
pause(0.5)

sl("圆桌旁坐着数人。", 0.05)
sl("一名穿着黑色铠甲、戴着银色面具的瘦高男子站在窗边，一言不发。", 0.05)
sl("一名披着厚重长袍的老者坐在圆桌旁，面前摊开着一张巨大的交界地地图。", 0.05)
sl("一名穿着简朴灰袍的祷告师坐在角落，手中捧着一本翻烂的经卷。", 0.05)
sl("一名身形魁梧的战士靠在柱子上，头盔下露出一双疲惫的眼睛。", 0.05)
sl("以及一位戴着兜帽的女性，坐在圆桌的对面。", 0.05)
print()
pause(0.8)

sl("她的面容被兜帽遮住大半，只能看见一双温柔的、带着疲惫的眼睛。", 0.05)
sl("她身上有一种淡淡的、像干枯花瓣的气息。", 0.05)
pause(0.5)
sl("菲雅：「受赐福指引而来的英雄啊，初次见面，幸会。」", 0.04)
sl("  「我名为菲雅，因故栖身在圆桌厅堂。」", 0.04)
pause(0.4)
sl("她站起身，向褪色者微微欠身。", 0.05)
sl("菲雅：「英雄啊，片刻就好，能否让我抱紧你呢？」", 0.04)
print()
pause(0.4)
sl("[1] 接受拥抱。", 0.01)
sl("[2] 拒绝。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("菲雅张开双臂，轻轻环住褪色者。", 0.05)
    sl("她的身体很冷，像一具尚未完全失去温度的尸体。", 0.05)
    sl("她的呼吸在褪色者耳边轻响，带着一种奇异的安宁。", 0.05)
    pause(0.5)
    sl("菲雅：「谢谢你。……这样，就好。」", 0.04)
    pause(0.4)
    sl("褪色者感到身体中的某种疲惫被抽走了。", 0.05)
    sl("▶ 获得「床帘恩泽」。", 0.04)
    sl("▶ 最大生命值-5 ，攻击力+3", 0.05)
    player_max_hp -= 5
    if player_hp > player_max_hp:
        player_hp = player_max_hp
    player_atk += 3

    print()
    pause(0.5)
    sl("此后，褪色者可以反复与菲雅拥抱。", 0.05)
    sl("...第二次拥抱后——", 0.1)
    pause(0.4)
    sl("菲雅：「英雄啊，我有件事想拜托你。", 0.04)
    sl("  请把这把短剑，交还给它的主人。」", 0.04)
    pause(0.4)
    sl("她递来一把极短的、刀刃上刻着细密纹路的匕首。", 0.05)
    sl("刀柄上缠着磨损的丝线，被摩挲得光滑。", 0.05)
    sl("▶ 获得「侵蚀短剑」。", 0.04)
else:
    sl("菲雅：「……我明白了。」", 0.04)
    sl("她重新坐回圆桌旁，兜帽的阴影重新覆盖了她的面容。", 0.05)
print()
pause(0.6)

sl("圆桌厅堂的窗外，是永不停息的浓雾。", 0.05)
sl("这里不属于交界地的任何一处，", 0.05)
sl("又或许……它存在于每一个赐福的交汇处。", 0.05)
pause(0.4)
sl("那些紧闭的门扉，每一扇后面都传来微弱的声音——", 0.05)
sl("有人在祈祷，有人在哭泣，有人在沉默。", 0.06)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 利耶尼亚 · 湖之利耶尼亚
# ============================================================
print()
bar()
sl("【利耶尼亚 · 湖之利耶尼亚】", 0.06)
bar()
print()

sl("从史东薇尔城后门出发，穿过一条隐秘的山道，", 0.05)
sl("褪色者第一次看见了利耶尼亚。", 0.05)
print()
pause(0.6)

sl("——整片大地被湖水淹没。", 0.07)
print()
pause(0.5)

sl("浅水中矗立着无数断裂的石柱、坍塌的尖塔和半沉的雕像。", 0.05)
sl("水面平静如镜，倒映着灰白色的天空与远处黄金树的光辉。", 0.05)
sl("水面上浮着一层薄薄的雾气，像轻纱。", 0.05)
print()
pause(0.6)

sl("魔法学院雷亚卢卡利亚矗立在湖中央，", 0.05)
sl("被一层透明的蓝色屏障包裹。", 0.05)
sl("学院的高塔上，偶尔闪过魔法的流光。", 0.05)
print()
pause(0.5)

sl("空气中弥漫着湿润的、带点铁锈味的水汽。", 0.05)
sl("水下隐约可见古老建筑的轮廓，像沉没的梦境。", 0.05)
print()
pause(0.5)

sl("褪色者骑着托雷特涉水前行。", 0.05)
sl("马蹄踏碎水面，涟漪扩散开去，", 0.05)
sl("惊起一群群栖息在废墟上的白色水鸟。", 0.05)
print()
pause(0.7)

# ---- 利耶尼亚三岔 ----
sl("涉水前行时，前方出现三条水路。", 0.05)
sl("左侧通向一座半沉的高塔，塔顶还残留着银色的月光符文。", 0.05)
sl("中央是通往学院的正道，蓝色屏障在远处微微发光。", 0.05)
sl("右侧是一处荒废的渔村，几缕黑烟从屋顶升起。", 0.05)
print()
pause(0.5)
sl("[1] 向左，探索高塔。", 0.01)
sl("[2] 直行，前往魔法学院。", 0.01)
sl("[3] 向右，搜索渔村。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2", "3"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你绕过浅水，来到高塔脚下。", 0.05)
    sl("塔门早已腐朽，里面是一段向上延伸的螺旋楼梯。", 0.05)
    pause(0.5)
    sl("高塔顶端，一位早已死去的占星术士倚墙而坐。", 0.05)
    sl("他手中紧握着一卷羊皮纸，指尖已经化为白骨。", 0.05)
    sl("羊皮纸上写满了银色墨水，是一段失传的魔法记录。", 0.05)
    pause(0.4)
    sl("▶ 获得「彗星阿兹尔」的施法记录。攻击力 +4。", 0.04)
    player_atk += 4
elif choice == "2":
    sl("你径直前往学院。", 0.05)
    sl("湖面平静，倒映着远处的黄金树。", 0.05)
    sl("蓝色屏障在你靠近时泛起涟漪，但没有阻止你。", 0.05)
elif choice == "3":
    sl("你踏过浅水，来到渔村边缘。", 0.05)
    sl("村中空无一人，只有几座半沉的木屋和几只翻覆的小船。", 0.05)
    pause(0.5)
    sl("村中央的水井里传来微弱的哭泣声。", 0.05)
    sl("你拉起井绳——只捞上来一只装满卢恩的布袋。", 0.05)
    sl("哭泣声停了。", 0.05)
    pause(0.4)
    max_flask += 1
    sl(f"▶ 圣杯瓶上限 +1（当前 x{max_flask}）。", 0.04)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 卡利亚城寨
# ============================================================
print()
bar()
sl("【卡利亚城寨】", 0.06)
bar()
print()

sl("卡利亚城寨矗立在利耶尼亚西北的悬崖上。", 0.05)
sl("城寨的建筑风格与史东薇尔截然不同——", 0.05)
sl("优雅、精致，线条流畅如月光的轨迹。", 0.05)
sl("墙壁上雕刻着繁复的星象图与月相变化。", 0.05)
print()
pause(0.6)

sl("但城寨已经半毁。", 0.05)
sl("魔法陷阱在走廊中闪烁，", 0.05)
sl("半透明的魔法骑士在庭院中巡逻。", 0.05)
sl("他们的铠甲上刻着卡利亚的徽记——", 0.05)
sl("一轮被星辰环绕的满月。", 0.05)
print()
pause(0.6)

sl("褪色者穿过城寨，在最高处的露台上击败了禁卫骑士罗蕾塔。", 0.05)
sl("她骑着一匹半透明的魔法战马，", 0.05)
sl("手中的镰刀划过空气时留下银蓝色的轨迹。", 0.05)
print()
pause(0.6)

sl("罗蕾塔（消散前）：「……菈妮大人……」", 0.04)
sl("  「请……照顾好她……」", 0.04)
pause(0.5)
sl("她的身体化为银色的光点，融入城寨的墙壁中。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第二幕 · 三姊妹塔 · 菈妮
# ============================================================
print()
bar()
sl("【三姊妹塔】", 0.06)
bar()
print()

sl("穿过卡利亚城寨后门，是一片被浓雾永久笼罩的高地。", 0.05)
sl("三座石塔矗立在雾中，", 0.05)
sl("塔身被藤蔓与暗蓝色的发光苔藓覆盖。", 0.05)
print()
pause(0.6)

sl("中央的塔——菈妮魔法师塔——最高。", 0.05)
sl("塔门没有上锁，推开时发出沉闷的声响。", 0.05)
print()
pause(0.5)

sl("塔内，螺旋楼梯向上延伸，", 0.05)
sl("墙壁上嵌着发光的石灯，光芒是银蓝色的，像月光凝结而成。", 0.05)
print()
pause(0.6)

sl("塔顶的房间。一位蓝皮肤、四只手臂的魔女坐在高背椅上。", 0.05)
sl("她的身体——那是人偶的身体。", 0.05)
sl("精细的关节、瓷白的表面、", 0.05)
sl("以及肩膀上披着的蓝色斗篷。", 0.05)
sl("她的头上戴着一顶宽檐帽，", 0.05)
sl("帽檐下是一张精致却毫无温度的面孔。", 0.05)
sl("她的眼睛是金色的，像两颗嵌入瓷面的宝石。", 0.05)
pause(0.5)
sl("膝盖上放着一本翻开的书。", 0.05)
print()
pause(0.8)

sl("菈妮：「哦，我们又见面了。」", 0.04)
pause(0.4)
sl("她的声音平静，但语调中有一丝几乎无法察觉的波动。", 0.05)
sl("菈妮：「我记得上次见面时，我说我的名字是蕾娜。", 0.04)
sl("  看到托雷特安然无恙，我很高兴……」", 0.04)
pause(0.4)
sl("她合上书，四只手臂在膝上交叠。", 0.05)
sl("菈妮：「但褪色者啊，你来这里做什么？我不记得给你发过邀请。」", 0.04)
print()
pause(0.6)

sl("褪色者沉默。", 0.05)
print()
pause(0.4)

sl("菈妮：「没有特别的理由，你是这么说的？", 0.04)
sl("  有趣。那么或许是命运引导你来到这里重逢的。」", 0.04)
pause(0.4)
sl("她站起身。人偶的身体在行动时发出极轻微的、像瓷器摩擦的声响。", 0.05)
sl("菈妮：「……你愿意为我效力吗？」", 0.04)
pause(0.5)
sl("她走向塔楼中央，四只手臂缓缓展开，像一尊古老的神像。", 0.05)
sl("菈妮：「我是魔女菈妮。我在很久以前偷走了死亡，", 0.04)
sl("  如今正在寻找一条深入黑暗的道路。", 0.04)
sl("  有朝一日，我要颠覆这一切，让黄金律法从这片土地上消失。」", 0.04)
pause(0.5)
sl("她的金色眼睛直视褪色者，里面有一种燃烧的、冰冷的东西。", 0.05)
print()
pause(0.5)
sl("[1] 「我愿为你效力。」", 0.01)
sl("[2] 「我对魔女的战争没有兴趣。」", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    stars = stars + 2
    ranni_route = True
    sl("菈妮沉默了片刻。", 0.05)
    pause(0.4)
    sl("然后，她的嘴角微微上扬——", 0.05)
    sl("那是一个极罕见的、几乎不可见的笑意，", 0.05)
    sl("像是冰面下闪过的一尾鱼。", 0.05)
    pause(0.4)
    sl("菈妮：「……很好。」", 0.04)
    pause(0.4)
    sl("她坐回高背椅，重新翻开书。", 0.05)
    sl("但褪色者注意到，她的目光并没有落在书页上。", 0.05)
    sl("菈妮：「布莱泽会告诉你接下来该做什么。", 0.04)
    sl("  我有些……别的事要处理。」", 0.04)
    print()
    pause(0.5)
    sl("▶ 星辰值 +2", 0.04)
    print()
    pause(0.6)
    sl("塔楼的三层，半狼布莱泽靠在墙边。", 0.05)
    sl("他穿着一身破旧的铠甲，毛皮从关节处露出，", 0.05)
    sl("一只眼睛上有一道横贯的伤疤。", 0.05)
    sl("他的声音低沉而沙哑。", 0.05)
    pause(0.4)
    sl("布莱泽：「菈妮大人很少对人说这么多话。……你不一样。」", 0.04)
    print()
    pause(0.5)
    sl("塔楼底层，军师伊吉坐在一堆巨大的铁砧与武器之间。", 0.05)
    sl("他的头盔巨大而沉重，像一尊移动的熔炉。", 0.05)
    sl("他说话时，头盔里传出沉闷的回响。", 0.05)
    pause(0.4)
    sl("伊吉：「欢迎。菈妮大人选择了你，那就没有什么可多说的。", 0.04)
    sl("  只是……这条路上，会有很多东西试图阻止你。做好准备。」", 0.04)
    print()
    pause(0.5)
    sl("塔楼地下，魔法教授塞尔维斯戴着银色面具，", 0.05)
    sl("坐在一排排摆满瓶罐的架子前。", 0.05)
    sl("那些瓶罐中漂浮着某种暗色的液体，", 0.05)
    sl("隐约可见其中的人形轮廓。", 0.05)
    pause(0.4)
    sl("塞尔维斯（低声）：「嘘……别让菈妮大人听见。", 0.04)
    sl("  我有一件小事想请你帮忙。", 0.04)
    sl("  这瓶药水……请把它交给圆桌厅堂的涅斐丽·露。", 0.04)
    sl("  她是个有用的素材。」", 0.04)
    print()
    pause(0.5)
    sl("[1] 将药水交给涅斐丽。", 0.01)
    sl("[2] 将药水交给百智爵士。", 0.01)
    sl("[3] 不交出药水，搁置。", 0.01)
    sub = input("> ").strip()
    while sub not in ("1", "2", "3"):
        sl("无效输入，请重新选择。", 0.03)
        sub = input("> ").strip()
    print()
    if sub == "1":
        sl("你将药水交给涅斐丽。", 0.05)
        sl("她接过药水，仰头喝了下去。", 0.05)
        pause(0.5)
        sl("她的眼神慢慢变得空洞。", 0.05)
        sl("片刻后，她转身离去——动作僵硬，像一具提线木偶。", 0.05)
        print()
        pause(0.6)
        sl("远处，塞尔维斯的笑声从塔楼深处传来。", 0.05)
        sl("「……很好。这是你的报酬。」", 0.04)
        print()
        pause(0.5)
        sl("▶ 涅斐丽再也没能成为宁姆格福的新领主。", 0.04)
        sl("▶ 领悟战技「傀儡突袭」—— FP 15，固定 45 伤害。", 0.04)
        skills.append({
            "name": "傀儡突袭", "cost": 15, "type": "fixed_only",
            "lo": 45, "hi": 45,
            "desc": "召唤傀儡突袭。固定 45 伤害，无视攻击力。"
        })

    elif sub == "2":
        sl("你将药水交给百智爵士。", 0.05)
        sl("他接过药水，面具下的眼睛眯起——像在阅读一段只有他能看见的文字。", 0.05)
        pause(0.5)
        sl("「……塞尔维斯。原来如此。」", 0.04)
        pause(0.4)
        sl("「这瓶药水本会让涅斐丽成为他的傀儡。」", 0.04)
        sl("「你救了她一命。」", 0.04)
        pause(0.5)
        sl("百智从怀中取出一份卷轴，递给你。", 0.05)
        sl("「这是塞尔维斯的笔记——他对战斗动作的分析，对你会有用。」", 0.04)
        print()
        pause(0.5)
        sl("▶ 获得「塞尔维斯的笔记」 —— 攻击力+2，且你使用重击时不会再被敌人看破", 0.04)
        player_atk += 2
        not_being_counter = True

    else:
        sl("你收起药水。", 0.05)
        sl("它安静地躺在行囊深处，像一段还没有说出口的秘密。", 0.05)
        pause(0.5)
        sl("夜里，药水的味道从瓶塞缝隙中渗出——", 0.05)
        sl("苦，涩，还有一点奇异的甜。", 0.05)
        sl("你感到身体里的某种东西，正在慢慢变得坚韧。", 0.05)
        print()
        pause(0.5)
        sl("▶ 最大 HP +20（药水的精华被你慢慢吸收）。", 0.04)
        player_max_hp += 20
        player_hp += 20
else:
    order = order + 1
    sl("菈妮沉默了很久。塔楼里的空气变得冰冷。", 0.05)
    pause(0.5)
    sl("菈妮：「……那就让黄金律法继续腐烂下去吧。」", 0.04)
    pause(0.4)
    sl("她合上书，站起身，走向塔楼的窗边。", 0.05)
    sl("她的背影纤细而笔直，像一把插入地面的剑。", 0.05)
    sl("菈妮：「你走吧。」", 0.04)
    print()
    pause(0.5)
    sl("▶ 秩序值 +1，菈妮线关闭。", 0.04)
    print()
    pause(0.6)
    sl("塔楼的门在褪色者身后关上。", 0.05)
    sl("雾更浓了。三姊妹塔的轮廓在雾中模糊，像三个沉默的守望者。", 0.05)
    pause(0.4)
    sl("布莱泽站在塔外的台阶上，没有说话。", 0.05)
    sl("他只是看着褪色者，那只独眼中有一丝……失望。", 0.06)
print()
input("按回车继续……")


# ============================================================
# 第三幕 · 盖利德
# ============================================================
print()
bar()
sl("【第三幕 · 盖利德】", 0.06)
bar()
print()

sl("从利耶尼亚东行，穿过亚坛高原的边缘，", 0.05)
sl("褪色者进入了盖利德。", 0.05)
print()
pause(0.6)

sl("——那是一整片燃烧的大地。", 0.07)
print()
pause(0.5)

sl("天空被染成暗红色，空气中弥漫着硫磺与灰烬的气味。", 0.05)
sl("大地龟裂，裂缝中涌出暗红色的光。", 0.05)
sl("枯死的树木以扭曲的姿态矗立，", 0.05)
sl("枝干上挂满了风干的肉块。", 0.05)
print()
pause(0.6)

sl("远处，一座巨大的城堡矗立在红色的荒原上。红狮子城。", 0.05)
sl("城墙上挂满了旗帜，但旗帜的颜色早已被血与灰覆盖。", 0.05)
print()
pause(0.6)

sl("盖利德曾是交界地最丰饶的土地之一。", 0.05)
sl("但在「碎星」拉塔恩与「女武神」玛莲妮亚的那场战斗中，", 0.05)
sl("玛莲妮亚释放了猩红腐败。", 0.05)
pause(0.4)
sl("从此，盖利德再也没有春天。", 0.06)
print()
pause(0.6)

# ---- 盖利德 · 腐败村庄岔路 ----
sl("穿过红狮子城外的荒原，你抵达了一座废弃的村庄。", 0.05)
sl("房屋的墙壁上长满了猩红色的腐败菌毯。", 0.05)
sl("空气中弥漫着甜腻的、腐臭的气味。", 0.05)
print()
pause(0.5)
sl("[1] 进入村庄搜索。", 0.01)
sl("[2] 绕道而行。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你踩过软塌塌的地面，在一间屋内发现了一具骑士的尸体。", 0.05)
    sl("他的铠甲上还残留着红狮子的纹章。", 0.05)
    sl("铠甲内侧，缝着一块小小的皮革，上面用炭笔写着：", 0.05)
    pause(0.4)
    sl("「若你见到拉塔恩将军——", 0.05)
    sl("  请告诉他，红狮子们从未离开。」", 0.05)
    pause(0.5)
    radahn_bonus = True
    sl("▶ 获得「拉塔恩的碎星徽记」—— 拉塔恩使用引星时，可以额外行动", 0.04)
else:
    sl("你绕开了村庄。远处传来猩红腐败的低语。", 0.05)
    sl("那种声音，像是有什么东西在地底缓慢地呼吸。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第三幕 · 红狮子城 · 战斗祭典
# ============================================================
print()
bar()
sl("【红狮子城 · 战斗祭典】", 0.06)
bar()
print()

sl("红狮子城广场上，沙尘漫天。", 0.05)
sl("广场中央搭起了一座高台，", 0.05)
sl("台上站着一名身穿红狮子铠甲的老兵，正在高声宣读祭典的规则。", 0.05)
print()
pause(0.5)

sl("「战斗祭典——正式开始！」", 0.05)
sl("「今日，我们要讨伐的，是‘碎星’拉塔恩将军！」", 0.05)
sl("「他是黄金一族的末裔，是交界地最强的战士之一！」", 0.05)
sl("「也是——封印了星辰运转的男人！」", 0.05)
print()
pause(0.7)
#blaze
sl("广场边缘，半狼布莱泽正靠在墙上磨刀。", 0.05)
sl("他的巨剑上布满了细密的裂痕，但刃口依然锋利。", 0.05)
pause(0.4)
sl("布莱泽：「你来了。菈妮大人已经跟我说了。", 0.04)
sl("  ……拉塔恩将军封印了星辰的运转。", 0.04)
sl("  只要他还活着，菈妮大人的命运就无法前进。」", 0.04)
pause(0.4)
sl("他抬起头，那只独眼望向远处的荒原。", 0.05)
sl("布莱泽：「他很强大。……但正因如此，才值得一战。」", 0.04)
print()
pause(0.5)

sl("战士壶亚历山大在广场边缘活动着自己的「关节」。", 0.05)
sl("他的陶罐身体发出嘎吱嘎吱的声响。", 0.05)
pause(0.4)
sl("亚历山大：「褪色者！你也是来参加祭典的吗？", 0.04)
sl("  这可是千载难逢的机会——与传说中的拉塔恩将军交手！", 0.04)
sl("  我亚历山大，一定会在这场战斗中……变得更加强大！」", 0.04)
print()
pause(0.7)


# ---- 拉塔恩战 ----
def radahn_special(hp, max_hp):
    """
    拉塔恩特殊机制：
      每 4 回合一次的碎星箭
      血量低于 40% → telegraph（预告）
      下一回合    → radahn_lethal_hit（引星）
      若已获得碎星徽记 → 引星时改为 skip（看穿）
    """
    if not hasattr(radahn_special, "state"):
        radahn_special.state = "idle"
    if not hasattr(radahn_special, "turn"):
        radahn_special.turn = 0

    radahn_special.turn += 1

    # ---- n 回合：释放引星 ----
    if radahn_special.state == "telegraphing":
        radahn_special.state = "done"
        if radahn_bonus:
            return True, "拉塔恩举起弯刀，引力漩涡将你扯向他,似乎想奋起一击 —— 但你早已看穿—— 「拉塔恩的碎星徽记」生效，获得额外回合。 ", "skip"
        else:
            return True, "拉塔恩举起弯刀，紫色的引力漩涡将你扯向他——", "radahn_lethal_hit"

    # ---- n-1 回合：预告 ----
    if hp <= max_hp * 0.4 and radahn_special.state == "idle":
        radahn_special.state = "telegraphing"
        return True, "拉塔恩停住了。紫色的光在他弯刀周围凝聚——", "telegraph"

    # ---- 常规：每 4 回合一次碎星箭 ----
    if radahn_special.turn % 4 == 1:
        return True, "拉塔恩拉开巨弓，碎星箭破空而来——", "damage_boost"


    return False, "", ""


sl("拉塔恩从荒原深处现身。", 0.05)
sl("他身高数十丈，骑着一匹同样巨大的、瘦骨嶙峋的战马。", 0.05)
sl("他的铠甲上覆盖着碎星战斗留下的熔岩与伤痕，", 0.05)
sl("头盔下露出一张被猩红腐败侵蚀的脸。", 0.05)
sl("他举起那双巨大的弯刀，双刀上缠绕着紫色的引力魔法。", 0.05)
pause(0.5)
sl("「碎星」拉塔恩——黄金一族最强大的战士，封印星辰的男人。", 0.06)
print()
pause(0.7)

win = False
while not win:
    # 重打时重置状态
    if hasattr(radahn_special, "state"):
        del radahn_special.state
    if hasattr(radahn_special, "turn"):
        del radahn_special.turn

    win = battle(
        "碎星 拉塔恩", 300, 22,
        intro_lines=[
            "拉塔恩从荒原深处现身。",
            "他身高数十丈，双刀上缠绕着紫色的引力魔法。",
            "「——」他没有说话，只是举起了刀。"
        ],
        win_lines=[
            "拉塔恩从战马上坠落，巨大的身躯砸在地上。",
            "「……玛莲妮亚……你……赢了……」",
            "他的身体开始崩塌。引力魔法从体内涌出，升向天空。",
            "群星重新开始转动。一颗流星坠落在宁姆格福西部。"
        ],
        special=radahn_special
    )

player_hp = player_max_hp
player_fp = player_max_fp
max_flask += 1
fill_flask()
player_atk += 3

# 学会「碎星箭」
skills.append({
    "name": "碎星箭", "cost": 20, "type": "fixed",
    "lo": 30, "hi": 30,
    "desc": "固定 30 伤害。撕开敌人防御，2 回合内受伤增加 30%。"
})

print()
sl("布莱泽（仰头望天）：「看。星辰动了。", 0.04)
sl("  ……去陨石坠落的地方吧。通往永恒之城的道路，就在那里。」", 0.04)
print()
sl("▶ 你击碎了星辰的封印。攻击力 +3。", 0.04)
sl("▶ 领悟战技「碎星箭」——固定 30 伤害，敌人易伤 2 回合。", 0.04)
print()
input("按回车继续……")


# ============================================================
# 第三幕 · 诺克隆恩 · 永恒之城（仅菈妮线）
# ============================================================
if ranni_route:
    print()
    bar()
    sl("【诺克隆恩 · 永恒之城】", 0.06)
    bar()
    print()

    sl("褪色者穿过流星坠落后形成的巨大陨石坑。", 0.05)
    sl("坑底，一座古老城市的大门显露出来。", 0.05)
    print()
    pause(0.6)

    sl("诺克隆恩——永恒之城。", 0.06)
    print()
    pause(0.5)

    sl("整座城市被一层永恒的、深蓝色的光芒笼罩。", 0.05)
    sl("天空是假的——那是巨大洞穴的穹顶，", 0.05)
    sl("上面镶嵌着无数发光的矿石，像星辰。", 0.05)
    print()
    pause(0.5)

    sl("城市的建筑风格古老而陌生。", 0.05)
    sl("墙壁上刻着与地面世界完全不同的文字与图案。", 0.05)
    sl("那些图案中反复出现一个形象——", 0.05)
    sl("一个坐在王座上的、长着巨大独眼的存在。", 0.05)
    print()
    pause(0.6)

    sl("永恒之城，诺克隆恩。", 0.05)
    sl("在黄金律法降临之前，这里曾是一个信奉「黑月」的文明。", 0.05)
    sl("他们试图创造自己的律法，自己的王。", 0.05)
    pause(0.4)
    sl("然后——无上意志降下了惩罚。", 0.06)
    print()
    pause(0.7)

    # ---- 仿身泪滴岔路 ----
    sl("在诺克隆恩的一条支路上，你发现了一处被封印的祭坛。", 0.05)
    sl("祭坛中央悬浮着一滴银色的液体——", 0.05)
    sl("「仿身泪滴的骨灰」。", 0.05)
    sl("它安静地旋转着，像是在观察你。", 0.05)
    print()
    pause(0.5)
    sl("[1] 取下骨灰。", 0.01)
    sl("[2] 不碰它。", 0.01)
    choice = input("> ").strip()
    while choice not in ("1", "2"):
        sl("无效输入，请重新选择。", 0.03)
        choice = input("> ").strip()
    print()

    if choice == "1":
        sl("你伸出手。骨灰化为银色光点，融入你的召魂铃。", 0.05)
        sl("▶ 获得「仿身泪滴的骨灰」——", 0.04)
        sl("  每场战斗中，你可召唤一个分身替你承担一次致命伤害。", 0.04)
        mimic_tear = True
    else:
        sl("你收回手。有些东西，不该被带走。", 0.05)
        sl("银色的液体继续在原地旋转，像一个没有答案的问题。", 0.05)
    print()
    input("按回车继续……")

    # ---- 猎杀指头刀 ----
    sl("褪色者穿过城市，在黑夜神域的最深处，", 0.05)
    sl("一个巨大的骷髅掌中，找到了一把黑色短刀。", 0.05)
    sl("刀身极薄，几乎透明，刀刃上流淌着暗紫色的光芒。", 0.05)
    sl("▶ 获得「猎杀指头刀」。", 0.04)
    print()
    pause(0.6)

    sl("当褪色者将刀带回菈妮魔法师塔时，", 0.05)
    sl("菈妮从高背椅上站起。", 0.05)
    sl("她的四只手臂同时伸出，接过刀。", 0.05)
    sl("她的手指微微颤抖——", 0.05)
    sl("人偶的手指，却能如此精确地传达这种颤抖。", 0.05)
    pause(0.5)
    sl("菈妮：「……你做到了。」", 0.04)
    pause(0.4)
    sl("她将刀举到面前，金色的眼睛里映着刀身上暗紫色的光芒。", 0.05)
    sl("菈妮：「这把刀，能让我斩断二指的枷锁。」", 0.04)
    pause(0.5)
    sl("她转过身，面朝塔楼窗外。", 0.05)
    sl("远处，黄金树的光芒在雾中若隐若现。", 0.05)
    pause(0.4)
    sl("菈妮：「我要睡一会儿。", 0.04)
    sl("  ……在安瑟尔河，有一具石棺。去那里吧。」", 0.04)
    pause(0.5)
    sl("她的身体开始变得透明。", 0.05)
    sl("人偶的关节发出细微的咔嗒声，", 0.05)
    sl("像是某种古老机械正在停止运转。", 0.05)
    pause(0.4)
    sl("菈妮：「……谢谢你。」", 0.04)
    pause(0.5)
    sl("她的身影消散。", 0.05)
    sl("塔楼中只剩下刀上残留的暗紫色光芒，缓缓消散在空气中。", 0.05)
    print()
    pause(0.5)
    stars = stars + 2
    sl("▶ 星辰值 +2。", 0.04)
    print()
    input("按回车继续……")

    # ---- 安瑟尔河 · 娇小菈妮 ----
    print()
    bar()
    sl("【安瑟尔河 · 娇小菈妮】", 0.06)
    bar()
    print()

    sl("蕾娜魔法师塔的传送门将褪色者送到了安瑟尔河。", 0.05)
    print()
    pause(0.5)

    sl("——那是一条地底暗河。", 0.06)
    print()
    pause(0.5)

    sl("巨大的洞穴中，暗绿色的河水缓缓流淌，", 0.05)
    sl("水面上漂浮着发光的苔藓与巨大的白色花朵。", 0.05)
    sl("洞穴壁上刻满了与诺克隆恩相同的文字。", 0.05)
    sl("空气中弥漫着潮湿的、带点甜味的腐败气息。", 0.05)
    print()
    pause(0.6)

    sl("褪色者在河岸的石棺上找到了一个小小的人偶。", 0.05)
    sl("人偶只有手掌大小，做工精致，", 0.05)
    sl("穿着蓝色的斗篷，头上戴着小巧的宽檐帽。", 0.05)
    sl("它的脸——是菈妮的脸，但更柔和，更年轻。", 0.05)
    sl("▶ 获得「娇小菈妮」。", 0.04)
    print()
    pause(0.6)

    sl("褪色者在赐福处反复休息，人偶始终沉默。", 0.05)
    sl("直到第三次——", 0.05)
    pause(0.5)
    sl("娇小菈妮（声音从人偶中传来，带着一丝被吵醒的恼怒）：", 0.04)
    sl("  「……真吵。你到底要做什么？」", 0.04)
    print()
    pause(0.5)
    sl("[1] 继续对话，追问她的过去。", 0.01)
    sl("[2] 简短回应，直奔任务。", 0.01)
    choice = input("> ").strip()
    while choice not in ("1", "2"):
        sl("无效输入，请重新选择。", 0.03)
        choice = input("> ").strip()
    print()

    if choice == "1":
        sl("经过数次追问，人偶中的声音逐渐变得柔和。", 0.05)
        pause(0.5)
        sl("娇小菈妮：「……你想知道我为什么偷走死亡？", 0.04)
        sl("  因为黄金律法不容许死亡。", 0.04)
        sl("  葛德文本该死去，但他没有。", 0.04)
        sl("  他成了‘死王子’，一个不该存在的东西。", 0.04)
        sl("  我偷走了一部分死亡卢恩，杀了自己的肉身。", 0.04)
        sl("  只有这样，我才能摆脱二指的控制。」", 0.04)
        print()
        pause(0.6)
        sl("褪色者：「你恨他吗？葛德文。」", 0.05)
        print()
        pause(0.7)
        sl("娇小菈妮（沉默了很久）：「……恨。也不恨。", 0.04)
        sl("  他是我的哥哥。但他也是黄金律法的牺牲品。", 0.04)
        sl("  ……够了。别问了。」", 0.04)
        pause(0.6)
        sl("人偶沉默。", 0.05)
        sl("但褪色者能感觉到，在沉默之下，有什么东西在微微颤动。", 0.05)
        print()
        pause(0.5)
        stars = stars + 1
        sl("▶ 星辰值 +1。", 0.04)
    else:
        sl("你简短地应了一声。人偶不再说话。", 0.05)
        sl("但你能感到，它在你行囊中轻轻动了一下。", 0.05)
    print()
    pause(0.6)

    sl("安瑟尔河的河水继续流淌。", 0.05)
    sl("在那条河的最深处，通向一片被称为「腐败湖」的禁忌之地。", 0.05)
    pause(0.4)
    sl("而在那之前，褪色者还有很长的路要走。", 0.06)
    print()
    input("按回车继续……")

else:
    # 未开启菈妮线 —— 跳过诺克隆恩与安瑟尔河
    print()
    sl("（你未曾与菈妮结盟，永恒之城的大门对你紧闭。）", 0.05)
    sl("（星辰的坠落与你无关。）", 0.05)
    print()
    input("按回车继续……")


# ============================================================
# 第四幕 · 王城罗德尔
# ============================================================
print()
bar()
sl("【第四幕 · 王城罗德尔】", 0.06)
bar()
print()

sl("从利耶尼亚东行，穿过迪可达斯大升降机，", 0.05)
sl("褪色者登上了亚坛高原。", 0.05)
print()
pause(0.6)

sl("高原上的空气比下方清澈得多。", 0.05)
sl("巨大的黄金树矗立在高原中央，树干粗如山脉，", 0.05)
sl("金色的树冠撑起整片天空。", 0.05)
sl("树皮上流淌着金色的光芒，像血液在血管中流淌。", 0.05)
print()
pause(0.6)

sl("空气中弥漫着一种奇异的、像蜂蜜与铁锈混合的气味。", 0.05)
print()
pause(0.5)

sl("王城罗德尔矗立在黄金树脚下。", 0.05)
sl("城墙由纯白色的巨石砌成，", 0.05)
sl("城墙上雕刻着黄金律法的符文与历代艾尔登之王的肖像。", 0.05)
print()
pause(0.6)

sl("但王城已经被封锁。", 0.05)
sl("巨大的龙尸挂在城墙上，龙翼上插满了黄金树的枝干。", 0.05)
sl("城门紧闭，只有一条隐秘的通道可以进入。", 0.05)
print()
pause(0.6)

sl("王城罗德尔——黄金律法的中心。", 0.05)
sl("千年来，无数褪色者试图进入这里。大多数人死在了路上。", 0.05)
pause(0.4)
sl("而进入的人……也未必能活着出来。", 0.06)
print()
pause(0.6)

# ---- 黄金树下的祈祷 ----
sl("黄金树的树根旁，有一座被藤蔓缠绕的小祭坛。", 0.05)
sl("祭坛上刻着古老的祈祷文。", 0.05)
sl("树根在你靠近时微微颤动，像是在回应你的呼吸。", 0.05)
print()
pause(0.5)
sl("[1] 跪下来祈祷。", 0.01)
sl("[2] 不理会，继续前进。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你跪下。金色的光点从树根间升起，环绕着你。", 0.05)
    sl("一个声音在脑中响起——那是黄金律法最后的声音：", 0.05)
    pause(0.5)
    sl("「……你……为何……而来？」", 0.05)
    print()
    sl("[1] 「为了成为艾尔登之王。」", 0.01)
    sl("[2] 「为了改变这一切。」", 0.01)
    sl("[3] 「为了烧尽一切。」", 0.01)
    choice2 = input("> ").strip()
    while choice2 not in ("1", "2", "3"):
        sl("无效输入，请重新选择。", 0.03)
        choice2 = input("> ").strip()
    print()

    if choice2 == "1":
        order += 2
        sl("金光在你身上短暂停留，然后消散。", 0.05)
        sl("▶ 秩序值 +2。", 0.04)
    elif choice2 == "2":
        stars += 2
        sl("金光转向远处——夜空的方向。", 0.05)
        sl("▶ 星辰值 +2。", 0.04)
    else:
        frenzy += 3
        sl("金光剧烈颤抖，然后破碎。", 0.05)
        sl("▶ 癫火值 +3。", 0.04)
else:
    sl("你没有停下脚步。", 0.05)
    sl("祭坛在身后微微发光，然后慢慢暗淡下去。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第四幕 · 菲雅线
# ============================================================
print()
bar()
sl("【圆桌厅堂 · 菲雅线】", 0.06)
bar()
print()

sl("褪色者将侵蚀短剑交给D。", 0.05)
sl("D接过短剑时，面具下的眼睛眯了一下。", 0.05)
pause(0.4)
sl("D：「……这是菲雅的东西。", 0.04)
sl("  我知道了。」", 0.04)
print()
pause(0.6)

sl("数日后，褪色者回到圆桌厅堂。", 0.05)
sl("D倒在圆桌旁，胸口插着那把侵蚀短剑。", 0.05)
sl("他的面具碎裂，露出一张年轻却已经僵硬的脸。", 0.05)
print()
pause(0.6)

sl("菲雅站在圆桌的另一端。", 0.05)
sl("她的兜帽已经放下，露出一张苍白而平静的面孔。", 0.05)
sl("她的眼睛是深灰色的，像雾中的湖面。", 0.05)
pause(0.5)
sl("菲雅：「你来了。", 0.04)
sl("  ……你想否定我吗？否定我所做的一切？」", 0.04)
pause(0.4)
sl("她的声音很轻，像在说一件与己无关的事。", 0.05)
sl("菲雅：「我是保护死诞者的人，甚至被咒骂成肮脏的魔女。", 0.04)
sl("  你是知情之后，还这么要求吗？」", 0.04)
print()
pause(0.5)
sl("[1] 「我不否定你。」", 0.01)
sl("[2] 「死诞者不该存在。」", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("菲雅：「……谢谢你。」", 0.04)
    pause(0.4)
    sl("她的眼中闪过一丝微弱的光芒，像湖面反射的星光。", 0.05)
    sl("菲雅：「那么，请把菈妮的另一半百足环——", 0.04)
    sl("  ‘死亡的咒痕’交给我。」", 0.04)
    print()
    pause(0.5)
    sl("褪色者从利耶尼亚神授塔获得「死亡的咒痕」，交给菲雅。", 0.05)
    sl("菲雅接过咒痕，将它放在D的尸体上。", 0.05)
    pause(0.4)
    sl("菲雅：「我会进入他的梦境。", 0.04)
    sl("  ……在那之前，我想告诉你一件事。", 0.04)
    sl("  死诞者不是怪物。他们只是……没有被允许死去的人。", 0.04)
    sl("  黄金律法拒绝了死亡。但死亡是生命的一部分。", 0.04)
    sl("  拒绝死亡，就是拒绝生命本身。」", 0.04)
    print()
    pause(0.6)
    sl("她俯身在D的额头轻吻。", 0.05)
    sl("然后，她的身体化为灰色的雾气，消散在空气中。", 0.05)
    print()
    pause(0.6)
    sl("褪色者进入死眠梦境。", 0.05)
    sl("在梦境的尽头，一条巨大的、由骸骨构成的龙——", 0.05)
    sl("死龙弗尔桑克斯——正守护着菲雅。", 0.05)
    print()
    pause(0.6)
    sl("战斗。弗尔桑克斯的每一次呼吸都带着死亡的气息，", 0.05)
    sl("它的翅膀扇动时，梦境中的地面龟裂。", 0.05)
    sl("褪色者在大大小小的死亡能量中闪避，", 0.05)
    sl("趁它吐息的间隙攻击它的头部。", 0.05)
    print()
    pause(0.6)
    sl("当弗尔桑克斯倒下时，它的身体化为无数灰色的光点。", 0.05)
    sl("菲雅站在光点中央，怀中抱着一个蜷缩的、灰白色的婴儿。", 0.05)
    pause(0.5)
    sl("菲雅（声音从远处传来）：「……谢谢你。", 0.04)
    sl("  这个孩子……葛德文的孩子……终于可以安息了。」", 0.04)
    print()
    pause(0.6)
    have_death_rune = True
    sl("▶ 获得「死王子的修复卢恩」。", 0.04)
    print()
    pause(0.5)
    sl("圆桌厅堂中，D的弟弟跪在哥哥的尸体前。", 0.05)
    sl("他没有哭。只是沉默地，", 0.05)
    sl("将哥哥的面具碎片一片片拾起，拼在一起。", 0.06)
else:
    sl("菲雅：「……我明白了。」", 0.04)
    pause(0.4)
    sl("她的身影消散。圆桌厅堂中只剩下D冰冷的尸体。", 0.05)
    sl("你什么也没得到。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第四幕 · 食粪者线
# ============================================================
print()
bar()
sl("【王城下水道 · 食粪者】", 0.06)
bar()
print()

sl("王城罗德尔的下水道深处，空气变得浓稠而恶臭。", 0.05)
sl("墙壁上覆盖着一层暗红色的、像血肉一样的物质。", 0.05)
print()
pause(0.5)

sl("在一间被锁链封锁的牢房中，褪色者遇到了食粪者。", 0.05)
sl("他戴着一顶像绞刑架般的头盔，", 0.05)
sl("头盔上缠绕着生锈的铁丝。", 0.05)
sl("他的身体被锁链束缚在墙上，", 0.05)
sl("身上覆盖着一层暗红色的污垢。", 0.05)
print()
pause(0.6)

sl("食粪者：「褪色者。", 0.04)
sl("  我观察你很久了。」", 0.04)
pause(0.4)
sl("他的声音从头盔下传出，沉闷而扭曲。", 0.05)
sl("食粪者：「……你的身体，很适合被玷污。", 0.04)
sl("  拿去，这是下水道监牢的钥匙。", 0.04)
sl("  如果你想要完成我的律法，就去收集‘温床的诅咒’。", 0.04)
sl("  五个。把它们带给我。」", 0.04)
print()
pause(0.5)
sl("[1] 收集五个温床的诅咒，交给食粪者。", 0.01)
sl("[2] 无视食粪者。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("褪色者在交界地各处找到了五个温床的诅咒——", 0.05)
    sl("那些是死诞者被玷污的胎盘，", 0.05)
    sl("暗红色的、还在微微搏动的肉块。", 0.05)
    print()
    pause(0.6)
    sl("将最后一个温床交给食粪者时，", 0.05)
    sl("他的身体开始剧烈颤抖。", 0.05)
    pause(0.4)
    sl("食粪者：「……终于……", 0.04)
    sl("  我的律法……我的诅咒……」", 0.04)
    pause(0.5)
    sl("他的身体从内部裂开，", 0.05)
    sl("暗红色的污浊从裂缝中涌出。", 0.05)
    sl("他发出扭曲的呻吟，然后死去。", 0.05)
    print()
    pause(0.6)
    have_dung_rune = True
    sl("▶ 获得「忌讳诅咒的修复卢恩」。", 0.04)
    print()
    pause(0.5)
    sl("下水道的深处，食粪者的尸体开始腐烂。", 0.05)
    sl("那种气味，像是最深的绝望被熬煮了千年。", 0.06)
else:
    sl("你转身离开。下水道的深处，只有锁链的响声。", 0.05)
    sl("食粪者在黑暗中低声笑了。", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第四幕 · 黄金律法线（柯林与金面具）
# ============================================================
print()
bar()
sl("【黄金律法线 · 柯林与金面具】", 0.06)
bar()
print()

sl("祷告师柯林离开圆桌厅堂，前往亚坛高原寻找贤者金面具。", 0.05)
print()
pause(0.5)

sl("褪色者在穿林大桥附近找到柯林。", 0.05)
sl("他跪在路边，面前摊开着一本翻烂的经卷，口中念念有词。", 0.05)
pause(0.4)
sl("柯林：「啊，是你。", 0.04)
sl("  ……我在寻找一位名叫金面具的贤者。", 0.04)
sl("  他知晓黄金律法的全貌。", 0.04)
sl("  如果你见到他，请告诉我。」", 0.04)
print()
pause(0.6)

sl("褪色者在断桥对面的悬崖边找到金面具。", 0.05)
print()
pause(0.5)

sl("——他一动不动地坐着，像一尊被遗忘的雕像。", 0.05)
sl("他的身体覆盖着一层薄薄的金色灰尘，", 0.05)
sl("像是从体内渗出的。", 0.05)
sl("他的脸被金色的面具完全遮盖，只露出一双空洞的眼睛，", 0.05)
sl("面朝黄金树的方向。", 0.05)
sl("他周围的地面上刻满了复杂的符文，", 0.05)
sl("符文以他为中心向外辐射，像蛛网，又像星图。", 0.05)
print()
pause(0.7)

sl("金面具——黄金律法最虔诚的学者。", 0.05)
sl("他试图理解律法的全貌。但律法的全貌，是无法被理解的。", 0.05)
pause(0.4)
sl("于是他选择了沉默。", 0.06)
print()
pause(0.7)

sl("褪色者需要获得「黄金律法原本」，", 0.05)
sl("学会「回归性原理」，", 0.05)
sl("并在王城拉达冈雕像前使用该祷告。", 0.05)
print()
pause(0.6)

sl("当褪色者在拉达冈的雕像前跪下，", 0.05)
sl("金色的符文从经卷中浮现，在空中重新组合——", 0.05)
print()
pause(0.5)
sl("「拉达冈就是玛莉卡。」", 0.07)
print()
pause(0.8)

sl("真相像一把刀，剖开了黄金律法最核心的秘密。", 0.05)
print()
pause(0.5)

sl("褪色者回到金面具处，将这一真相告诉他。", 0.05)
pause(0.4)
sl("金面具第一次开口说话。", 0.05)
sl("他的声音像石头摩擦，像千年未动的门轴。", 0.05)
pause(0.4)
sl("金面具：「……原来如此。", 0.04)
sl("  黄金律法的全貌。", 0.04)
sl("  ……去吧。去告诉柯林。」", 0.04)
print()
pause(0.6)

sl("柯林在灰烬王城中找到金面具的遗体。", 0.05)
sl("金面具靠在悬崖边的石头上，", 0.05)
sl("身体已经完全被金色灰尘覆盖，像一尊真正的雕像。", 0.05)
pause(0.4)
sl("柯林跪下，双手合十。", 0.05)
pause(0.5)
sl("柯林：「老师……", 0.04)
sl("  我明白了。", 0.04)
sl("  黄金律法不是完美的。", 0.04)
sl("  但正因为不完美，才需要被修复。」", 0.04)
pause(0.5)
sl("他站起身，转向褪色者。", 0.05)
sl("他的脸上有一种褪色者从未见过的平静。", 0.05)
sl("柯林：「谢谢你。……请把这个拿去。」", 0.04)
print()
pause(0.6)

have_perfect_rune = True
order = order + 3
sl("▶ 秩序值 +3，获得「完美律法的修复卢恩」。", 0.04)
print()
pause(0.5)

sl("柯林在金面具的遗体旁坐下。", 0.05)
sl("他开始念诵。声音很低，像风穿过枯枝。", 0.05)
sl("那是黄金律法的经文。", 0.05)
sl("但这一次，他的念诵中多了一些东西——", 0.05)
sl("理解，而不是盲从。", 0.06)
print()
input("按回车继续……")


# ============================================================
# 第五幕 · 巨人山顶
# ============================================================
print()
bar()
sl("【第五幕 · 巨人山顶】", 0.06)
bar()
print()

sl("穿过王城罗德尔的后门，褪色者抵达了巨人山顶。", 0.05)
print()
pause(0.5)

sl("——那是交界地最寒冷的地方。", 0.06)
print()
pause(0.5)

sl("风雪漫天，能见度不足数步。", 0.05)
sl("脚下的积雪深及膝盖，每走一步都需要极大的力气。", 0.05)
sl("空气中弥漫着冰晶与灰烬混合的气味。", 0.05)
print()
pause(0.6)

sl("远处的雪山之巅，一团巨大的、暗红色的火焰正在燃烧。", 0.05)
sl("那是「灰灭火焰」——永不熄灭的火焰，", 0.05)
sl("只有它能点燃黄金树。", 0.05)
print()
pause(0.6)

sl("火焰大锅矗立在山顶的巨人遗骸之间。", 0.05)
sl("那些巨人早已死去，", 0.05)
sl("巨大的骸骨半埋在雪中，像白色的山丘。", 0.05)
print()
pause(0.6)

sl("巨人山顶——被诅咒的土地。", 0.05)
sl("曾经，火焰巨人们在这里守护着灰灭火焰。", 0.05)
sl("但黄金律法降临后，他们被屠杀殆尽。", 0.05)
pause(0.4)
sl("只有那团火焰，还在这里燃烧。", 0.06)
print()
pause(0.6)


# ---- 巨人山顶 · 风雪中的信件 ----
sl("火焰大锅前的雪地上，躺着一位早已冻僵的褪色者。", 0.05)
sl("他的铠甲上覆盖着冰霜，手指已经和信纸冻在了一起。", 0.05)
sl("他手中紧握着一封未寄出的信。", 0.05)
print()
pause(0.5)
sl("[1] 拾起信件。", 0.01)
sl("[2] 让他安息。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你小心地掰开他的手指，取出信件。", 0.05)
    sl("信上写着：", 0.05)
    pause(0.4)
    sl("「如果你也走到了这里——", 0.05)
    sl("  不要相信任何人。黄金树不会回答你。", 0.05)
    sl("  但你可以选择自己的结局。」", 0.05)
    pause(0.5)
    sl("▶ 你在风雪中感到一丝清醒。", 0.04)
    if frenzy > 0:
        frenzy -= 1
        sl("  癫火值 -1。", 0.04)
else:
    sl("你用手把雪盖在他身上。", 0.05)
    sl("他握着信的手慢慢被雪埋住。", 0.05)
    sl("▶ 你感到一种奇怪的平静。秩序值 +1。", 0.04)
    order += 1
print()
input("按回车继续……")


# ---- 火焰巨人战 ----
def fire_giant_special(hp, max_hp):
    """
    火焰巨人：
      每 4 回合一次踩踏（高伤）
      血量低于 50% → 灰灭火焰治疗
    """
    if not hasattr(fire_giant_special, "turn"):
        fire_giant_special.turn = 0
    fire_giant_special.turn += 1

    if fire_giant_special.turn % 4 == 0:
        return True, "火焰巨人抬起那只燃烧的巨脚，向你踩下——", "damage_boost"
    if hp < max_hp * 0.5 and fire_giant_special.turn % 3 == 0:
        return True, "火焰巨人胸口的灰灭火焰猛地窜出，笼罩了全身。", "heal"
    return False, "", ""


sl("火焰大锅前，最后一位火焰巨人从雪地中站起。", 0.05)
sl("他的身体比雪山还要高大，一只脚上燃烧着灰灭火焰。", 0.05)
sl("他的脸上没有表情——只有一种古老的、被诅咒的沉默。", 0.05)
print()
pause(0.6)

win = False
while not win:
    if hasattr(fire_giant_special, "turn"):
        del fire_giant_special.turn

    win = battle(
        "火焰巨人", 300, 19,
        intro_lines=[
            "火焰巨人从雪地中站起，脚下的积雪被烧成蒸汽。",
            "他的胸口涌动着灰灭火焰。"
        ],
        win_lines=[
            "火焰巨人跪倒在雪地中，身体开始崩解。",
            "灰灭火焰从他体内涌出，融入大锅。",
            "他的身体化为灰烬，被风吹散在雪山之巅。"
        ],
        special=fire_giant_special
    )

player_hp = player_max_hp
player_fp = player_max_fp
fill_flask()
player_atk += 2
max_flask += 1

# 学会「灰灭燃焰」
skills.append({
    "name": "灰灭燃焰", "cost": 15, "type": "burn",
    "lo": 9, "hi": 12,
    "desc": "火焰斩击。敌人燃烧 3 回合，每回合受 20 伤害。"
})

print()
sl("▶ 火焰巨人倒下。攻击力 +2，圣杯瓶上限 +1，HP/FP/瓶已恢复。", 0.04)
sl("▶ 领悟战技「灰灭燃焰」——伤害 + 敌人燃烧 3 回合，每回合 20 伤。", 0.04)
print()
input("按回车继续……")


# ============================================================
# 第五幕 · 烧树
# ============================================================
sl("褪色者爬上大锅边缘。", 0.05)
sl("锅中的火焰是暗红色的，没有温度，", 0.05)
sl("却让人感到一种深入骨髓的寒冷。", 0.05)
print()
pause(0.6)

sl("梅琳娜站在赐福旁。", 0.05)
sl("她的斗篷被风吹得猎猎作响，", 0.05)
sl("兜帽下露出那张苍白而平静的面孔。", 0.05)
sl("她的左眼依然紧闭，", 0.05)
sl("右眼中的金色光芒比以往任何时候都要明亮。", 0.05)
print()
pause(0.7)

sl("梅琳娜：「你做好犯下重罪的心理准备了吗？」", 0.04)
pause(0.5)
sl("她的声音很平静。", 0.05)
sl("但褪色者注意到，她握着斗篷边缘的手指微微发白。", 0.05)
print()
pause(0.5)
sl("[1] 「我准备好了。」——让梅琳娜自焚。", 0.01)
sl("[2] 「不。」——拒绝。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "2":
    sl("无法推进。只有烧树才能打开前路。", 0.05)
    sl("梅琳娜在风雪中站了很久。", 0.05)
    sl("[1] 「我准备好了。」", 0.01)
    input("> ")
    print()

sl("梅琳娜：「……黄金树啊，燃烧吧。", 0.04)
sl("  为了新王……」", 0.04)
pause(0.6)
sl("她走向大锅边缘。", 0.05)
sl("灰灭火焰从锅中升起，舔舐着她的斗篷。", 0.05)
pause(0.5)
sl("她转过头，最后一次看向褪色者。", 0.05)
sl("那只黯淡的金色眼睛——", 0.05)
sl("第一次，也是最后一次——闪过了黄金树的光芒。", 0.05)
pause(0.6)
sl("梅琳娜：「再会了，褪色者。", 0.04)
sl("  愿你能成为艾尔登之王。」", 0.04)
pause(0.6)
sl("她张开双臂。灰灭火焰吞没了她瘦小的身影。", 0.06)
sl("斗篷在火焰中化为灰烬，升入夜空。", 0.06)
pause(0.6)
sl("大锅中的火焰猛然腾起，", 0.05)
sl("一道暗红色的光柱直冲云霄，刺穿了巨人山顶的云层。", 0.05)
sl("远处，黄金树开始燃烧。", 0.06)
pause(0.6)
melina_alive = False
print()
pause(0.5)
sl("那一夜，巨人山顶的雪停了。", 0.05)
sl("灰灭火焰的热浪融化了千年的积雪，", 0.05)
sl("露出下面被冰封的巨人骸骨。", 0.05)
pause(0.4)
sl("而在火焰之中，褪色者感到了一种前所未有的孤独。", 0.06)
print()
input("按回车继续……")


# ============================================================
# 第五幕 · 三指与癫火
# ============================================================
print()
bar()
sl("【王城下水道 · 三指与癫火】", 0.06)
bar()
print()

sl("褪色者在弃置噩兆的底层找到了一扇熔烧的门。", 0.05)
sl("门上覆盖着一层活着的火焰——", 0.05)
sl("那火焰没有温度，却在不断蠕动，", 0.05)
sl("像某种生物的皮肤。", 0.05)
print()
pause(0.5)

sl("盲眼女巫海妲跪在门前。", 0.05)
sl("她的眼睛被一层白色的膜覆盖，", 0.05)
sl("但她准确地转向褪色者的方向。", 0.05)
print()
pause(0.5)
sl("海妲：「你来了。", 0.04)
sl("  ……三指在等你。脱下所有防具吧。", 0.04)
sl("  三指不接受任何……遮蔽。」", 0.04)
print()
pause(0.5)
sl("[1] 询问海妲：三指究竟是什么？", 0.01)
sl("[2] 沉默走向熔烧的门。", 0.01)
sl("[3] 转身离开。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2", "3"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("海妲沉默了片刻。", 0.05)
    pause(0.4)
    sl("海妲：「三指……是癫火的化身。", 0.04)
    sl("  它想烧尽一切差异。", 0.04)
    sl("  秩序、生命、痛苦——全部归于混沌。", 0.04)
    sl("  你还要接受它吗？」", 0.04)
    print()
    pause(0.5)
    sl("[1] 接受三指烙印。", 0.01)
    sl("[2] 转身离开。", 0.01)
    sub = input("> ").strip()
    while sub not in ("1", "2"):
        sl("无效输入，请重新选择。", 0.03)
        sub = input("> ").strip()
    print()
    if sub == "1":
        choice = "1"
    else:
        choice = "3"

# ---- 处理最终选择 ----
if choice == "1":
    frenzy = frenzy + 5
    sl("褪色者脱下全部防具。", 0.05)
    sl("铠甲、头盔、护手、靴子——", 0.05)
    sl("一件件落在石地上，发出沉闷的响声。", 0.05)
    pause(0.5)
    sl("褪色者推开熔烧的门。", 0.05)
    pause(0.5)
    sl("门后是一片无尽的黑暗。", 0.05)
    sl("但在黑暗中，有一只巨大的、畸形的三指从阴影中伸出。", 0.05)
    sl("它的每一根手指都是一条独立的、蠕动的肢体，", 0.05)
    sl("上面覆盖着密密麻麻的眼睛。", 0.05)
    print()
    pause(0.6)
    sl("三指拥抱了褪色者。", 0.05)
    sl("那些眼睛同时睁开，看向褪色者。", 0.05)
    pause(0.5)
    sl("癫火烙印出现在褪色者的身体上。", 0.05)
    sl("金色光芒从眼中彻底消失。", 0.05)
    print()
    pause(0.6)
    sl("当褪色者回到赐福处时，梅琳娜坐在那里。", 0.05)
    sl("她的表情前所未有地平静——", 0.05)
    sl("一种比愤怒更可怕的东西。", 0.05)
    pause(0.5)
    sl("梅琳娜：「你……接受了癫火。」", 0.04)
    pause(0.4)
    sl("她站起身，向后退了一步。", 0.05)
    sl("梅琳娜：「那么，我们的约定到此为止。」", 0.04)
    pause(0.4)
    sl("她的声音很轻，但每一个字都像石头落入深水。", 0.05)
    sl("梅琳娜：「如果你成为癫火之王，我会亲手杀了你。", 0.04)
    sl("  无论你在哪里，无论你变成什么。」", 0.04)
    pause(0.5)
    sl("她转身，消失在赐福的光芒中。", 0.05)
    sl("此后，梅琳娜不会再出现在任何赐福处。", 0.05)
    melina_alive = False
    print()
    pause(0.6)
    sl("▶ 癫火值 +5（阈值突破）。", 0.04)
    sl("  所有其他结局路线被锁定，", 0.04)
    sl("  除非在天空城使用米凯拉的金针净化。", 0.04)
    print()
    pause(0.5)
    sl("那一夜，褪色者在赐福旁坐了很久。", 0.05)
    sl("癫火烙印在皮肤下隐隐作痛，", 0.05)
    sl("像是有什么东西正在里面生长。", 0.05)
    sl("而在远方，黄金树依然在燃烧。", 0.06)
else:
    sl("你转身离开。门上的火焰缓缓蠕动，像在呼吸。", 0.05)
    sl("海妲在身后低声说：「……那也是一种选择。」", 0.05)
print()
input("按回车继续……")


# ============================================================
# 第六幕 · 天空城
# ============================================================
print()
bar()
sl("【第六幕 · 法姆·亚兹拉】", 0.06)
bar()
print()

sl("烧树后，褪色者被传送到 法姆·亚兹拉。", 0.05)
print()
pause(0.5)

sl("——那是漂浮在时空裂隙中的古城。", 0.06)
print()
pause(0.5)

sl("整座城市悬浮在一片混沌的虚空之上。", 0.05)
sl("虚空中有无数破碎的建筑、倒悬的山脉、", 0.05)
sl("以及缓慢旋转的星辰碎片。", 0.05)
sl("天空是暗紫色的，偶尔闪过一阵金色的闪电。", 0.05)
print()
pause(0.6)

sl("城市的建筑风格古老而陌生。", 0.05)
sl("墙壁上刻着与诺克隆恩相同的文字，但规模更加宏大。", 0.05)
sl("巨大的龙尸横陈在街道上，", 0.05)
sl("有些已经化为白骨，有些还残留着干枯的皮肉。", 0.05)
print()
pause(0.6)

sl("空气中弥漫着一种陈旧的、像陨石与灰烬混合的气味。", 0.05)
print()
pause(0.5)

sl("法姆·亚兹拉——天空之城。", 0.05)
sl("在黄金律法降临之前，这里曾是龙的故乡。", 0.05)
sl("古龙们在这里统治着交界地的天空。", 0.05)
pause(0.4)
sl("然后，黄金律法来了。龙的时代结束了。", 0.05)
sl("但这座城……依然漂浮在时空的裂隙中，等待着什么。", 0.06)
print()
pause(0.7)


# ---- 天空城 · 龙王遗骸岔路 ----
sl("天空城的一处断裂平台上，横陈着一具巨大的龙骸。", 0.05)
sl("鳞片已经失去光泽，但骨架依然保持着飞行的姿态。", 0.05)
sl("风穿过骨骼的空隙，发出类似长笛的声音。", 0.05)
print()
pause(0.5)
sl("[1] 从龙骸上取下鳞片。", 0.01)
sl("[2] 在龙骸前静立片刻。", 0.01)
choice = input("> ").strip()
while choice not in ("1", "2"):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
print()

if choice == "1":
    sl("你取下一枚暗金色的龙鳞。它依然温热。", 0.05)
    sl("鳞片在你手中微微发光，仿佛还带着古龙最后的呼吸。", 0.05)
    player_max_hp += 20
    player_hp += 20
    sl("▶ 获得「古龙的鳞片」——最大 HP +20。", 0.04)
else:
    sl("你站在龙骸前。风穿过骨骼，发出类似长笛的声音。", 0.05)
    sl("那一刻，你仿佛听见了古龙时代最后的回响。", 0.05)
    stars += 1
    sl("▶ 星辰值 +1。", 0.04)
print()
input("按回车继续……")


# ---- 黑剑玛利喀斯战 ----
def maliketh_special(hp, max_hp):
    """
    玛利喀斯：
      每 3 回合命定之死（削减玩家上限）
      血量低于 50% → 每 5 回合黑剑燃焰（高伤）
    """
    if not hasattr(maliketh_special, "turn"):
        maliketh_special.turn = 0
    maliketh_special.turn += 1

    if maliketh_special.turn % 3 == 0:
        return True, "玛利喀斯跃起，黑剑上命定之死的光芒斩落——", "curse"
    if maliketh_special.turn % 5 == 0 and hp < max_hp * 0.5:
        return True, "玛利喀斯的黑剑燃起暗红色的火焰，剑势骤然凌厉——", "damage_boost"
    return False, "", ""


sl("在天空城的最深处，褪色者面对「黑剑」玛利喀斯。", 0.05)
print()
pause(0.5)

sl("他是一条巨大的黑色野兽，身形如狼，鳞片如铠甲。", 0.05)
sl("他的手中握着一把黑色长剑——", 0.05)
sl("那剑身上流淌着暗红色的光芒，像凝固的血液。", 0.05)
print()
pause(0.5)

sl("玛利喀斯：「渴望接近命定之死的人啊。", 0.04)
sl("  我不会让它失窃第二次。」", 0.04)
print()
pause(0.6)

win = False
while not win:
    if hasattr(maliketh_special, "turn"):
        del maliketh_special.turn

    win = battle(
        "黑剑 玛利喀斯", 350, 22,
        intro_lines=[
            "玛利喀斯跃上石桥，黑剑在虚空中划出一道暗红的弧线。",
            "「命定之死，不是你能触碰的东西。」"
        ],
        win_lines=[
            "玛利喀斯跪倒在地。黑剑从手中滑落，在石地上发出清脆的响声。",
            "「……玛莉卡……我……失败了……」",
            "他的身体化为黑色的光点，消散在虚空中。",
            "死亡卢恩被释放。远处，灰烬王城中的黄金树开始彻底崩塌。"
        ],
        special=maliketh_special
    )

player_hp = player_max_hp
player_fp = player_max_fp
fill_flask()
player_atk += 3
max_flask += 1

# 学会「命定之死」
skills.append({
    "name": "命定之死", "cost": 25, "type": "reduce_max",
    "lo": 50, "hi": 50,
    "desc": "削去敌人生命上限 50（本战内）。使用后仍可行动。"
})

print()
sl("▶ 命定之死已被释放。攻击力 +3，圣杯瓶上限 +1，HP/FP/瓶已恢复。", 0.04)
sl("▶ 领悟战技「命定之死」——削减敌人最大 HP 50（本战内）。", 0.04)
print()
input("按回车继续……")


# ---- 龙王与金针（仅癫火状态下）----
if frenzy >= 5:
    print()
    sl("在天空城深处的漩涡中，", 0.05)
    sl("龙王普拉顿桑克斯竞技场悬浮在时空裂隙之上。", 0.05)
    print()
    pause(0.5)

    sl("——那是时空的源头。", 0.05)
    sl("漩涡中翻滚着无数破碎的画面：", 0.05)
    sl("古老的战场、燃烧的城市、跪在王座前的人群。", 0.05)
    print()
    pause(0.6)

    sl("龙王普拉顿桑克斯盘踞在漩涡中央。", 0.05)
    sl("他的身体巨大而古老，", 0.05)
    sl("鳞片上刻满了已经失传的文字。", 0.05)
    sl("他的双眼是金色的，像两颗燃烧的太阳。", 0.05)
    print()
    pause(0.6)

    sl("你取出「米凯拉的金针」。", 0.05)
    sl("金针在癫火烙印前微微发光，像是在等待你的决定。", 0.05)
    print()
    pause(0.4)
    sl("[1] 使用金针，净化癫火。", 0.01)
    sl("[2] 保留癫火。", 0.01)
    choice = input("> ").strip()
    while choice not in ("1", "2"):
        sl("无效输入，请重新选择。", 0.03)
        choice = input("> ").strip()
    print()

    if choice == "1":
        sl("褪色者将金针刺入癫火烙印。", 0.05)
        sl("金色的光芒从针尖涌出，", 0.05)
        sl("与暗红色的癫火在体内交战。", 0.05)
        pause(0.5)
        sl("剧痛。像是身体被从内部撕开。", 0.05)
        pause(0.6)
        sl("然后，癫火烙印消失了。", 0.05)
        sl("金色光芒重新回到眼中。", 0.05)
        print()
        pause(0.5)
        frenzy = 0
        gold_needle_used = True
        sl("▶ 癫火归零。结局开放了……", 0.04)
    else:
        sl("褪色者收起金针。", 0.05)
        sl("癫火烙印继续在体内燃烧。", 0.05)
        print()
        pause(0.5)
        sl("▶ 癫火维持。癫火之王似乎已经成为了命中注定。", 0.04)
    print()
    input("按回车继续……")


# ============================================================
# 终幕 · 灰烬王城
# ============================================================
print()
bar()
sl("【终幕 · 灰烬王城】", 0.06)
bar()
print()

sl("灰烬王城。黄金树内部。", 0.05)
print()
pause(0.5)

sl("——那是一个巨大的、由金色枝干构成的空间。", 0.05)
sl("空气中弥漫着浓郁的、像蜜与铁锈混合的气味。", 0.05)
sl("墙壁上流淌着金色的光芒，像血管，像河流。", 0.05)
print()
pause(0.6)

sl("拉达冈挡在濒毁的玛莉卡石像前。", 0.05)
print()
pause(0.5)

sl("他是一名红发的高大战士，身披金色的铠甲，", 0.05)
sl("手中握着一把巨大的锤子。", 0.05)
sl("他的面容与玛莉卡极其相似，", 0.05)
sl("但线条更加粗犷，像同一个人被雕成了不同的形态。", 0.05)
sl("他的眼睛是金色的，但其中没有意志。", 0.05)
sl("像是一具被操控的躯壳。", 0.05)
print()
pause(0.6)

sl("拉达冈——黄金律法的化身。", 0.05)
sl("他是玛莉卡的另一个自我。", 0.05)
sl("是黄金律法为了维持自身而创造的工具。", 0.05)
pause(0.4)
sl("他没有意志，没有欲望。他只是一个……律法的容器。", 0.06)
print()
pause(0.7)


# ---- 第一阶段：拉达冈 ----
def radagon_special(hp, max_hp):
    """
    拉达冈：
      每 2 回合律法回复
      每 3 回合黄金冲击波
    """
    if not hasattr(radagon_special, "turn"):
        radagon_special.turn = 0
    radagon_special.turn += 1

    if radagon_special.turn % 2 == 0:
        return True, "拉达冈高举锤子，黄金律法的光辉笼罩全身。", "heal"
    if radagon_special.turn % 3 == 0:
        return True, "拉达冈将锤子砸向地面，金色的冲击波扩散开来——", "damage_boost"
    return False, "", ""


win = False
while not win:
    if hasattr(radagon_special, "turn"):
        del radagon_special.turn

    win = battle(
        "黄金律法 拉达冈", 400, 20,
        intro_lines=[
            "拉达冈举起锤子。金色的光芒在锤头上凝聚。",
            "——他没有说话。律法的容器不需要言语。"
        ],
        win_lines=[
            "拉达冈跪倒在地。铠甲碎裂，露出金色的、像树皮一样的皮肤。",
            "他的身体开始崩解，金色的碎片从体内涌出，向天空升去。"
        ],
        special=radagon_special
    )

print()
pause(0.6)


print()
pause(0.6)

# 学会「黄金祷言」（两阶段连战，给一个治疗战技作为补偿）
skills.append({
    "name": "黄金祷言", "cost": 15, "type": "heal",
    "lo": 75, "hi": 75,
    "desc": "恢复自身 75 HP。使用后仍可行动。"
})
sl("▶ 领悟战技「黄金祷言」——恢复自身 75 HP。", 0.04)
# sl(f"  黄金树的光芒短暂治疗了你。▶ 恢复 {int(player_max_hp*0.8)}HP , 30 FP ")
# player_hp = min(player_max_hp,int(player_hp + (player_max_hp * 0.8)))
# player_fp = min(player_max_fp,int(player_fp + 30))
print()
pause(0.5)

# ---- 阶段过渡：不回血，直接进入第二阶段 ----
sl("但他的身体崩解到一半时——", 0.05)



pause(0.5)
sl("艾尔登之兽从拉达冈的躯体内显现。", 0.06)
print()
pause(0.6)

sl("——一头由金色光斑构成的、形如星辰巨兽的存在。", 0.05)
sl("它的身体如同一团旋转的星云，", 0.05)
sl("其中闪烁着无数古老的符文。", 0.05)
sl("它的「头」是一个巨大的、发光的球体，像一颗微型的太阳。", 0.05)
print()
pause(0.6)

sl("艾尔登之兽——黄金律法的真正形态。", 0.05)
sl("它是无上意志投向交界地的一颗流星。", 0.05)
sl("是黄金律法的根基与牢笼。", 0.05)
pause(0.4)
sl("击败它，才能真正获得艾尔登法环。", 0.06)
print()
pause(0.7)

sl("▶ 拉达冈的崩解让你喘了口气。", 0.04)
print()
pause(0.5)


# ---- 第二阶段：艾尔登之兽 ----
def elden_beast_special(hp, max_hp):
    """
    艾尔登之兽：
      每 3 回合光柱
      每 5 回合星辰重压（削弱）
      血量低于 40% → 每 7 回合星云治疗
    """
    if not hasattr(elden_beast_special, "turn"):
        elden_beast_special.turn = 0
    elden_beast_special.turn += 1

    if elden_beast_special.turn % 3 == 0:
        return True, "艾尔登之兽核心凝聚，金色光柱贯穿虚空——", "damage_boost"
    if elden_beast_special.turn % 5 == 0:
        return True, "星辰的重压碾过你的身体，你的力量在消退……", "weaken"
    if elden_beast_special.turn % 7 == 0 and hp < max_hp * 0.4:
        return True, "艾尔登之兽的星云旋转起来，无数古老的符文涌入它的核心。", "heal"
    return False, "", ""


win = False
while not win:
    if hasattr(elden_beast_special, "turn"):
        del elden_beast_special.turn

    win = battle(
        "艾尔登之兽", 500, 23,
        intro_lines=[
            "艾尔登之兽在虚空中穿梭，每一次攻击都带着星辰的力量。",
            "金色的光柱从它体内射出，击碎了周围的枝干。"
        ],
        win_lines=[
            "最终一击。艾尔登之兽的核心碎裂。",
            "金色的光斑向四面八方飞散。",
            "它消失了。",
            "艾尔登法环——完整地，悬浮在虚空中。"
        ],
        special=elden_beast_special
    )

print()
pause(0.7)

sl("褪色者走向玛莉卡的石像。", 0.05)
sl("石像已经严重破损，", 0.05)
sl("只剩下上半身还依稀可辨。", 0.05)
sl("玛莉卡的面容在石像上显得疲惫而平静，", 0.05)
sl("像一位终于可以休息的母亲。", 0.05)
pause(0.5)
sl("石像前，缺失着什么。", 0.06)
print()
pause(0.8)


# ============================================================
# 结局判定
# ============================================================
double_bar()
sl(f"当前状态：秩序 {order} ／ 星辰 {stars} ／ 癫火 {frenzy}", 0.05)
double_bar()
print()
pause(0.6)

available = []

if frenzy >= 5 and not gold_needle_used:
    available = ["癫火之王"]
else:
    if have_perfect_rune:
        available.append("放置「完美律法的修复卢恩」")
    if have_death_rune:
        available.append("放置「死王子的修复卢恩」")
    if have_dung_rune:
        available.append("放置「忌讳诅咒的修复卢恩」")
    if stars >= 5 and ranni_route:
        available.append("召唤菈妮")
    available.append("不放置 大卢恩")

sl("可放置的大卢恩：", 0.04)
for i, name in enumerate(available, 1):
    color = ENDING_COLORS.get(name, C_RESET)
    print(f"  [{i}] {color}{name}{C_RESET}")
print()
choice = input("> ").strip()
while not (choice.isdigit() and 1 <= int(choice) <= len(available)):
    sl("无效输入，请重新选择。", 0.03)
    choice = input("> ").strip()
pick = available[int(choice) - 1]
print()

double_bar()

# ---- 律法时代 ----
if pick == "放置「完美律法的修复卢恩」":
    print(f"{C_YELLOW}【律法时代】{C_RESET}")
    print()
    pause(0.5)
    sl("褪色者使用完美律法的修复卢恩。", 0.05)
    sl("金色的符文从褪色者手中流出，", 0.05)
    sl("重新编织艾尔登法环的纹路。", 0.05)
    sl("裂痕被一种冷静的、精确的力量填补。", 0.05)
    sl("法环上的光芒变得清澈，", 0.05)
    sl("不再是盲目的金色，而是带着一种理性的、被理解的光辉。", 0.05)
    print()
    pause(0.7)
    sl("黄金律法被重新定义。", 0.06)
    sl("它不再是盲目的永恒，", 0.05)
    sl("而是一种被理解、被选择的秩序。", 0.05)
    pause(0.6)
    sl("柯林的遗愿，金面具的沉默，在这一刻得到了回答。", 0.05)
    pause(0.5)
    sl("交界地迎来了一个……被思考过的时代。", 0.06)

# ---- 潜藏者当道的时代 ----
elif pick == "放置「死王子的修复卢恩」":
    print(f"{C_BLUE}【潜藏者当道的时代】{C_RESET}")
    print()
    pause(0.5)
    sl("褪色者使用死王子的修复卢恩。", 0.05)
    sl("黑色的、如同深海般的光芒融入法环。", 0.05)
    sl("那些曾经被黄金律法排斥在外的死诞者，", 0.05)
    sl("第一次被纳入了律法的庇护之下。", 0.05)
    print()
    pause(0.7)
    sl("葛德文的死，第一次被黄金律法所容纳。", 0.05)
    sl("死亡不再是需要被消灭的东西，而是生命的一部分。", 0.05)
    pause(0.6)
    sl("死诞者们站在了阳光下。", 0.05)
    sl("他们的存在，不再是诅咒。", 0.05)
    pause(0.5)
    sl("交界地迎来了一个……完整的时代。", 0.06)

# ---- 绝望赐福时代 ----
elif pick == "放置「忌讳诅咒的修复卢恩」":
    print(f"{C_PURPLE}【绝望赐福时代】{C_RESET}")
    print()
    pause(0.5)
    sl("褪色者使用忌讳诅咒的修复卢恩。", 0.05)
    sl("暗红色的污浊从法环内部涌出，", 0.05)
    sl("浸染了金色的光芒。", 0.05)
    sl("法环的纹路扭曲，像一张被揉皱的脸。", 0.05)
    print()
    pause(0.7)
    sl("食粪者的诅咒融入了黄金律法。", 0.05)
    sl("这是一个连绝望都被赐福的世界。", 0.05)
    pause(0.6)
    sl("没有人再需要挣扎。", 0.05)
    sl("因为挣扎本身，已经被赐福所包含。", 0.05)
    pause(0.5)
    sl("交界地迎来了一个……终结的时代。", 0.06)

# ---- 星星时代 ----
elif pick == "召唤菈妮":
    print(f"{C_CYAN}【星星时代】{C_RESET}")
    print()

    pause(0.5)
    sl("褪色者在最终战场景的地面上点击蓝色召唤符。", 0.05)
    sl("菈妮的身影从暗月的辉光中显现。", 0.05)
    sl("她不再是四只手臂的人偶，", 0.05)
    sl("而是一个真正的、由星光构成的存在。", 0.05)
    sl("她的长发如夜空般深蓝，眼中映着无数星辰。", 0.05)
    print()
    pause(0.7)

    if stars >= 7:
        sl("*额外对话已触发(星辰值 >= 7)",0.04)
        sl("菈妮：「我曾以为，这条路上只有我一人。", 0.04)
        sl("  你从艾雷教堂的那个夜晚起，", 0.04)
        sl("  就一直在我的棋局之中——", 0.04)
        sl("  但如今，我愿将棋局之外的一切，也交予你。」", 0.04)
    else:
        sl("菈妮：「……你来了。", 0.04)
        sl("  群星的律法，将由我等共同书写。", 0.04)
        sl("  走吧，我的王。」", 0.04)

    print()
    pause(0.7)
    sl("她伸出手。", 0.05)
    sl("暗月大剑的蓝光映照着两颗远离交界地的星辰。", 0.05)
    print()
    pause(0.5)
    sl("褪色者握住她的手。", 0.05)
    sl("两人的身影开始上升，", 0.05)
    sl("穿过黄金树的穹顶，穿过云层，穿过大气，", 0.05)
    sl("进入深蓝色的、布满星辰的夜空。", 0.05)
    print()
    pause(0.7)
    sl("黄金树的光芒在下方逐渐变小，", 0.05)
    sl("最终成为一颗普通的、微弱的星。", 0.05)
    print()
    pause(0.6)
    sl("黄金律法被抛弃了。", 0.05)
    sl("群星的律法——冰冷、遥远、不可确信——", 0.05)
    sl("成为了新的秩序。", 0.05)
    pause(0.5)
    sl("褪色者与菈妮一同离开交界地，走向夜空深处。", 0.05)
    sl("在那里，在无数星辰之间，他们将书写新的律法。", 0.05)
    sl("一个没有黄金树、没有双指、没有无上意志的律法。", 0.05)
    pause(0.5)
    sl("一个属于他们自己的……时代。", 0.06)

# ---- 癫火之王 ----
elif pick == "癫火之王":
    print(f"{C_YELLOW}【癫火之王】{C_RESET}")
    print()

    pause(0.5)
    sl("褪色者的头部裂开。", 0.05)
    sl("癫火从眼眶、口中、耳中涌出。", 0.05)
    sl("黄色火焰吞噬了一切。", 0.05)
    print()
    pause(0.6)
    sl("黄金树燃烧。王城崩塌。大地龟裂。", 0.05)
    pause(0.5)
    sl("一切差异、一切秩序、一切痛苦，", 0.05)
    sl("都在混沌中消融。", 0.05)
    print()
    pause(0.7)
    sl("癫火之王诞生了。", 0.06)
    sl("交界地化为灰烬。", 0.05)
    pause(0.5)
    sl("没有生，没有死。没有王，没有臣。", 0.05)
    sl("没有律法，没有罪。", 0.05)
    pause(0.5)
    sl("只有……混沌。", 0.07)
    print()
    pause(0.8)

    if not melina_alive:
        sl("灰烬中，一个身影出现。", 0.05)
        sl("梅琳娜斗篷破烂，", 0.05)
        sl("右眼中的金色光芒依然明亮。", 0.05)
        sl("她手中握着一把褪色的、布满裂痕的短剑。", 0.05)
        pause(0.6)
        sl("梅琳娜：「我说过，我会亲手杀了你。", 0.04)
        sl("  ……无论你在哪里。", 0.04)
        sl("  无论你变成什么。」", 0.04)
        pause(0.6)
        sl("她转身走进灰烬中。", 0.05)
        print()
        pause(0.6)
        sl("屏幕变黑。", 0.05)
        pause(0.5)
        sl("交界地……没有了。", 0.08)

# ---- 衰颓时代 ----
else:
    print(f"{C_GRAY}【衰颓时代】{C_RESET}")
    print()
    pause(0.5)
    sl("褪色者触碰玛莉卡石像。", 0.05)
    sl("没有使用任何修复卢恩。", 0.05)
    print()
    pause(0.5)
    sl("艾尔登法环被重新拼凑，", 0.05)
    sl("但裂痕依然清晰可见。", 0.05)
    sl("金色的光芒从法环中流出，注入玛莉卡的石像。", 0.05)
    sl("石像开始缓慢地修复，", 0.05)
    sl("但那些裂痕——那些深深嵌入律法根基的裂痕——依然存在。", 0.05)
    print()
    pause(0.7)
    sl("褪色者成为了艾尔登之王。", 0.06)
    sl("但修复的法环无法掩盖裂痕。", 0.05)
    sl("交界地继续在缓慢的腐朽中存在。", 0.05)
    pause(0.6)
    sl("死诞者依然游荡，黄金树的赐福依然在消退。", 0.05)
    pause(0.5)
    sl("这是一个……没有终点的时代。", 0.06)

double_bar()
print()
sl("游戏结束。", 0.08)
print()
sl("Tips:不同的选项会有不同结局", 0.08)
print()
input("任意键以退出...")

#Oct.4th
#radahn unedited DONE
#curse unedited Done
#boss unedited
#text needing enrich
#battle sys needing change
#tears

#Oct 13rd
#bottle！！
#battle?
#text
#value

#Bug
#  1     global enemy_max_hp 位置
#   2     mimic_tear 逻辑
#   3     enemy_vulnerable 死变量
#   4     拉塔恩战后 max_flask += 1
#   5     weaken 永久削攻击力
#   6     telegraph 回合 defend_next 是否延续
#   7     速度菜单失效
#   8     黄金祷言注释误导