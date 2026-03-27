#!/usr/bin/env python3
"""
Generate the 64 Hexagram Engine State Space Table
Maps the 6 binary DOFs (Ax1-Ax6) to the 64 possible structural configurations.
"""

import os

# Definitive Axis mapping based on the (6, 5, 3) & (4, 1, 2) Trigram Proposal:
# Trigram 1 (Inner/Bottom): Line 1 = Ax6, Line 2 = Ax5, Line 3 = Ax3
# Trigram 2 (Outer/Top): Line 4 = Ax4, Line 5 = Ax1, Line 6 = Ax2
DOFS = [
    {"line": "L1", "axis": "Ax6", "name": "Action Precedence", "yin": "ρA (Receptive)", "yang": "Aρ (Generative)"},
    {"line": "L2", "axis": "Ax5", "name": "Curvature", "yin": "FGA / Flat", "yang": "FSA / Hysteresis"},
    {"line": "L3", "axis": "Ax3", "name": "Chirality", "yin": "Left / -Phase", "yang": "Right / +Phase"},
    {"line": "L4", "axis": "Ax4", "name": "Process Direction", "yin": "CCW (Inductive)", "yang": "CW (Deductive)"},
    {"line": "L5", "axis": "Ax1", "name": "Channel Coupling", "yin": "Closed / Unitary", "yang": "Open / Dissipative"},
    {"line": "L6", "axis": "Ax2", "name": "Boundary / Frame", "yin": "Spread / Eulerian", "yang": "Concentrated / Lagrangian"}
]

# Standard King Wen hexagram names mapped by Shao Yong (Fuxi) binary index
# where Bottom Line = LSB, Top Line = MSB, Yin = 0, Yang = 1.
# This array maps index 0-63 to the standard King Wen number and Name.
# 000000 = 0 -> Hex 2 (Kun)
# 111111 = 63 -> Hex 1 (Qian)
KING_WEN_MAPPING = {
    0: (2, "Kun (Field)"), 1: (24, "Fu (Return)"), 2: (7, "Shi (Army)"), 3: (19, "Lin (Approach)"),
    4: (15, "Qian (Modesty)"), 5: (36, "Ming Yi (Darkening)"), 6: (46, "Sheng (Ascending)"), 7: (11, "Tai (Peace)"),
    8: (16, "Yu (Enthusiasm)"), 9: (51, "Zhen (Shock)"), 10: (40, "Xie (Deliverance)"), 11: (54, "Gui Mei (Maiden)"),
    12: (62, "Xiao Guo (Small Exceeding)"), 13: (55, "Feng (Abundance)"), 14: (32, "Heng (Duration)"), 15: (34, "Da Zhuang (Great Power)"),
    16: (8, "Bi (Holding Together)"), 17: (3, "Zhun (Difficulty)"), 18: (29, "Kan (Abyss)"), 19: (60, "Jie (Limitation)"),
    20: (39, "Jian (Obstruction)"), 21: (63, "Ji Ji (After Completion)"), 22: (48, "Jing (Well)"), 23: (5, "Xu (Waiting)"),
    24: (45, "Cui (Gathering)"), 25: (17, "Sui (Following)"), 26: (47, "Kun (Oppression)"), 27: (58, "Dui (Joy)"),
    28: (31, "Xian (Influence)"), 29: (49, "Ge (Revolution)"), 30: (28, "Da Guo (Great Exceeding)"), 31: (43, "Kuai (Breakthrough)"),
    32: (23, "Bo (Splitting Apart)"), 33: (27, "Yi (Nourishment)"), 34: (4, "Meng (Youthful Folly)"), 35: (41, "Sun (Decrease)"),
    36: (52, "Gen (Keeping Still)"), 37: (22, "Bi (Grace)"), 38: (18, "Gu (Decay)"), 39: (26, "Da Chu (Great Taming)"),
    40: (35, "Jin (Progress)"), 41: (21, "Shi He (Biting Through)"), 42: (64, "Wei Ji (Before Completion)"), 43: (38, "Kui (Opposition)"),
    44: (56, "Lu (Wanderer)"), 45: (30, "Li (Clinging)"), 46: (50, "Ding (Cauldron)"), 47: (14, "Da You (Great Possession)"),
    48: (20, "Guan (Contemplation)"), 49: (42, "Yi (Increase)"), 50: (59, "Huan (Dispersion)"), 51: (61, "Zhong Fu (Inner Truth)"),
    52: (53, "Jian (Gradual Progress)"), 53: (37, "Jia Ren (Family)"), 54: (57, "Xun (Gentle)"), 55: (9, "Xiao Chu (Small Taming)"),
    56: (12, "Pi (Standstill)"), 57: (25, "Wu Wang (Innocence)"), 58: (6, "Song (Conflict)"), 59: (10, "Lu (Treading)"),
    60: (33, "Dun (Retreat)"), 61: (13, "Tong Ren (Fellowship)"), 62: (44, "Gou (Coming to Meet)"), 63: (1, "Qian (Creative)")
}


def build_markdown():
    lines = []
    lines.append("# The 64 Engine State Space (Hexagrams)")
    lines.append("")
    lines.append("This document maps the 6 binary DOFs (Ax1-Ax6) onto the 64 distinct structural configurations of the constraint manifold.")
    lines.append("The engines are generators that traverse this 64-state space along the entropy gradient (Ax0).")
    lines.append("")
    
    lines.append("## Axis Definition (The 6 Lines)")
    lines.append("The mathematically grounded QIT mapping strictly maps the 6 axes into two mutually irreducible Trigrams:")
    lines.append("- **Trigram 1 (Inner/Bottom)**: `(Ax6, Ax5, Ax3)` — The Generative Substrate (SU(2) generators)")
    lines.append("- **Trigram 2 (Outer/Top)**: `(Ax4, Ax1, Ax2)` — The Boundary & Heat (Environmental coupling)")
    lines.append("")
    lines.append("`0` = Yin (broken), `1` = Yang (solid).")
    lines.append("")
    lines.append("| Line | Axis | 0 (Yin) | 1 (Yang) |")
    lines.append("|---|---|---|---|")
    for dof in DOFS:
        lines.append(f"| {dof['line']} | **{dof['axis']}** ({dof['name']}) | {dof['yin']} | {dof['yang']} |")
    lines.append("")
    
    lines.append("## The 64 Configurations")
    lines.append("")
    lines.append("| Hex | Binary | L6 (Ax2) | L5 (Ax1) | L4 (Ax4) | L3 (Ax3) | L2 (Ax5) | L1 (Ax6) | I Ching Hexagram |")
    lines.append("|:---:|:---:|---|---|---|---|---|---|---|")
    
    for i in range(64):
        # padding to 6 bits. 
        # LSB (index 5 of binary string) = Line 1 (Ax6)
        # MSB (index 0 of binary string) = Line 6 (Ax2)
        binary = format(i, '06b')
        l6_ax2, l5_ax1, l4_ax4, l3_ax3, l2_ax5, l1_ax6 = binary[0], binary[1], binary[2], binary[3], binary[4], binary[5]
        
        kw_num, kw_name = KING_WEN_MAPPING[i]
        
        row = f"| {i:02d} | `{binary}` | {l6_ax2} | {l5_ax1} | {l4_ax4} | {l3_ax3} | {l2_ax5} | {l1_ax6} | **{kw_num}**: {kw_name} |"
        lines.append(row)
        
    lines.append("")
    lines.append("---")
    lines.append("*Context: Ax0 is the Drive that pushes the system through these 64 structural states.*")
    return "\n".join(lines)


if __name__ == "__main__":
    md_content = build_markdown()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "64_HEXAGRAM_STATE_SPACE.md")
    with open(out_path, "w") as f:
        f.write(md_content)
    print(f"Generated {out_path}")
