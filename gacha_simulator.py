import random
import datetime
import os

BASE_RATES = {
    "六星": 2.0,
    "五星": 8.0,
    "四星": 50.0,
    "三星": 40.0,
}

def get_rates_with_pity(no_six_count):
    """根据当前未出六星次数计算每个星级概率。"""
    six_rate = BASE_RATES["六星"]
    if no_six_count > 50:
        increase = 2.0 * (no_six_count - 50)
        six_rate += increase
    six_rate = min(six_rate, 100.0)

    remaining = max(100.0 - six_rate, 0.0)
    if remaining <= 0:
        return {"六星": 100.0, "五星": 0.0, "四星": 0.0, "三星": 0.0}

    other_total = BASE_RATES["五星"] + BASE_RATES["四星"] + BASE_RATES["三星"]
    return {
        "六星": six_rate,
        "五星": remaining * (BASE_RATES["五星"] / other_total),
        "四星": remaining * (BASE_RATES["四星"] / other_total),
        "三星": remaining * (BASE_RATES["三星"] / other_total),
    }


def draw_single(no_six_count):
    rates = get_rates_with_pity(no_six_count)
    r = random.random() * 100
    cumulative = 0.0
    for star in ["六星", "五星", "四星", "三星"]:
        cumulative += rates[star]
        if r < cumulative:
            return star
    return "三星"


def format_star_line(star, is_up):
    symbols = {
        "六星": "⭐⭐⭐⭐⭐⭐",
        "五星": "⭐⭐⭐⭐⭐",
        "四星": "⭐⭐⭐⭐",
        "三星": "⭐⭐⭐",
    }
    up_text = "（UP）" if (star == "六星" and is_up) else ""
    return f"{symbols.get(star, star)} {star}{up_text}"


def simulate(total_draws):
    counts = {"六星": 0, "六星(UP)": 0, "六星(非UP)": 0, "五星": 0, "四星": 0, "三星": 0}
    no_six_counter = 0
    no_up_six_streak = 0
    draw_results = []

    for i in range(total_draws):
        star = draw_single(no_six_counter + 1)
        is_up = False

        if star == "六星":
            counts["六星"] += 1
            if no_up_six_streak >= 2:
                is_up = True
            else:
                is_up = random.random() < 0.5

            if is_up:
                counts["六星(UP)"] += 1
                no_up_six_streak = 0
            else:
                counts["六星(非UP)"] += 1
                no_up_six_streak += 1

            no_six_counter = 0
        else:
            counts[star] += 1
            no_six_counter += 1

        draw_results.append((star, is_up))

    return counts, draw_results


def save_record(mode, n, counts, avg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"{timestamp}|{mode}|{n}|{counts['六星']}|{counts['五星']}|{counts['四星']}|{counts['三星']}|{avg:.2f}\n"
    with open("gacha_history.txt", "a", encoding="utf-8") as f:
        f.write(record)


def view_records():
    if not os.path.exists("gacha_history.txt"):
        print("暂无抽卡记录。")
        return
    with open("gacha_history.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        print("暂无抽卡记录。")
        return
    print("\n抽卡历史记录（最近10条）：")
    for line in lines[-10:]:
        parts = line.strip().split("|")
        if len(parts) == 8:
            ts, mode, n, six, five, four, three, avg = parts
            mode_name = "单抽" if mode == "1" else "十连"
            print(f"{ts} | {mode_name} {n}次 | 六星:{six} 五星:{five} 四星:{four} 三星:{three} | 平均:{avg}")
    print()


def main():
    print("抽卡模拟器：六星2%、五星8%、四星50%、三星40%；超过50次未出六星后，每次六星概率+2%（其他按权重缩减）。")
    print("六星出货时，UP六星占六星的50%；若连续两次六星非UP，则下一次六星必为UP。")

    while True:
        mode = input("请选择模式（1=单抽, 2=十连抽, 3=查看记录, q=退出）：").strip()
        if mode == "q":
            print("退出。")
            return
        if mode == "3":
            view_records()
            continue
        if mode not in ["1", "2"]:
            print("无效输入，请输入1、2、3或q。")
            continue

        if mode == "2":
            n = 10
            print("\n自动进入十连抽（10次）。")
        else:
            try:
                n = int(input("输入抽卡总次数（正整数）："))
                if n <= 0:
                    raise ValueError
            except ValueError:
                print("请输入一个正整数。")
                continue

        counts, draw_results = simulate(n)

        print(f"\n本轮抽卡 {n} 次结果：")
        for idx, (star, is_up) in enumerate(draw_results, start=1):
            star_line = format_star_line(star, is_up)
            print(f"{idx:2d}. {star_line}")

        print("\n本次抽卡总结：")
        for star in ["六星", "六星(UP)", "六星(非UP)", "五星", "四星", "三星"]:
            count = counts[star]
            pct = count / n * 100
            print(f"{star}: {count} 次 ({pct:.2f}%)")

        six_total = counts["六星"]
        up_total = counts["六星(UP)"]
        if six_total > 0:
            print(f"六星中当期UP比例：{up_total / six_total * 100:.2f}%")
        else:
            print("未出六星，无法计算UP比例")

        avg = (counts["六星"] * 6 + counts["五星"] * 5 + counts["四星"] * 4 + counts["三星"] * 3) / n
        print(f"平均星级：{avg:.2f}\n")

        # 保存记录
        save_record(mode, n, counts, avg)


if __name__ == "__main__":
    main()

