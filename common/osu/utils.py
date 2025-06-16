# osu! related utils

from common.osu.enums import Gamemode, Mods, NewMods


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


def get_lazer_accuracy(
    statistics: dict[str, int], hitobject_counts: dict[str, int], gamemode: Gamemode
):
    if gamemode == Gamemode.STANDARD:
        great = statistics.get("great", 0)
        ok = statistics.get("ok", 0)
        meh = statistics.get("meh", 0)
        miss = statistics.get("miss", 0)
        slider_tails = statistics.get("slider_tail_hit", 0)
        slider_ticks = statistics.get("large_tick_hit", 0)

        max_slider_tails = hitobject_counts.get("sliders", 0)
        max_slider_ticks = hitobject_counts.get("slider_ticks", 0)

        max_points = (
            300 * (great + ok + meh + miss)
            + (max_slider_tails * 150)
            + (max_slider_ticks * 30)
        )
        points = (
            (50 * meh)
            + (100 * ok)
            + (300 * great)
            + (slider_tails * 150)
            + (slider_ticks * 30)
        )
    elif gamemode == Gamemode.TAIKO:
        return get_classic_accuracy(statistics, Gamemode.TAIKO)
    elif gamemode == Gamemode.CATCH:
        return get_classic_accuracy(statistics, Gamemode.CATCH)
    elif gamemode == Gamemode.MANIA:
        return get_classic_accuracy(statistics, Gamemode.MANIA)
    else:
        raise ValueError(f"{gamemode} is not a valid gamemode")

    try:
        return 100 * (points / max_points)
    except ZeroDivisionError:
        return 0


def get_bpm(bpm: float, mods: dict):
    bpm = float(bpm)
    if NewMods.DOUBLETIME in mods or NewMods.NIGHTCORE in mods:
        return bpm * 1.5
    elif NewMods.HALFTIME in mods or NewMods.DAYCORE in mods:
        return bpm * (3 / 4)
    else:
        return bpm


def get_length(length: float, mods: dict):
    length = float(length)
    if NewMods.DOUBLETIME in mods or NewMods.NIGHTCORE in mods:
        return length / 1.5
    elif NewMods.HALFTIME in mods or NewMods.DAYCORE in mods:
        return length / (3 / 4)
    else:
        return length


def get_cs(cs: float, mods: dict, gamemode: Gamemode):
    cs = float(cs)

    if gamemode == Gamemode.MANIA:
        if NewMods.KEY_1 in mods:
            return 1
        if NewMods.KEY_2 in mods:
            return 2
        if NewMods.KEY_3 in mods:
            return 3
        if NewMods.KEY_4 in mods:
            return 4
        if NewMods.KEY_5 in mods:
            return 5
        if NewMods.KEY_6 in mods:
            return 6
        if NewMods.KEY_7 in mods:
            return 7
        if NewMods.KEY_8 in mods:
            return 8
        if NewMods.KEY_9 in mods:
            return 9
        return cs

    if NewMods.HARDROCK in mods:
        cs *= 1.3
    if NewMods.EASY in mods:
        cs *= 0.5

    return cs


def get_ar(ar: float, mods: dict):
    def ar_to_ms(ar: float):  # convert ar to ms
        if ar <= 5:
            ms = -120 * ar + 1800
        else:
            ms = -150 * ar + 1950
        return ms

    def ms_to_ar(ms: float):  # convert ms to ar
        if ms >= 1200:
            ar = (ms - 1800) / -120
        else:
            ar = (ms - 1950) / -150
        return ar

    ar = float(ar)

    if NewMods.HARDROCK in mods:
        ar *= 1.4
    if NewMods.EASY in mods:
        ar *= 0.5

    if ar > 10:
        ar = 10

    if NewMods.DOUBLETIME in mods or NewMods.NIGHTCORE in mods:
        ms = ar_to_ms(ar) / 1.5
        ar = ms_to_ar(ms)
    if NewMods.HALFTIME in mods or NewMods.DAYCORE in mods:
        ms = ar_to_ms(ar) / (3 / 4)
        ar = ms_to_ar(ms)

    return ar


def get_od(od: float, mods: dict):
    def od_to_ms(od: float):  # convert od to ms
        ms = -6 * od + 79.5
        return ms

    def ms_to_od(ms: float):  # convert ms to od
        od = (ms - 79.5) / -6
        return od

    od = float(od)

    if NewMods.HARDROCK in mods:
        od *= 1.4
    elif NewMods.EASY in mods:
        od *= 0.5

    if od > 10:
        od = 10

    if NewMods.DOUBLETIME in mods or NewMods.NIGHTCORE in mods:
        ms = od_to_ms(od) / 1.5
        od = ms_to_od(ms)
    if NewMods.HALFTIME in mods or NewMods.DAYCORE in mods:
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


def get_mods_string_from_json_mods(mods: dict):
    return ",".join(mod for mod in NewMods if mod in mods)


def get_json_mods(mods: int, add_classic: bool) -> dict:
    mods_dict = {mod_acronyms[mod]: {} for mod in mod_acronyms if mod & mods != 0}

    if Mods.NIGHTCORE & mods and "DT" in mods_dict:
        mods_dict.pop("DT")
    if Mods.PERFECT & mods and "SD" in mods_dict:
        mods_dict.pop("SD")

    if add_classic:
        mods_dict["CL"] = {}

    return mods_dict


def get_mod_acronyms(mods: int) -> list[str]:
    json_mods = get_json_mods(mods, add_classic=False)
    return list(json_mods.keys())


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


unranked_mods = [
    NewMods.RELAX,
    NewMods.AUTO,
    NewMods.AUTOPILOT,
    NewMods.KEY_1,
    NewMods.KEY_2,
    NewMods.KEY_3,
    NewMods.KEY_COOP,
    NewMods.RANDOM,
    NewMods.SCORE_V2,
]


def mods_are_ranked(mods: dict, is_stable: bool) -> bool:
    if any(mod in unranked_mods for mod in mods):
        return False
    if any(settings != {} for settings in mods.values()):
        return False
    if not is_stable and NewMods.CLASSIC in mods:
        return False
    return True
