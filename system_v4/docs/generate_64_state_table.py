#!/usr/bin/env python3
"""
Generate the 64 Hexagram Engine State Space Table
Maps the 6 binary DOFs (Ax1-Ax6) to the 64 possible structural configurations.
"""

import os

# Define the 6 DOFs and their binary representations (0 = Yin, 1 = Yang)
# These are candidate labels based on the corrected geometry ratchet ontology.
DOFS = [
    {"axis": "Ax1", "name": "Channel", "yin": "Closed (Unitary)", "yang": "Open (Dissipative)"},
    {"axis": "Ax2", "name": "Boundary", "yin": "Spread (Wave/Field)", "yang": "Concentrated (Particle/Dots)"},
    {"axis": "Ax3", "name": "Chirality", "yin": "Left (Negative Phase)", "yang": "Right (Positive Phase)"},
    {"axis": "Ax4", "name": "Traversal", "yin": "CCW (Inductive)", "yang": "CW (Deductive)"},
    {"axis": "Ax5", "name": "Curvature", "yin": "Flat (FGA / Straight)", "yang": "Curved (FSA / Hysteresis)"},
    {"axis": "Ax6", "name": "Precedence", "yin": "Receptive (ρA / Object-first)", "yang": "Generative (Aρ / Action-first)"}
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
    lines.append("We map Ax1 to the bottom line (Line 1, LSB) and Ax6 to the top line (Line 6, MSB). `0` = Yin (broken), `1` = Yang (solid).")
    lines.append("")
    lines.append("| Line | Axis | 0 (Yin) | 1 (Yang) |")
    lines.append("|---|---|---|---|")
    for i, dof in enumerate(DOFS):
        lines.append(f"| L{i+1} | **{dof['axis']}** ({dof['name']}) | {dof['yin']} | {dof['yang']} |")
    lines.append("")
    
    lines.append("## The 64 Configurations")
    lines.append("")
    lines.append("| Hex | Binary | Ax6 | Ax5 | Ax4 | Ax3 | Ax2 | Ax1 | I Ching Hexagram |")
    lines.append("|:---:|:---:|---|---|---|---|---|---|---|")
    
    for i in range(64):
        # binary string, padded to 6 bits, reversed so LSB is at the end? 
        # Standard notation: MSB on left. So: Ax6 Ax5 Ax4 Ax3 Ax2 Ax1
        binary = format(i, '06b')
        # Here binary[0] is MSB (Ax6), binary[5] is LSB (Ax1)
        ax6, ax5, ax4, ax3, ax2, ax1 = binary[0], binary[1], binary[2], binary[3], binary[4], binary[5]
        
        kw_num, kw_name = KING_WEN_MAPPING[i]
        
        row = f"| {i:02d} | `{binary}` | {ax6} | {ax5} | {ax4} | {ax3} | {ax2} | {ax1} | **{kw_num}**: {kw_name} |"
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
