# osu! related utils

from common.osu.enums import BitMods, Gamemode, Mods


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
    if Mods.DOUBLETIME in mods or Mods.NIGHTCORE in mods:
        return bpm * 1.5
    elif Mods.HALFTIME in mods or Mods.DAYCORE in mods:
        return bpm * (3 / 4)
    else:
        return bpm


def get_length(length: float, mods: dict):
    length = float(length)
    if Mods.DOUBLETIME in mods or Mods.NIGHTCORE in mods:
        return length / 1.5
    elif Mods.HALFTIME in mods or Mods.DAYCORE in mods:
        return length / (3 / 4)
    else:
        return length


def get_cs(cs: float, mods: dict, gamemode: Gamemode):
    cs = float(cs)

    if gamemode == Gamemode.MANIA:
        if Mods.KEY_1 in mods:
            return 1
        if Mods.KEY_2 in mods:
            return 2
        if Mods.KEY_3 in mods:
            return 3
        if Mods.KEY_4 in mods:
            return 4
        if Mods.KEY_5 in mods:
            return 5
        if Mods.KEY_6 in mods:
            return 6
        if Mods.KEY_7 in mods:
            return 7
        if Mods.KEY_8 in mods:
            return 8
        if Mods.KEY_9 in mods:
            return 9
        return cs

    if Mods.HARDROCK in mods:
        cs *= 1.3
    if Mods.EASY in mods:
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

    if Mods.HARDROCK in mods:
        ar *= 1.4
    if Mods.EASY in mods:
        ar *= 0.5

    if ar > 10:
        ar = 10

    if Mods.DOUBLETIME in mods or Mods.NIGHTCORE in mods:
        ms = ar_to_ms(ar) / 1.5
        ar = ms_to_ar(ms)
    if Mods.HALFTIME in mods or Mods.DAYCORE in mods:
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

    if Mods.HARDROCK in mods:
        od *= 1.4
    elif Mods.EASY in mods:
        od *= 0.5

    if od > 10:
        od = 10

    if Mods.DOUBLETIME in mods or Mods.NIGHTCORE in mods:
        ms = od_to_ms(od) / 1.5
        od = ms_to_od(ms)
    if Mods.HALFTIME in mods or Mods.DAYCORE in mods:
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
    BitMods.NONE: "NONE",
    BitMods.NOFAIL: "NF",
    BitMods.EASY: "EZ",
    BitMods.TOUCH_DEVICE: "TD",
    BitMods.HIDDEN: "HD",
    BitMods.HARDROCK: "HR",
    BitMods.SUDDEN_DEATH: "SD",
    BitMods.DOUBLETIME: "DT",
    BitMods.RELAX: "RX",
    BitMods.HALFTIME: "HT",
    BitMods.NIGHTCORE: "NC",
    BitMods.FLASHLIGHT: "FL",
    BitMods.AUTO: "AUTO",
    BitMods.SPUN_OUT: "SO",
    BitMods.AUTOPILOT: "AP",
    BitMods.PERFECT: "PF",
    BitMods.KEY_4: "4K",
    BitMods.KEY_5: "5K",
    BitMods.KEY_6: "6K",
    BitMods.KEY_7: "7K",
    BitMods.KEY_8: "8K",
    BitMods.FADE_IN: "FI",
    BitMods.RANDOM: "RN",
    BitMods.CINEMA: "CN",
    BitMods.TARGET_PRACTICE: "TP",
    BitMods.KEY_9: "9K",
    BitMods.KEY_COOP: "COOP",
    BitMods.KEY_1: "1K",
    BitMods.KEY_2: "2K",
    BitMods.KEY_3: "3K",
    BitMods.SCORE_V2: "V2",
    BitMods.MIRROR: "MI",
}


def get_mods_string(mods: int):
    mod_strings = []
    for mod in mod_acronyms:
        if mod & mods:
            mod_strings.append(mod_acronyms[mod])

    if BitMods.NIGHTCORE & mods and "DT" in mod_strings:
        mod_strings.remove("DT")
    if BitMods.PERFECT & mods and "SD" in mod_strings:
        mod_strings.remove("SD")

    return ",".join(mod_strings)


def get_mods_string_from_json_mods(mods: dict):
    return ",".join(mod for mod in Mods if mod in mods)


def get_json_mods(mods: int, add_classic: bool) -> dict:
    mods_dict = {mod_acronyms[mod]: {} for mod in mod_acronyms if mod & mods != 0}

    if BitMods.NIGHTCORE & mods and "DT" in mods_dict:
        mods_dict.pop("DT")
    if BitMods.PERFECT & mods and "SD" in mods_dict:
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

    if bitwise_mods & BitMods.NIGHTCORE:
        bitwise_mods |= BitMods.DOUBLETIME
    if bitwise_mods & BitMods.PERFECT:
        bitwise_mods |= BitMods.SUDDEN_DEATH

    # HACK: daycore is the only diff reduction mod in the new lazer set so i want to handle it manually even if we cant do the others the same way
    #   better to be missing pp than gain pp from missing handling
    if Mods.DAYCORE in acronyms:
        bitwise_mods |= BitMods.HALFTIME

    return bitwise_mods


unranked_mods = [
    Mods.RELAX,
    Mods.AUTO,
    Mods.AUTOPILOT,
    Mods.KEY_1,
    Mods.KEY_2,
    Mods.KEY_3,
    Mods.KEY_COOP,
    Mods.RANDOM,
    Mods.SCORE_V2,
]


def mods_are_ranked(mods: dict, is_stable: bool) -> bool:
    if any(mod in unranked_mods for mod in mods):
        return False
    if any(settings != {} for settings in mods.values()):
        return False
    if not is_stable and Mods.CLASSIC in mods:
        return False
    return True
