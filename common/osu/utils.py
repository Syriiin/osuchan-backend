# osu! related utils

from common.osu.enums import Gamemode, Mods


def calculate_pp_total(sorted_pps):
    # sorted_pps should be a sorted generator but can be any iterable of floats
    return sum(pp * (0.95**i) for i, pp in enumerate(sorted_pps))


def get_classic_accuracy(
    statistics: dict[str, int],
    gamemode=Gamemode.STANDARD,
):
    if gamemode == Gamemode.STANDARD:
        great = statistics.get("great", 0)
        ok = statistics.get("ok", 0)
        meh = statistics.get("meh", 0)
        miss = statistics.get("miss", 0)

        max_points = 300 * (great + ok + meh + miss)
        points = (50 * meh) + (100 * ok) + (300 * great)

    elif gamemode == Gamemode.TAIKO:
        great = statistics.get("great", 0)
        ok = statistics.get("ok", 0)
        miss = statistics.get("miss", 0)

        max_points = 300 * (great + ok + miss)
        points = 300 * ((0.5 * ok) + great)

    elif gamemode == Gamemode.CATCH:
        great = statistics.get("great", 0)
        large_tick_hit = statistics.get("large_tick_hit", 0)
        small_tick_hit = statistics.get("small_tick_hit", 0)
        small_tick_miss = statistics.get("small_tick_miss", 0)
        miss = statistics.get("miss", 0)

        max_points = great + large_tick_hit + small_tick_hit + miss + small_tick_miss
        points = great + large_tick_hit + small_tick_hit

    elif gamemode == Gamemode.MANIA:
        perfect = statistics.get("perfect", 0)
        great = statistics.get("great", 0)
        good = statistics.get("good", 0)
        ok = statistics.get("ok", 0)
        meh = statistics.get("meh", 0)
        miss = statistics.get("miss", 0)

        max_points = 300 * (meh + ok + good + great + perfect + miss)
        points = (
            (50 * meh) + (100 * ok) + (200 * good) + (300 * great) + (300 * perfect)
        )
    else:
        raise ValueError(f"{gamemode} is not a valid gamemode")

    try:
        return 100 * (points / max_points)
    except ZeroDivisionError:
        return 0


def get_bpm(bpm, mods):
    bpm = float(bpm)
    mods = int(mods)
    if mods & Mods.DOUBLETIME:
        return bpm * 1.5
    elif mods & Mods.HALFTIME:
        return bpm * (3 / 4)
    else:
        return bpm


def get_length(length, mods):
    length = float(length)
    mods = int(mods)
    if mods & Mods.DOUBLETIME:
        return length / 1.5
    elif mods & Mods.HALFTIME:
        return length / (3 / 4)
    else:
        return length


def get_cs(cs, mods, gamemode):
    cs = float(cs)
    mods = int(mods)

    if gamemode == Gamemode.MANIA:
        if mods & Mods.KEY_MOD:
            if mods & Mods.KEY_1:
                return 1
            if mods & Mods.KEY_2:
                return 2
            if mods & Mods.KEY_3:
                return 3
            if mods & Mods.KEY_4:
                return 4
            if mods & Mods.KEY_5:
                return 5
            if mods & Mods.KEY_6:
                return 6
            if mods & Mods.KEY_7:
                return 7
            if mods & Mods.KEY_8:
                return 8
            if mods & Mods.KEY_9:
                return 9
        return cs

    if mods & Mods.HARDROCK:
        cs *= 1.3
    if mods & Mods.EASY:
        cs *= 0.5

    return cs


def get_ar(ar, mods):
    def ar_to_ms(ar):  # convert ar to ms
        if ar <= 5:
            ms = -120 * ar + 1800
        else:
            ms = -150 * ar + 1950
        return ms

    def ms_to_ar(ms):  # convert ms to ar
        if ms >= 1200:
            ar = (ms - 1800) / -120
        else:
            ar = (ms - 1950) / -150
        return ar

    ar = float(ar)
    mods = int(mods)

    if mods & Mods.HARDROCK:
        ar *= 1.4
    if mods & Mods.EASY:
        ar *= 0.5

    if ar > 10:
        ar = 10

    if mods & Mods.DOUBLETIME:
        ms = ar_to_ms(ar) / 1.5
        ar = ms_to_ar(ms)
    if mods & Mods.HALFTIME:
        ms = ar_to_ms(ar) / (3 / 4)
        ar = ms_to_ar(ms)

    return ar


def get_od(od, mods):
    def od_to_ms(od):  # convert od to ms
        ms = -6 * od + 79.5
        return ms

    def ms_to_od(ms):  # convert ms to od
        od = (ms - 79.5) / -6
        return od

    od = float(od)
    mods = int(mods)

    if mods & Mods.HARDROCK:
        od *= 1.4
    elif mods & Mods.EASY:
        od *= 0.5

    if od > 10:
        od = 10

    if mods & Mods.DOUBLETIME:
        ms = od_to_ms(od) / 1.5
        od = ms_to_od(ms)
    if mods & Mods.HALFTIME:
        ms = od_to_ms(od) / (3 / 4)
        od = ms_to_od(ms)

    return od


def get_gamemode_from_gamemode_string(gamemode_string: str):
    try:
        return Gamemode(int(gamemode_string))
    except ValueError:
        if gamemode_string == "osu":
            return Gamemode.STANDARD
        elif gamemode_string == "taiko":
            return Gamemode.TAIKO
        elif gamemode_string == "catch":
            return Gamemode.CATCH
        elif gamemode_string == "mania":
            return Gamemode.MANIA


def get_gamemode_string_from_gamemode(gamemode: Gamemode):
    if gamemode == Gamemode.STANDARD:
        return "osu"
    elif gamemode == Gamemode.TAIKO:
        return "taiko"
    elif gamemode == Gamemode.CATCH:
        return "catch"
    elif gamemode == Gamemode.MANIA:
        return "mania"
    else:
        raise ValueError(f"{gamemode} is not a valid gamemode")


mod_acronyms = {
    Mods.NONE: "NONE",
    Mods.NOFAIL: "NF",
    Mods.EASY: "EZ",
    Mods.TOUCH_DEVICE: "TD",
    Mods.HIDDEN: "HD",
    Mods.HARDROCK: "HR",
    Mods.SUDDEN_DEATH: "SD",
    Mods.DOUBLETIME: "DT",
    Mods.RELAX: "RX",
    Mods.HALFTIME: "HT",
    Mods.NIGHTCORE: "NC",
    Mods.FLASHLIGHT: "FL",
    Mods.AUTO: "AUTO",
    Mods.SPUN_OUT: "SO",
    Mods.AUTOPILOT: "AP",
    Mods.PERFECT: "PF",
    Mods.KEY_4: "4K",
    Mods.KEY_5: "5K",
    Mods.KEY_6: "6K",
    Mods.KEY_7: "7K",
    Mods.KEY_8: "8K",
    Mods.FADE_IN: "FI",
    Mods.RANDOM: "RN",
    Mods.CINEMA: "CN",
    Mods.TARGET_PRACTICE: "TP",
    Mods.KEY_9: "9K",
    Mods.KEY_COOP: "COOP",
    Mods.KEY_1: "1K",
    Mods.KEY_2: "2K",
    Mods.KEY_3: "3K",
    Mods.SCORE_V2: "V2",
    Mods.MIRROR: "MI",
}


def get_mods_string(mods: int):
    mod_strings = []
    for mod in mod_acronyms:
        if mod & mods:
            mod_strings.append(mod_acronyms[mod])

    if Mods.NIGHTCORE & mods and "DT" in mod_strings:
        mod_strings.remove("DT")
    if Mods.PERFECT & mods and "SD" in mod_strings:
        mod_strings.remove("SD")

    return ",".join(mod_strings)


def get_json_mods(mods: int, add_classic: bool) -> list[dict]:
    json_mods = [
        {"acronym": mod_acronyms[mod]} for mod in mod_acronyms if mod & mods != 0
    ]

    if Mods.NIGHTCORE & mods:
        json_mods = [mod for mod in json_mods if mod["acronym"] != "DT"]
    if Mods.PERFECT & mods:
        json_mods = [mod for mod in json_mods if mod["acronym"] != "SD"]

    if add_classic:
        json_mods.append({"acronym": "CL"})

    return json_mods


def get_bitwise_mods(acronyms: list[str]) -> int:
    bitwise_mods = 0
    for acronym in acronyms:
        for mod, mod_acronym in mod_acronyms.items():
            if acronym == mod_acronym:
                bitwise_mods |= mod
                break

    if bitwise_mods & Mods.NIGHTCORE:
        bitwise_mods |= Mods.DOUBLETIME
    if bitwise_mods & Mods.PERFECT:
        bitwise_mods |= Mods.SUDDEN_DEATH

    return bitwise_mods
